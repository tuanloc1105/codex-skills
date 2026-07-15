import assert from 'node:assert/strict';
import test from 'node:test';
import {
  formatRedisReply,
  parseRedisClientInfo,
  parseRedisInfo,
  redisClientOptions,
} from '../src/adapters/redis.js';

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
