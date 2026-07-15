import { safeError } from './errors.js';
import { MAX_OUTPUT_BYTES, normalizeValue } from './values.js';

export function success(command, data, context = undefined, warnings = []) {
  return {
    ok: true,
    command,
    ...(context ? { context } : {}),
    data: normalizeValue(data),
    warnings,
  };
}

export function failure(command, error, context = undefined) {
  return {
    ok: false,
    command,
    ...(context ? { context } : {}),
    error: safeError(error),
  };
}

export function emitJson(payload, stream = process.stdout) {
  const terminalUnsafe = /[\u007f-\u009f\u061c\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]/gu;
  const encode = (value) => JSON.stringify(value).replace(
    terminalUnsafe,
    (character) => `\\u${character.codePointAt(0).toString(16).padStart(4, '0')}`,
  );
  let serialized = encode(payload);
  if (Buffer.byteLength(serialized, 'utf8') + 1 > MAX_OUTPUT_BYTES) {
    serialized = encode({
      ok: false,
      command: payload?.command || 'unknown',
      error: {
        code: 'OUTPUT_TOO_LARGE',
        message: `Serialized CLI output exceeds the hard ${MAX_OUTPUT_BYTES}-byte limit`,
      },
    });
  }
  stream.write(`${serialized}\n`);
}

export function publicTarget(target) {
  return {
    id: target.id,
    engine: target.engine,
    environment: target.environment,
    host: target.connection.host,
    port: target.connection.port,
    database: target.connection.database,
    ...(target.connection.service ? { service: target.connection.service } : {}),
    tls: Boolean(target.connection.tls),
    ...(target.connection.encrypt === undefined ? {} : { encrypt: Boolean(target.connection.encrypt) }),
    trustServerCertificate: Boolean(target.connection.trustServerCertificate),
    ...(target.connection.authSource ? { authSource: target.connection.authSource } : {}),
    expectedServerIdentity: target.expectedServerIdentity,
    targetFingerprint: target.targetFingerprint,
  };
}

export function commandContext(project, target = undefined) {
  return {
    project: { id: project.id, name: project.name, root: project.root, bindingRevision: project.bindingRevision },
    ...(target ? { target: publicTarget(target) } : {}),
  };
}
