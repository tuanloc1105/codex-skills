import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { AgentDbError, invariant } from '../core/errors.js';
import { atomicWriteJson } from '../core/fs.js';
import { projectPaths } from './paths.js';

const MAX_CACHE_AGE_MS = 24 * 60 * 60 * 1000;

function scope(project, target) {
  return {
    kind: 'schema-cache',
    projectId: project.id,
    projectBindingRevision: project.bindingRevision,
    targetId: target.id,
    targetFingerprint: target.targetFingerprint,
    credentialId: target.credentials.read,
  };
}

function cachePath(paths, project, target) {
  return path.join(projectPaths(paths, project.id).schema, `${target.id}.json.enc`);
}

export async function saveSchemaCache(paths, vault, project, target, data) {
  const binding = scope(project, target);
  const payload = {
    formatVersion: 1,
    ...binding,
    capturedAt: new Date().toISOString(),
    identity: data.identity,
    schema: data.schema,
    schemaTruncated: Boolean(data.schemaTruncated || data.schema?.truncated),
  };
  await atomicWriteJson(cachePath(paths, project, target), {
    formatVersion: 1,
    ...binding,
    envelope: await vault.encryptObject(payload, binding),
  });
  return payload;
}

export async function loadSchemaCache(paths, vault, project, target, { now = Date.now() } = {}) {
  let record;
  try {
    record = JSON.parse(await readFile(cachePath(paths, project, target), 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT') throw new AgentDbError('SCHEMA_CACHE_MISSING', `No schema cache exists for target ${target.id}`);
    throw error;
  }
  const binding = scope(project, target);
  for (const [key, value] of Object.entries(binding)) {
    invariant(record[key] === value, 'SCHEMA_CACHE_MISMATCH', `Schema cache ${key} does not match the current target`);
  }
  const payload = await vault.decryptObject(record.envelope, binding);
  invariant(Date.parse(payload.capturedAt) + MAX_CACHE_AGE_MS > now, 'SCHEMA_CACHE_EXPIRED', 'Schema cache is older than 24 hours; refresh it before use');
  return payload;
}
