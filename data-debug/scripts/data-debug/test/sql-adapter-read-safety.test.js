import assert from 'node:assert/strict';
import test from 'node:test';
import { createOracleAdapter } from '../src/adapters/oracle.js';
import { createPostgresqlAdapter } from '../src/adapters/postgresql.js';
import { createSqlServerAdapter } from '../src/adapters/sqlserver.js';

const credential = { username: 'reader', secret: 'unused', mode: 'read' };
const options = { maxRows: 10, timeoutMs: 1000 };

const cases = [
  {
    engine: 'postgresql',
    createAdapter: createPostgresqlAdapter,
    target: {
      engine: 'postgresql',
      connection: { host: '127.0.0.1', port: 1, database: 'data_debug', tls: false },
    },
  },
  {
    engine: 'sqlserver',
    createAdapter: createSqlServerAdapter,
    target: {
      engine: 'sqlserver',
      connection: { host: '127.0.0.1', port: 1, database: 'data_debug', encrypt: false, tls: false },
    },
  },
  {
    engine: 'oracle',
    createAdapter: createOracleAdapter,
    target: {
      engine: 'oracle',
      connection: { host: '127.0.0.1', port: 1, database: 'FREEPDB1', service: 'FREEPDB1', tls: false },
    },
  },
];

for (const { engine, createAdapter, target } of cases) {
  test(`${engine} executeRead rejects mutations before connecting`, async () => {
    const adapter = await createAdapter(target, credential);
    await assert.rejects(
      adapter.executeRead('DELETE FROM users', options),
      { code: 'READ_ONLY_VIOLATION' },
    );
  });

  test(`${engine} executeMutation rejects DDL before connecting`, async () => {
    const adapter = await createAdapter(target, { ...credential, mode: 'mutation' });
    await assert.rejects(
      adapter.executeMutation('DROP TABLE users', {
        timeoutMs: 1000,
        expectedIdentity: {},
        transactionMode: 'never',
        approvalExpiresAt: new Date(Date.now() + 60_000).toISOString(),
      }),
      { code: 'UNSUPPORTED_OPERATION' },
    );
  });
}
