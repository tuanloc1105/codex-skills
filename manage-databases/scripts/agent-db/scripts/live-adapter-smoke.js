import assert from 'node:assert/strict';
import { setTimeout as delay } from 'node:timers/promises';
import { createAdapter } from '../src/adapters/index.js';

const specs = {
  mongodb: {
    target: {
      connection: { authSource: 'admin', tls: false },
      allowedNamespaces: ['ci_smoke'],
    },
    read: { operation: 'estimatedDocumentCount', collection: 'ci_smoke' },
  },
  oracle: {
    target: {
      connection: { service: 'FREEPDB1', tls: false, trustServerCertificate: false },
    },
    read: 'SELECT 1 AS smoke_test FROM DUAL',
  },
  postgresql: {
    target: { connection: { tls: false } },
    read: 'SELECT 1 AS smoke_test',
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
  },
  sqlserver: {
    target: { connection: { encrypt: false, tls: false, trustServerCertificate: false } },
    read: 'SELECT 1 AS smoke_test',
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
  const waitMs = positiveInteger('AGENT_DB_TEST_WAIT_MS', 300000);
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

const engine = requiredEnvironment('AGENT_DB_TEST_ENGINE');
const spec = specs[engine];
if (!spec) throw new Error(`Unsupported integration test engine: ${engine}`);

const database = requiredEnvironment('AGENT_DB_TEST_DATABASE');
const target = {
  id: `ci-${engine}`,
  engine,
  environment: 'test',
  ...spec.target,
  connection: {
    ...spec.target.connection,
    host: process.env.AGENT_DB_TEST_HOST || '127.0.0.1',
    port: positiveInteger('AGENT_DB_TEST_PORT'),
    database,
  },
};
const credential = {
  id: `ci-${engine}-read`,
  username: requiredEnvironment('AGENT_DB_TEST_USERNAME'),
  mode: 'read',
  ...(engine === 'redis' ? {} : { secret: requiredEnvironment('AGENT_DB_TEST_PASSWORD') }),
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

console.log(`Live adapter smoke passed for ${engine}`);
