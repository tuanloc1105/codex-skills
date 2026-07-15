import assert from 'node:assert/strict';
import test from 'node:test';
import {
  assertNoEmbeddedSecret,
  classifyMongoRead,
  classifyRedisRead,
  classifySqlRead,
  requireMongoMutation,
  requireReadOperation,
  resolveTransactionMode,
} from '../src/security/safety.js';

test('SQL classifier accepts one conservative read statement', () => {
  assert.equal(classifySqlRead("-- read only\nSELECT ';UPDATE' AS value;").classification, 'read');
  assert.equal(classifySqlRead('WITH rows AS (SELECT 1) SELECT * FROM rows').classification, 'read');
});

test('SQL classifier gates state-changing and ambiguous statements', () => {
  const cases = [
    'SELECT 1; SELECT 2',
    'WITH changed AS (DELETE FROM jobs RETURNING *) SELECT * FROM changed',
    'SELECT * INTO backup_users FROM users',
    'SELECT * FROM jobs FOR UPDATE',
    'SELECT order_seq.NEXTVAL FROM dual',
    'SELECT NEXT VALUE FOR dbo.order_seq',
    'SELECT * FROM jobs WITH (UPDLOCK)',
    'SELECT pg_terminate_backend(123)',
    'SELECT * FROM jobs FOR NO KEY UPDATE',
    'EXPLAIN ANALYZE SELECT * FROM users',
    'EXPLAIN PLAN FOR SELECT * FROM users',
    'EXEC dbo.read_only_looking_procedure',
    'SELECT 1\nDENY SELECT ON dbo.t TO analyst',
    'SELECT 1\nUPDATETEXT dbo.t.c @ptr 0 1 0x41',
    'SELECT 1\nDBCC FREEPROCCACHE',
    'SELECT 1\nCHECKPOINT',
    'SELECT 1\nUSE otherdb',
    'SELECT 1\nCOMMIT TRANSACTION',
    'SELECT "pg_terminate_backend"(123)',
    "SELECT * FROM dblink('remote', 'DELETE FROM jobs RETURNING *') AS x(id int)",
    "WITH c AS (SELECT dblink_connect('c','dbname=remote')) SELECT dblink_send_query('c','DELETE FROM jobs') FROM c",
    "SELECT * FROM OPENQUERY(remote_server, 'DELETE FROM jobs')",
    "SELECT UTL_HTTP.REQUEST('https://example.invalid') FROM dual",
  ];
  for (const sql of cases) {
    assert.notEqual(classifySqlRead(sql).classification, 'read', sql);
    assert.throws(() => requireReadOperation('postgresql', sql), { code: 'MUTATION_CONFIRMATION_REQUIRED' });
  }
});

test('SQL classifier ignores blocked words inside quoted values and comments', () => {
  const sql = "SELECT 'DROP TABLE users' AS warning /* DELETE FROM users */";
  assert.equal(classifySqlRead(sql).classification, 'read');
});

test('MongoDB classifier accepts typed reads and blocks nested write stages', () => {
  assert.equal(classifyMongoRead({ operation: 'find', collection: 'users', filter: {} }).classification, 'read');
  const result = classifyMongoRead({
    operation: 'aggregate',
    collection: 'users',
    pipeline: [{ $facet: { persisted: [{ $merge: 'archive' }] } }],
  });
  assert.equal(result.classification, 'mutation');
  assert.throws(
    () => requireReadOperation('mongodb', JSON.stringify({ operation: 'deleteMany', collection: 'users' })),
    { code: 'MUTATION_CONFIRMATION_REQUIRED' },
  );
});

test('MongoDB read policy blocks server-side JavaScript and cross-collection allowlist bypasses', () => {
  const target = { allowedNamespaces: ['orders', 'customers'] };
  const cases = [
    { operation: 'find', collection: 'orders', filter: { $where: 'sleep(1000)' } },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $lookup: { from: 'secrets', pipeline: [], as: 'x' } }] },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $graphLookup: { from: 'secrets', startWith: '$id', connectFromField: 'id', connectToField: 'id', as: 'x' } }] },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $unionWith: 'secrets' }] },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $unionWith: { coll: 'secrets', pipeline: [] } }] },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $project: { value: { $function: { body: 'function(){}', args: [], lang: 'js' } } } }] },
  ];
  for (const operation of cases) {
    assert.notEqual(classifyMongoRead(operation, target).classification, 'read');
    assert.throws(
      () => requireReadOperation('mongodb', operation, target),
      { code: 'MUTATION_CONFIRMATION_REQUIRED' },
    );
  }
  assert.equal(classifyMongoRead({
    operation: 'aggregate', collection: 'orders', pipeline: [{ $lookup: { from: 'customers', pipeline: [], as: 'customer' } }],
  }, target).classification, 'read');
});

test('MongoDB mutation validation rejects reads and unknown operations', () => {
  assert.equal(requireMongoMutation({ operation: 'updateOne' }).operation, 'updateOne');
  assert.throws(() => requireMongoMutation({ operation: 'find' }), { code: 'UNSUPPORTED_OPERATION' });
  assert.throws(() => requireMongoMutation({ operation: 'madeUpOperation' }), { code: 'UNSUPPORTED_OPERATION' });
  assert.throws(
    () => requireMongoMutation(
      { operation: 'command', command: { delete: 'secrets', deletes: [{ q: {}, limit: 0 }] } },
      { allowedNamespaces: ['orders'] },
    ),
    { code: 'NAMESPACE_NOT_ALLOWED' },
  );
  assert.equal(
    requireMongoMutation({ operation: 'command', command: { dropDatabase: 1 } }, { allowedNamespaces: [] }).operation,
    'command',
  );
});

test('MongoDB mutation options cannot redirect or expand the approved namespace', () => {
  const target = { allowedNamespaces: ['orders'] };
  for (const options of [
    { dbName: 'other_db' },
    { authdb: 'other_db' },
    { encryptedFields: { escCollection: 'other' } },
    { viewOn: 'customers' },
    { writeConcern: { w: 0 } },
  ]) {
    assert.throws(
      () => requireMongoMutation({ operation: 'createCollection', collection: 'orders', options }, target),
      { code: 'UNSUPPORTED_OPERATION' },
    );
  }
  assert.throws(
    () => requireMongoMutation({ operation: 'command', command: { insert: 'orders', writeConcern: { w: 0 } } }),
    { code: 'UNSUPPORTED_OPERATION' },
  );
  assert.doesNotThrow(() => requireMongoMutation({
    operation: 'updateOne',
    collection: 'orders',
    filter: { id: 1 },
    update: { $set: { status: 'done' } },
    options: { upsert: false, comment: 'approved' },
  }, target));
});

test('transaction strategy is explicit and conservative', () => {
  assert.equal(resolveTransactionMode('postgresql', 'UPDATE jobs SET status = 1'), 'always');
  assert.equal(resolveTransactionMode('postgresql', 'VACUUM jobs'), 'never');
  assert.equal(resolveTransactionMode('postgresql', 'CREATE INDEX CONCURRENTLY ix ON jobs(id)'), 'never');
  assert.equal(resolveTransactionMode('oracle', 'UPDATE jobs SET status = 1'), 'never');
  assert.equal(resolveTransactionMode('postgresql', 'UPDATE jobs SET status = 1', 'never'), 'never');
  assert.throws(
    () => resolveTransactionMode('sqlserver', 'UPDATE jobs SET status = 1', 'always'),
    { code: 'UNSUPPORTED_OPERATION' },
  );
});

test('mutation preview refuses common embedded credential shapes', () => {
  assert.throws(
    () => assertNoEmbeddedSecret('postgresql', "ALTER ROLE app PASSWORD 'do-not-print'"),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('oracle', "CREATE USER app IDENTIFIED BY do_not_print"),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('oracle', 'CREATE USER app IDENTIFIED/**/BY "do-not-print"'),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('mongodb', { operation: 'command', command: { createUser: 'app', pwd: 'do-not-print' } }),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('mongodb', { operation: 'updateOne', update: { $set: { 'auth.password': 'do-not-print' } } }),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('postgresql', "INSERT INTO config(name, value) VALUES ('api_key', 'do-not-print')"),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('mongodb', { operation: 'updateOne', update: { $set: { name: 'api_key', value: 'do-not-print' } } }),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('sqlserver', "EXEC sp_addlogin 'review_user', 'do-not-print'"),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('mongodb', { operation: 'updateOne', update: { $set: { kind: 'auth', value: 'do-not-print' } } }),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.throws(
    () => assertNoEmbeddedSecret('postgresql', "INSERT INTO config(name, value) VALUES ('encryption_key', 'do-not-print')"),
    { code: 'SECRET_IN_OPERATION' },
  );
  assert.doesNotThrow(() => assertNoEmbeddedSecret('postgresql', "UPDATE jobs SET status = 'done'"));
});

test('deep MongoDB input fails with a structured complexity error', () => {
  const filter = {};
  let cursor = filter;
  for (let depth = 0; depth < 200; depth += 1) {
    cursor.child = {};
    cursor = cursor.child;
  }
  assert.throws(
    () => classifyMongoRead({ operation: 'find', collection: 'orders', filter }),
    { code: 'INPUT_TOO_COMPLEX' },
  );
});

test('Redis classifier accepts typed, prefix-scoped debug commands', () => {
  const target = { keyPrefix: 'app:' };
  const get = classifyRedisRead({
    operation: 'command',
    command: 'get',
    arguments: { key: 'app:user:42' },
  }, target);
  assert.equal(get.classification, 'read');
  assert.deepEqual(get.operation.argv, ['GET', 'app:user:42']);

  const scan = classifyRedisRead({
    operation: 'command',
    command: 'SCAN',
    arguments: { cursor: '0', matchSuffix: 'user:*', count: 25, type: 'hash' },
  }, target, { maxRows: 50 });
  assert.equal(scan.classification, 'read');
  assert.deepEqual(scan.operation.argv, ['SCAN', '0', 'MATCH', 'app:user:*', 'COUNT', '25', 'TYPE', 'hash']);

  const slowlog = classifyRedisRead({
    operation: 'command', command: 'SLOWLOG GET', arguments: { count: 5 },
  }, target, { maxRows: 10 });
  assert.equal(slowlog.operation.resultKind, 'slowlog');
});

test('Redis classifier blocks unknown, mutating, blocking, scripting, and module commands', () => {
  const target = { keyPrefix: 'app:' };
  for (const command of [
    'SET', 'DEL', 'KEYS', 'RANDOMKEY', 'MONITOR', 'XREAD', 'BLPOP', 'EVAL', 'FCALL',
    'CONFIG GET', 'ACL LIST', 'CLIENT LIST', 'FT.SEARCH', 'JSON.GET',
  ]) {
    const result = classifyRedisRead({ operation: 'command', command, arguments: {} }, target);
    assert.notEqual(result.classification, 'read', command);
    assert.throws(
      () => requireReadOperation('redis', { operation: 'command', command, arguments: {} }, target),
      { code: 'UNSUPPORTED_OPERATION' },
    );
  }
});

test('Redis classifier enforces exact schemas, bounds, and key prefix', () => {
  const target = { keyPrefix: 'app:' };
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'GET', arguments: { key: 'other:user' } }, target),
    { code: 'NAMESPACE_NOT_ALLOWED' },
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'GET', arguments: { key: 'app:user', surprise: true } }, target),
    { code: 'INVALID_ARGUMENT' },
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'LRANGE', arguments: { key: 'app:list', start: 0, stop: 100 } }, target, { maxRows: 10 }),
    { code: 'INVALID_ARGUMENT' },
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'XRANGE', arguments: { key: 'app:stream', start: '-', end: '+' } }, target),
    { code: 'INVALID_ARGUMENT' },
  );
  assert.deepEqual(
    classifyRedisRead({
      operation: 'command', command: 'XREVRANGE', arguments: { key: 'app:stream', start: '-', end: '+', count: 5 },
    }, target).operation.argv,
    ['XREVRANGE', 'app:stream', '+', '-', 'COUNT', '5'],
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'MEMORY USAGE', arguments: { key: 'app:user', samples: 0 } }, target),
    { code: 'INVALID_ARGUMENT' },
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'INFO', arguments: { section: 'everything' } }, target),
    { code: 'UNSUPPORTED_OPERATION' },
  );
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'SCAN', arguments: { cursor: '0', match: '*' } }, target),
    { code: 'INVALID_ARGUMENT' },
  );
});
