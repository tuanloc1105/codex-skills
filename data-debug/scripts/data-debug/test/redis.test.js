import assert from 'node:assert/strict';
import test from 'node:test';
import {
  createRedisAdapter,
  formatRedisReply,
  parseRedisClientInfo,
  parseRedisInfo,
  redisClientOptions,
} from '../src/adapters/redis.js';
import { DataDebugError } from '../src/core/errors.js';

function fakeRedisModule({ mutationError } = {}) {
  const calls = [];
  let open = false;
  const client = {
    get isOpen() { return open; },
    withTypeMapping() { return this; },
    on() { return this; },
    async connect() {
      calls.push('connect');
      open = true;
    },
    async sendCommand(argv) {
      calls.push(argv);
      if (argv[0] === 'CLIENT') return 'id=7 db=2 user=writer name=';
      if (argv[0] === 'ACL') return 'writer';
      if (argv[0] === 'INFO') return 'redis_version:8.0.1\r\nredis_mode:standalone\r\nrun_id:test-run\r\n';
      if (mutationError) throw mutationError;
      return 'OK';
    },
    destroy() {
      calls.push('destroy');
      open = false;
    },
  };
  return {
    calls,
    redisModule: {
      RESP_TYPES: { BLOB_STRING: 'blob-string' },
      createClient() { return client; },
    },
  };
}

function redisMutationFixture() {
  const target = {
    engine: 'redis',
    connection: {
      host: 'cache.internal', port: 6380, database: '2', tls: false,
    },
  };
  const credential = { username: 'writer', secret: 'do-not-log', mode: 'mutation' };
  const expectedIdentity = {
    database: '2',
    principal: 'writer',
    serverIdentity: 'cache.internal:6380',
    instanceRunId: 'test-run',
  };
  const input = {
    operation: 'command',
    command: 'SET',
    arguments: { key: 'app:item', value: 'value' },
  };
  return { target, credential, expectedIdentity, input };
}

test('Redis client options disable reconnect, offline queue, and implicit client metadata', () => {
  const target = {
    connection: {
      host: 'cache.internal', port: 6380, database: '2', tls: true, trustServerCertificate: false,
    },
  };
  const options = redisClientOptions(target, { username: 'reader', secret: 'do-not-log' }, 1234);
  assert.equal(options.username, 'reader');
  assert.equal(options.password, 'do-not-log');
  assert.equal(options.database, 2);
  assert.equal(options.url, undefined);
  assert.equal(options.RESP, 2);
  assert.equal(options.disableOfflineQueue, true);
  assert.equal(options.disableClientInfo, true);
  assert.equal(options.maintNotifications, 'disabled');
  assert.equal(options.commandOptions.timeout, 1234);
  assert.equal(options.socket.connectTimeout, 1234);
  assert.equal(options.socket.socketTimeout, 1234);
  assert.equal(options.socket.reconnectStrategy, false);
  assert.equal(options.socket.rejectUnauthorized, true);
});

test('Redis INFO and CLIENT INFO parsers extract identity metadata', () => {
  assert.deepEqual(parseRedisInfo(Buffer.from('# Server\r\nredis_version:8.0.1\r\nredis_mode:standalone\r\n')), {
    redis_version: '8.0.1',
    redis_mode: 'standalone',
  });
  assert.deepEqual(parseRedisClientInfo(Buffer.from('id=7 db=2 user=reader name=')), {
    id: '7', db: '2', user: 'reader', name: '',
  });
});

test('Redis SCAN formatting preserves cursor, prefix scope, and complete-page limits', () => {
  const operation = { resultKind: 'scan', scope: 'keyspace', keyPrefix: 'app:' };
  const result = formatRedisReply(operation, [Buffer.from('7'), [Buffer.from('app:one'), Buffer.from('app:two')]], 2);
  assert.equal(result.nextCursor, '7');
  assert.equal(result.rowCount, 2);
  assert.equal(result.truncated, false);

  assert.throws(
    () => formatRedisReply(operation, ['0', ['other:key']], 10),
    { code: 'NAMESPACE_NOT_ALLOWED' },
  );
  assert.throws(
    () => formatRedisReply(operation, ['0', ['app:one', 'app:two']], 1),
    { code: 'OUTPUT_TOO_LARGE' },
  );
});

test('Redis paired scan and sorted-set responses become bounded structured rows', () => {
  const hash = formatRedisReply(
    { resultKind: 'hscan', scope: 'key' },
    ['0', ['name', 'Ada', 'role', 'admin']],
    2,
  );
  assert.deepEqual(hash.values, [{ field: 'name', value: 'Ada' }, { field: 'role', value: 'admin' }]);

  const sorted = formatRedisReply(
    { resultKind: 'zrange-with-scores' },
    ['alice', '42', 'bob', '7'],
    2,
  );
  assert.deepEqual(sorted.values, [{ member: 'alice', score: '42' }, { member: 'bob', score: '7' }]);
});

test('Redis binary scalar replies preserve bytes in the structured output', () => {
  const result = formatRedisReply({ resultKind: 'scalar' }, Buffer.from('known-value'), 1);
  assert.deepEqual(result.value, { $binary: Buffer.from('known-value').toString('base64') });
});

test('Redis SLOWLOG formatting never returns raw command arguments or client metadata', () => {
  const result = formatRedisReply(
    { resultKind: 'slowlog' },
    [[1, 1700000000, 50, ['SET', 'app:token', 'super-secret'], '10.0.0.1:1234', 'worker']],
    10,
  );
  assert.equal(result.entries[0].command, 'SET');
  assert.equal(result.entries[0].argumentCount, 2);
  assert.equal(result.entries[0].commandArgumentsOmitted, true);
  assert.doesNotMatch(JSON.stringify(result), /super-secret|10\.0\.0\.1|worker/);
});

test('Redis mutation verifies identity and approval immediately before one allowlisted send', async () => {
  const { target, credential, expectedIdentity, input } = redisMutationFixture();
  const fake = fakeRedisModule();
  const adapter = await createRedisAdapter(target, credential, fake.redisModule);
  const result = await adapter.executeMutation(input, {
    timeoutMs: 1000,
    expectedIdentity,
    approvalExpiresAt: new Date(Date.now() + 60_000).toISOString(),
  });

  assert.equal(result.result, 'OK');
  assert.equal(result.transactional, false);
  assert.deepEqual(fake.calls, [
    'connect',
    ['CLIENT', 'INFO'],
    ['ACL', 'WHOAMI'],
    ['INFO', 'server'],
    ['SET', 'app:item', 'value'],
    'destroy',
  ]);
});

test('Redis mutation does not send the write after approval expiry', async () => {
  const { target, credential, expectedIdentity, input } = redisMutationFixture();
  const fake = fakeRedisModule();
  const adapter = await createRedisAdapter(target, credential, fake.redisModule);

  await assert.rejects(
    adapter.executeMutation(input, {
      timeoutMs: 1000,
      expectedIdentity,
      approvalExpiresAt: new Date(Date.now() - 1_000).toISOString(),
    }),
    { code: 'PLAN_EXPIRED' },
  );
  assert.equal(fake.calls.some((entry) => Array.isArray(entry) && entry[0] === 'SET'), false);
});

test('Redis mutation does not send the write when planned identity changed', async () => {
  const { target, credential, expectedIdentity, input } = redisMutationFixture();
  const fake = fakeRedisModule();
  const adapter = await createRedisAdapter(target, credential, fake.redisModule);

  await assert.rejects(
    adapter.executeMutation(input, {
      timeoutMs: 1000,
      expectedIdentity: { ...expectedIdentity, serverIdentity: 'other.internal:6380' },
      approvalExpiresAt: new Date(Date.now() + 60_000).toISOString(),
    }),
    { code: 'TARGET_IDENTITY_MISMATCH' },
  );
  assert.equal(fake.calls.some((entry) => Array.isArray(entry) && entry[0] === 'SET'), false);
});

test('Redis mutation reports an unknown outcome and redacts secrets after send', async () => {
  const { target, credential, expectedIdentity, input } = redisMutationFixture();
  const fake = fakeRedisModule({
    mutationError: new DataDebugError('DATABASE_TIMEOUT', `socket timed out with ${credential.secret}`),
  });
  const adapter = await createRedisAdapter(target, credential, fake.redisModule);

  await assert.rejects(
    adapter.executeMutation(input, {
      timeoutMs: 1000,
      expectedIdentity,
      approvalExpiresAt: new Date(Date.now() + 60_000).toISOString(),
    }),
    (error) => {
      assert.equal(error.code, 'MUTATION_OUTCOME_UNKNOWN');
      assert.equal(error.details?.requiresVerification, true);
      assert.doesNotMatch(error.message, /do-not-log/);
      return true;
    },
  );
});
