import { createCipheriv, createDecipheriv, randomBytes, randomUUID, scrypt as scryptCallback } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { AgentDbError, invariant } from '../core/errors.js';
import { atomicWriteJson, readJson, removeIfExists, validateUuid, withFileLock } from '../core/fs.js';
import { readHidden } from './secret-input.js';

const scrypt = promisify(scryptCallback);
const KEYRING_SERVICE = 'codex-agent-db';
const CIPHER = 'aes-256-gcm';
const IV_BYTES = 12;
const TAG_BYTES = 16;
const SCRYPT_OPTIONS = { N: 32768, r: 8, p: 3, maxmem: 64 * 1024 * 1024 };

function encode(value) {
  return Buffer.from(value).toString('base64');
}

function decode(value) {
  return Buffer.from(value, 'base64');
}

function canonicalAad(scope) {
  const ordered = {};
  for (const key of Object.keys(scope).sort()) ordered[key] = scope[key];
  return Buffer.from(JSON.stringify(ordered));
}

function validateFormat(format) {
  invariant(format?.formatVersion === 1, 'VAULT_FORMAT_UNSUPPORTED', 'Unsupported vault format version');
  validateUuid(format.vaultId, 'vault id');
  invariant(
    format.cipher?.name === CIPHER
      && format.cipher.keyBytes === 32
      && format.cipher.ivBytes === IV_BYTES
      && format.cipher.tagBytes === TAG_BYTES,
    'VAULT_FORMAT_UNSUPPORTED',
    'Vault cipher parameters are not supported',
  );
  if (format.protector?.type === 'os-keyring') {
    invariant(format.protector.service === KEYRING_SERVICE, 'VAULT_FORMAT_UNSUPPORTED', 'Vault keyring service is invalid');
    invariant(format.protector.account === `vault:${format.vaultId}`, 'VAULT_FORMAT_UNSUPPORTED', 'Vault keyring account is invalid');
    return format;
  }
  if (format.protector?.type === 'passphrase-scrypt') {
    const parameters = format.protector.parameters;
    invariant(
      parameters?.N === SCRYPT_OPTIONS.N
        && parameters.r === SCRYPT_OPTIONS.r
        && parameters.p === SCRYPT_OPTIONS.p
        && parameters.maxmem === SCRYPT_OPTIONS.maxmem
        && decode(format.protector.salt).length === 16,
      'VAULT_FORMAT_UNSUPPORTED',
      'Vault scrypt parameters are not supported',
    );
    return format;
  }
  throw new AgentDbError('VAULT_FORMAT_UNSUPPORTED', `Unknown vault protector: ${format.protector?.type}`);
}

function encrypt(key, value, scope) {
  const iv = randomBytes(IV_BYTES);
  const cipher = createCipheriv(CIPHER, key, iv, { authTagLength: TAG_BYTES });
  cipher.setAAD(canonicalAad(scope));
  const ciphertext = Buffer.concat([cipher.update(Buffer.from(JSON.stringify(value))), cipher.final()]);
  return { iv: encode(iv), tag: encode(cipher.getAuthTag()), ciphertext: encode(ciphertext) };
}

function decrypt(key, envelope, scope) {
  try {
    const decipher = createDecipheriv(CIPHER, key, decode(envelope.iv), { authTagLength: TAG_BYTES });
    decipher.setAAD(canonicalAad(scope));
    decipher.setAuthTag(decode(envelope.tag));
    const plaintext = Buffer.concat([decipher.update(decode(envelope.ciphertext)), decipher.final()]);
    return JSON.parse(plaintext.toString('utf8'));
  } catch {
    throw new AgentDbError('VAULT_INTEGRITY_ERROR', 'Vault data could not be authenticated or decrypted');
  }
}

async function nativeKeyring(env) {
  if (env.AGENT_DB_DISABLE_KEYRING === '1') return null;
  try {
    const { Entry } = await import('@napi-rs/keyring');
    return {
      async get(account) {
        try {
          return new Entry(KEYRING_SERVICE, account).getPassword();
        } catch {
          return null;
        }
      },
      async set(account, value) {
        new Entry(KEYRING_SERVICE, account).setPassword(value);
      },
      async delete(account) {
        try {
          new Entry(KEYRING_SERVICE, account).deletePassword();
        } catch {
          // Best-effort cleanup for an initialization that did not commit.
        }
      },
      name: 'napi-os-keyring',
    };
  } catch {
    return null;
  }
}

async function getPassphrase(env, creating) {
  if (env.AGENT_DB_VAULT_PASSPHRASE) {
    invariant(env.AGENT_DB_VAULT_PASSPHRASE.length >= 12, 'VAULT_PASSPHRASE_WEAK', 'Vault passphrase must contain at least 12 characters');
    return env.AGENT_DB_VAULT_PASSPHRASE;
  }
  const first = await readHidden(creating ? 'Create vault master passphrase: ' : 'Vault master passphrase: ');
  invariant(first.length >= 12, 'VAULT_PASSPHRASE_WEAK', 'Vault passphrase must contain at least 12 characters');
  if (!creating) return first;
  const second = await readHidden('Repeat vault master passphrase: ');
  invariant(first === second, 'VAULT_PASSPHRASE_MISMATCH', 'Vault passphrases did not match');
  return first;
}

export class Vault {
  constructor(paths, { env = process.env, keyring = undefined, passphraseProvider = undefined } = {}) {
    this.paths = paths;
    this.env = env;
    this.injectedKeyring = keyring;
    this.passphraseProvider = passphraseProvider;
    this.cachedKey = null;
  }

  async passphrase(creating) {
    const value = this.passphraseProvider
      ? await this.passphraseProvider(creating)
      : await getPassphrase(this.env, creating);
    invariant(typeof value === 'string' && value.length >= 12, 'VAULT_PASSPHRASE_WEAK', 'Vault passphrase must contain at least 12 characters');
    return value;
  }

  async keyring() {
    return this.injectedKeyring === undefined ? nativeKeyring(this.env) : this.injectedKeyring;
  }

  async initialize() {
    const existing = await readJson(this.paths.vaultFormat, null);
    if (existing) return existing;
    return withFileLock(`${this.paths.vaultFormat}.lock`, async () => {
      const winner = await readJson(this.paths.vaultFormat, null);
      if (winner) return winner;

      const vaultId = randomUUID();
      const key = randomBytes(32);
      const keyring = await this.keyring();
      let protector;
      let keyringAccount;

      if (keyring) {
        try {
          keyringAccount = `vault:${vaultId}`;
          await keyring.set(keyringAccount, encode(key));
          protector = { type: 'os-keyring', backend: keyring.name || 'injected', service: KEYRING_SERVICE, account: keyringAccount };
        } catch {
          protector = null;
          keyringAccount = undefined;
        }
      }

      if (!protector) {
        const passphrase = await this.passphrase(true);
        const salt = randomBytes(16);
        const wrappingKey = await scrypt(passphrase, salt, 32, SCRYPT_OPTIONS);
        protector = {
          type: 'passphrase-scrypt',
          salt: encode(salt),
          parameters: { N: SCRYPT_OPTIONS.N, r: SCRYPT_OPTIONS.r, p: SCRYPT_OPTIONS.p, maxmem: SCRYPT_OPTIONS.maxmem },
          wrappedKey: encrypt(wrappingKey, { key: encode(key) }, { formatVersion: 1, vaultId, purpose: 'vault-key' }),
        };
      }

      const format = {
        formatVersion: 1,
        vaultId,
        cipher: { name: CIPHER, keyBytes: 32, ivBytes: IV_BYTES, tagBytes: TAG_BYTES },
        protector,
        recoveryCommand: 'agent-db credential reveal --target <target> --mode <read|mutation>',
      };
      try {
        await atomicWriteJson(this.paths.vaultFormat, format);
      } catch (error) {
        if (keyringAccount && keyring?.delete) await keyring.delete(keyringAccount);
        throw error;
      }
      this.cachedKey = key;
      return format;
    });
  }

  async key() {
    if (this.cachedKey) return this.cachedKey;
    const format = validateFormat(await this.initialize());

    if (format.protector.type === 'os-keyring') {
      const keyring = await this.keyring();
      invariant(keyring, 'VAULT_LOCKED', 'The configured OS keyring backend is unavailable');
      const encodedKey = await keyring.get(format.protector.account);
      invariant(encodedKey, 'VAULT_LOCKED', 'The vault key is missing from the OS keyring');
      this.cachedKey = decode(encodedKey);
    } else if (format.protector.type === 'passphrase-scrypt') {
      const passphrase = await this.passphrase(false);
      const parameters = format.protector.parameters;
      const wrappingKey = await scrypt(passphrase, decode(format.protector.salt), 32, parameters);
      const unwrapped = decrypt(wrappingKey, format.protector.wrappedKey, {
        formatVersion: 1,
        vaultId: format.vaultId,
        purpose: 'vault-key',
      });
      this.cachedKey = decode(unwrapped.key);
    }

    invariant(this.cachedKey.length === 32, 'VAULT_INTEGRITY_ERROR', 'Vault key length is invalid');
    return this.cachedKey;
  }

  async encryptObject(value, scope) {
    return encrypt(await this.key(), value, { formatVersion: 1, ...scope });
  }

  async decryptObject(envelope, scope) {
    return decrypt(await this.key(), envelope, { formatVersion: 1, ...scope });
  }

  async storeCredential({ projectId, targetId, targetFingerprint, engine, mode, username, secret }) {
    invariant(typeof username === 'string' && username && Buffer.byteLength(username, 'utf8') <= 4096, 'INVALID_ARGUMENT', 'Username is required and must not exceed 4096 bytes');
    invariant(typeof secret === 'string' && secret && Buffer.byteLength(secret, 'utf8') <= 65536, 'INVALID_ARGUMENT', 'Secret is required and must not exceed 65536 bytes');
    invariant(typeof targetFingerprint === 'string' && targetFingerprint, 'INVALID_ARGUMENT', 'Target fingerprint is required');
    const credentialId = randomUUID();
    const scope = { credentialId, projectId, targetId, targetFingerprint, engine, mode, kind: 'credential' };
    const payload = {
      formatVersion: 1,
      ...scope,
      username,
      secret,
      createdAt: new Date().toISOString(),
      rotatedAt: null,
    };
    const record = { formatVersion: 1, ...scope, envelope: await this.encryptObject(payload, scope) };
    await atomicWriteJson(path.join(this.paths.vault, `${credentialId}.json.enc`), record);
    return { credentialId, username, mode };
  }

  async credential(credentialId, expected) {
    invariant(credentialId, 'CREDENTIAL_REQUIRED', `Missing ${expected.mode} credential for target ${expected.targetId}`);
    validateUuid(credentialId, 'credential id');
    const filePath = path.join(this.paths.vault, `${credentialId}.json.enc`);
    let record;
    try {
      record = JSON.parse(await readFile(filePath, 'utf8'));
    } catch (error) {
      if (error?.code === 'ENOENT') throw new AgentDbError('CREDENTIAL_REQUIRED', `Credential record not found for target ${expected.targetId}`);
      throw error;
    }
    const scope = {
      credentialId,
      projectId: expected.projectId,
      targetId: expected.targetId,
      targetFingerprint: expected.targetFingerprint,
      engine: expected.engine,
      mode: expected.mode,
      kind: 'credential',
    };
    for (const [key, value] of Object.entries(scope)) {
      invariant(record[key] === value, 'CREDENTIAL_SCOPE_MISMATCH', `Credential ${key} does not match the requested target`);
    }
    return this.decryptObject(record.envelope, scope);
  }

  async deleteCredential(credentialId) {
    if (credentialId) {
      validateUuid(credentialId, 'credential id');
      await removeIfExists(path.join(this.paths.vault, `${credentialId}.json.enc`));
    }
  }
}
