import assert from 'node:assert/strict';
import test from 'node:test';
import { createAdapter } from '../src/adapters/index.js';

const targets = {
  mongodb: {
    connection: { host: '127.0.0.1', port: 27017, database: 'data_debug', authSource: 'admin', tls: false },
    allowedNamespaces: ['ci_smoke'],
  },
  oracle: {
    connection: { host: '127.0.0.1', port: 1521, database: 'FREEPDB1', service: 'FREEPDB1', tls: false },
  },
  postgresql: {
    connection: { host: '127.0.0.1', port: 5432, database: 'data_debug', tls: false },
  },
  redis: {
    connection: { host: '127.0.0.1', port: 6379, database: '0', tls: false },
    keyPrefix: 'ci:',
  },
  sqlserver: {
    connection: { host: '127.0.0.1', port: 1433, database: 'master', encrypt: false, tls: false },
  },
};

test('all supported adapter factories load on the current platform', async (t) => {
  for (const [engine, target] of Object.entries(targets)) {
    await t.test(engine, async () => {
      const adapter = await createAdapter(
        { id: `ci-${engine}`, engine, environment: 'test', ...target },
        { id: `ci-${engine}-read`, username: engine === 'redis' ? 'default' : 'data_debug', secret: 'unused', mode: 'read' },
      );

      for (const method of ['test', 'inspect', 'executeRead', 'executeMutation']) {
        assert.equal(typeof adapter[method], 'function', `${engine}.${method} must be callable`);
      }
    });
  }
});
