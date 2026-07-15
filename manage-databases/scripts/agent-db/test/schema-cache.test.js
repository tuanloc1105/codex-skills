import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { runtimePaths } from '../src/config/paths.js';
import { loadSchemaCache, saveSchemaCache } from '../src/config/schema-cache.js';
import { Vault } from '../src/security/vault.js';

function memoryKeyring() {
  const values = new Map();
  return {
    name: 'memory-test-keyring',
    async get(account) { return values.get(account) || null; },
    async set(account, value) { values.set(account, value); },
  };
}

test('schema cache is encrypted, credential-bound, and expires after 24 hours', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-schema-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const paths = runtimePaths({ AGENT_DB_HOME: root });
  const vault = new Vault(paths, { keyring: memoryKeyring() });
  const project = { id: 'c3a7ba02-dd0e-4f32-89af-2479c6e36441' };
  const target = {
    id: 'primary', targetFingerprint: 'fingerprint-1', credentials: { read: 'credential-1' },
  };
  const saved = await saveSchemaCache(paths, vault, project, target, {
    identity: { database: 'payments', principal: 'reader', serverIdentity: 'db-01', version: '16' },
    schema: [{ table: 'invoices' }],
  });
  const capturedAt = Date.parse(saved.capturedAt);
  assert.deepEqual((await loadSchemaCache(paths, vault, project, target, { now: capturedAt })).schema, [{ table: 'invoices' }]);
  await assert.rejects(
    loadSchemaCache(paths, vault, project, { ...target, credentials: { read: 'credential-2' } }, { now: capturedAt }),
    { code: 'SCHEMA_CACHE_MISMATCH' },
  );
  await assert.rejects(
    loadSchemaCache(paths, vault, project, target, { now: capturedAt + 24 * 60 * 60 * 1000 + 1 }),
    { code: 'SCHEMA_CACHE_EXPIRED' },
  );
});
