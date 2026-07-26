import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { createAdapter } from '../src/adapters/index.js';
import { requireMongoMutation, requireRedisMutation, requireSqlMutation } from '../src/security/safety.js';

const smokeId = `smoke_${randomUUID().replaceAll('-', '')}`;
const smokeValue = `value_${randomUUID().replaceAll('-', '')}`;
const redisSmokeKey = `ci:${smokeId}`;

const specs = {
  mongodb: {
    target: {
      connection: { authSource: 'admin', tls: false },
      allowedNamespaces: ['ci_smoke'],
    },
    read: { operation: 'estimatedDocumentCount', collection: 'ci_smoke' },
    mutation: {
      operation: 'insertOne',
      collection: 'ci_smoke',
      document: { _id: smokeId, smoke_value: smokeValue },
    },
    verification: {
      operation: 'findOne',
      collection: 'ci_smoke',
      filter: { _id: smokeId },
      projection: { _id: 0, smoke_value: 1 },
    },
    cleanup: {
      operation: 'deleteOne',
      collection: 'ci_smoke',
      filter: { _id: smokeId },
    },
    assertVerification(result) {
      assert.deepEqual(result.documents, [{ smoke_value: smokeValue }]);
    },
  },
  oracle: {
    target: {
      connection: { service: 'FREEPDB1', tls: false, trustServerCertificate: false },
    },
    read: 'SELECT 1 AS smoke_test FROM DUAL',
    mutation: `INSERT INTO DATA_DEBUG_SMOKE (SMOKE_ID, SMOKE_VALUE) VALUES ('${smokeId}', '${smokeValue}')`,
    verification: `SELECT SMOKE_VALUE FROM DATA_DEBUG_SMOKE WHERE SMOKE_ID = '${smokeId}'`,
    cleanup: `DELETE FROM DATA_DEBUG_SMOKE WHERE SMOKE_ID = '${smokeId}'`,
    assertVerification(result) {
      assert.deepEqual(result.rows, [[smokeValue]]);
    },
  },
  postgresql: {
    target: { connection: { tls: false } },
    read: 'SELECT 1 AS smoke_test',
    mutation: `INSERT INTO public.data_debug_smoke (smoke_id, smoke_value) VALUES ('${smokeId}', '${smokeValue}')`,
    verification: `SELECT smoke_value FROM public.data_debug_smoke WHERE smoke_id = '${smokeId}'`,
    cleanup: `DELETE FROM public.data_debug_smoke WHERE smoke_id = '${smokeId}'`,
    assertVerification(result) {
      assert.deepEqual(result.rows, [[smokeValue]]);
    },
  },
  redis: {
    target: {
      connection: { tls: false },
      keyPrefix: 'ci:',
    },
    read: {
      operation: 'command',
      command: 'SCAN',
      arguments: { cursor: '0', matchSuffix: '*', count: 10 },
    },
    mutation: {
      operation: 'command',
      command: 'SET',
      arguments: { key: redisSmokeKey, value: smokeValue },
    },
    verification: {
      operation: 'command',
      command: 'GET',
      arguments: { key: redisSmokeKey },
    },
    cleanup: {
      operation: 'command',
      command: 'DEL',
      arguments: { keys: [redisSmokeKey] },
    },
    assertVerification(result) {
      assert.equal(result.value, smokeValue);
    },
  },
  sqlserver: {
    target: { connection: { encrypt: false, tls: false, trustServerCertificate: false } },
    read: 'SELECT 1 AS smoke_test',
    mutation: `INSERT INTO dbo.data_debug_smoke (smoke_id, smoke_value) VALUES ('${smokeId}', '${smokeValue}')`,
    verification: `SELECT smoke_value FROM dbo.data_debug_smoke WHERE smoke_id = '${smokeId}'`,
    cleanup: `DELETE FROM dbo.data_debug_smoke WHERE smoke_id = '${smokeId}'`,
    assertVerification(result) {
      assert.deepEqual(result.rows, [[smokeValue]]);
    },
  },
};

function requiredEnvironment(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

function positiveInteger(name, fallback) {
  const value = Number(process.env[name] || fallback);
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${name} must be a positive integer`);
  return value;
}

function connectionError(error) {
  return [error?.code, error?.message].filter(Boolean).join(': ') || String(error);
}

async function waitForDatabase(adapter, engine) {
  const waitMs = positiveInteger('DATA_DEBUG_TEST_WAIT_MS', 300000);
  const deadline = Date.now() + waitMs;
  let lastError;

  while (Date.now() < deadline) {
    try {
      return await adapter.test({ timeoutMs: Math.min(10000, Math.max(1000, deadline - Date.now())) });
    } catch (error) {
      lastError = error;
      await delay(Math.min(5000, Math.max(0, deadline - Date.now())));
    }
  }

  throw new Error(`${engine} did not become ready within ${waitMs}ms (${connectionError(lastError)})`);
}

function validateMutation(engine, input, target) {
  if (engine === 'mongodb') requireMongoMutation(input, target);
  else if (engine === 'redis') requireRedisMutation(input, target);
  else requireSqlMutation(input, engine);
}

const engine = requiredEnvironment('DATA_DEBUG_TEST_ENGINE');
const spec = specs[engine];
if (!spec) throw new Error(`Unsupported integration test engine: ${engine}`);

const database = requiredEnvironment('DATA_DEBUG_TEST_DATABASE');
const target = {
  id: `ci-${engine}`,
  engine,
  environment: 'test',
  ...spec.target,
  connection: {
    ...spec.target.connection,
    host: process.env.DATA_DEBUG_TEST_HOST || '127.0.0.1',
    port: positiveInteger('DATA_DEBUG_TEST_PORT'),
    database,
  },
};
const credential = {
  id: `ci-${engine}-mutation`,
  username: requiredEnvironment('DATA_DEBUG_TEST_USERNAME'),
  mode: 'mutation',
  ...(engine === 'redis' ? {} : { secret: requiredEnvironment('DATA_DEBUG_TEST_PASSWORD') }),
};

const adapter = await createAdapter(target, credential);
const connection = await waitForDatabase(adapter, engine);
assert.equal(connection.identity.database.toLowerCase(), database.toLowerCase());

const inspection = await adapter.inspect({ timeoutMs: 30000 });
assert.equal(inspection.identity.database.toLowerCase(), database.toLowerCase());
assert.ok(inspection.schema && typeof inspection.schema === 'object');

const read = await adapter.executeRead(spec.read, { maxRows: 10, timeoutMs: 30000 });
assert.equal(read.identity.database.toLowerCase(), database.toLowerCase());
assert.ok(read.result && typeof read.result === 'object');

async function executeApprovedMutation(input) {
  validateMutation(engine, input, target);
  return adapter.executeMutation(input, {
    timeoutMs: 30000,
    expectedIdentity: connection.identity,
    transactionMode: engine === 'postgresql' ? 'always' : 'never',
    approvalExpiresAt: new Date(Date.now() + 60000).toISOString(),
  });
}

let mutationCompleted = false;
try {
  const mutation = await executeApprovedMutation(spec.mutation);
  mutationCompleted = true;
  assert.equal(mutation.identity.database.toLowerCase(), database.toLowerCase());

  const verification = await adapter.executeRead(spec.verification, { maxRows: 10, timeoutMs: 30000 });
  assert.equal(verification.identity.database.toLowerCase(), database.toLowerCase());
  spec.assertVerification(verification.result);
} finally {
  if (mutationCompleted) {
    try {
      await executeApprovedMutation(spec.cleanup);
    } catch (error) {
      console.warn(`Best-effort cleanup failed for ${engine}: ${connectionError(error)}`);
    }
  }
}

console.log(`Live adapter smoke passed for ${engine}`);
