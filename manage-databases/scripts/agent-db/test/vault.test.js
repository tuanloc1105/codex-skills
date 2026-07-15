import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { runtimePaths } from '../src/config/paths.js';
import { Vault } from '../src/security/vault.js';

function memoryKeyring() {
  const values = new Map();
  return {
    name: 'memory-test-keyring',
    async get(account) { return values.get(account) || null; },
    async set(account, value) { values.set(account, value); },
  };
}

async function fixture(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-vault-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  return { paths: runtimePaths({ AGENT_DB_HOME: root }), keyring: memoryKeyring() };
}

test('vault encrypts and scope-binds credentials', async (t) => {
  const { paths, keyring } = await fixture(t);
  const vault = new Vault(paths, { keyring });
  const stored = await vault.storeCredential({
    projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
    username: 'reader', secret: 'not-in-plaintext',
  });
  const ciphertext = await readFile(path.join(paths.vault, `${stored.credentialId}.json.enc`), 'utf8');
  assert.doesNotMatch(ciphertext, /not-in-plaintext/);
  assert.doesNotMatch(ciphertext, /reader/);

  const loaded = await vault.credential(stored.credentialId, {
    projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
  });
  assert.equal(loaded.username, 'reader');
  assert.equal(loaded.secret, 'not-in-plaintext');
  await assert.rejects(
    vault.credential(stored.credentialId, {
      projectId: 'project-2', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
    }),
    { code: 'CREDENTIAL_SCOPE_MISMATCH' },
  );
  await assert.rejects(
    vault.credential(stored.credentialId, {
      projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-2', engine: 'postgresql', mode: 'read',
    }),
    { code: 'CREDENTIAL_SCOPE_MISMATCH' },
  );
});

test('vault rejects ciphertext tampering', async (t) => {
  const { paths, keyring } = await fixture(t);
  const vault = new Vault(paths, { keyring });
  const stored = await vault.storeCredential({
    projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'mongodb', mode: 'read',
    username: 'reader', secret: 'secret-value',
  });
  const file = path.join(paths.vault, `${stored.credentialId}.json.enc`);
  const record = JSON.parse(await readFile(file, 'utf8'));
  record.envelope.ciphertext = `${record.envelope.ciphertext.slice(0, -2)}AA`;
  await writeFile(file, JSON.stringify(record));
  await assert.rejects(
    vault.credential(stored.credentialId, {
      projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'mongodb', mode: 'read',
    }),
    { code: 'VAULT_INTEGRITY_ERROR' },
  );
});

test('passphrase fallback can reopen the same vault without a keyring', async (t) => {
  const { paths } = await fixture(t);
  const provider = async () => 'a sufficiently long test passphrase';
  const first = new Vault(paths, { keyring: null, passphraseProvider: provider });
  const stored = await first.storeCredential({
    projectId: 'project-1', targetId: 'oracle', targetFingerprint: 'fingerprint-1', engine: 'oracle', mode: 'mutation',
    username: 'dba', secret: 'secret-value',
  });
  const reopened = new Vault(paths, { keyring: null, passphraseProvider: provider });
  const credential = await reopened.credential(stored.credentialId, {
    projectId: 'project-1', targetId: 'oracle', targetFingerprint: 'fingerprint-1', engine: 'oracle', mode: 'mutation',
  });
  assert.equal(credential.secret, 'secret-value');
});

test('credential ids cannot traverse outside the vault directory', async (t) => {
  const { paths, keyring } = await fixture(t);
  const vault = new Vault(paths, { keyring });
  await assert.rejects(vault.deleteCredential('../victim'), { code: 'INVALID_ARGUMENT' });
  await assert.rejects(
    vault.credential('../victim', {
      projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
    }),
    { code: 'INVALID_ARGUMENT' },
  );
});

test('concurrent first use converges on one vault key', async (t) => {
  const { paths, keyring } = await fixture(t);
  const first = new Vault(paths, { keyring });
  const second = new Vault(paths, { keyring });
  const [left, right] = await Promise.all([
    first.storeCredential({
      projectId: 'project-1', targetId: 'left', targetFingerprint: 'fingerprint-left', engine: 'postgresql', mode: 'read',
      username: 'left-user', secret: 'left-secret',
    }),
    second.storeCredential({
      projectId: 'project-1', targetId: 'right', targetFingerprint: 'fingerprint-right', engine: 'postgresql', mode: 'read',
      username: 'right-user', secret: 'right-secret',
    }),
  ]);

  const reopened = new Vault(paths, { keyring });
  const leftCredential = await reopened.credential(left.credentialId, {
    projectId: 'project-1', targetId: 'left', targetFingerprint: 'fingerprint-left', engine: 'postgresql', mode: 'read',
  });
  const rightCredential = await reopened.credential(right.credentialId, {
    projectId: 'project-1', targetId: 'right', targetFingerprint: 'fingerprint-right', engine: 'postgresql', mode: 'read',
  });
  assert.equal(leftCredential.secret, 'left-secret');
  assert.equal(rightCredential.secret, 'right-secret');
});

test('vault rejects modified KDF parameters before deriving a key', async (t) => {
  const { paths } = await fixture(t);
  const provider = async () => 'a sufficiently long test passphrase';
  const first = new Vault(paths, { keyring: null, passphraseProvider: provider });
  const stored = await first.storeCredential({
    projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
    username: 'reader', secret: 'secret-value',
  });
  const format = JSON.parse(await readFile(paths.vaultFormat, 'utf8'));
  format.protector.parameters.N = 2 ** 30;
  await writeFile(paths.vaultFormat, JSON.stringify(format));
  const reopened = new Vault(paths, { keyring: null, passphraseProvider: provider });
  await assert.rejects(
    reopened.credential(stored.credentialId, {
      projectId: 'project-1', targetId: 'primary', targetFingerprint: 'fingerprint-1', engine: 'postgresql', mode: 'read',
    }),
    { code: 'VAULT_FORMAT_UNSUPPORTED' },
  );
});

test('all passphrase sources enforce the minimum length', async (t) => {
  const { paths } = await fixture(t);
  const fromEnvironment = new Vault(paths, {
    keyring: null,
    env: { AGENT_DB_VAULT_PASSPHRASE: 'short' },
  });
  await assert.rejects(fromEnvironment.key(), { code: 'VAULT_PASSPHRASE_WEAK' });

  const fromProvider = new Vault(runtimePaths({ AGENT_DB_HOME: `${paths.root}-provider` }), {
    keyring: null,
    passphraseProvider: async () => 'short',
  });
  t.after(() => rm(`${paths.root}-provider`, { recursive: true, force: true }));
  await assert.rejects(fromProvider.key(), { code: 'VAULT_PASSPHRASE_WEAK' });
});
