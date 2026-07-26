import assert from 'node:assert/strict';
import test from 'node:test';
import {
  classifyMongoRead,
  classifyRedisRead,
  classifySqlMutation,
  classifySqlRead,
  requireMongoMutation,
  requireReadOperation,
  requireRedisMutation,
  requireSqlMutation,
  resolveTransactionMode,
} from '../src/security/safety.js';

test('SQL read policy accepts one conservative read statement', () => {
  assert.equal(classifySqlRead("-- read only\nSELECT ';UPDATE' AS value;").classification, 'read');
  assert.equal(classifySqlRead('WITH rows AS (SELECT 1) SELECT * FROM rows').classification, 'read');
  assert.equal(
    classifySqlRead("SELECT NQ'[quoted' UTL_HTTP.REQUEST(''ignored'') text]' FROM dual", 'oracle').classification,
    'read',
  );
});

test('SQL policy interprets square brackets according to the selected dialect', () => {
  const read = 'SELECT values[pg_terminate_backend(1)] FROM jobs';
  const mutation = 'UPDATE jobs SET value = values[pg_terminate_backend(1)]';
  assert.notEqual(classifySqlRead(read, 'postgresql').classification, 'read');
  assert.throws(() => requireSqlMutation(mutation, 'postgresql'), { code: 'UNSUPPORTED_OPERATION' });
});

test('SQL read policy rejects state changes and ambiguous statements', () => {
  const cases = [
    ['SELECT 1; SELECT 2', 'postgresql'],
    ['WITH changed AS (DELETE FROM jobs RETURNING *) SELECT * FROM changed', 'postgresql'],
    ['SELECT * INTO backup_users FROM users', 'postgresql'],
    ['SELECT * FROM jobs FOR UPDATE', 'postgresql'],
    ['SELECT order_seq.NEXTVAL FROM dual', 'oracle'],
    ['EXPLAIN ANALYZE SELECT * FROM users', 'postgresql'],
    ['EXEC dbo.read_only_looking_procedure', 'sqlserver'],
    ['SELECT pg_terminate_backend(123)', 'postgresql'],
    ["SELECT pg_read_file('/etc/passwd')", 'postgresql'],
    ['SELECT * FROM OtherDb.dbo.secrets', 'sqlserver'],
    ['SELECT * FROM [LinkedSrv].[OtherDb].[dbo].[secrets]', 'sqlserver'],
    ['SELECT * FROM OtherDb..secrets', 'sqlserver'],
    ['SELECT * FROM LinkedSrv.OtherDb..secrets', 'sqlserver'],
    ['SELECT OtherDb.dbo.secret_fn()', 'sqlserver'],
    ['SELECT * FROM secrets@prod_link', 'oracle'],
    ['SELECT remote_fn@prod_link(1) FROM dual', 'oracle'],
    ["SELECT UTL_HTTP.REQUEST('https://example.invalid') FROM dual", 'oracle'],
    ["SELECT DBMS_XMLGEN.GETXML('SELECT * FROM secrets@prod_link') FROM dual", 'oracle'],
  ];
  for (const [sql, engine] of cases) {
    assert.notEqual(classifySqlRead(sql, engine).classification, 'read', sql);
    assert.throws(() => requireReadOperation(engine, sql), { code: 'READ_ONLY_VIOLATION' });
  }
  assert.throws(
    () => classifySqlRead('SELECT U&"identifier" FROM jobs', 'postgresql'),
    { code: 'UNSUPPORTED_OPERATION' },
  );
  assert.throws(
    () => requireReadOperation('postgresql', 'SELECT U&"identifier" FROM jobs'),
    { code: 'UNSUPPORTED_OPERATION' },
  );
});

test('SQL mutation policy allows one data mutation only', () => {
  for (const sql of [
    "INSERT INTO jobs(id, status) VALUES (1, 'queued')",
    "UPDATE jobs SET status = 'done' WHERE id = 1",
    'DELETE FROM jobs WHERE id = 1',
    "INSERT INTO jobs(id, status) VALUES (2, 'queued') ON CONFLICT (id) DO UPDATE SET status = 'queued'",
  ]) {
    assert.equal(classifySqlMutation(sql).classification, 'mutation');
    assert.equal(requireSqlMutation(sql), sql);
  }
  for (const sql of [
    'UPDATE jobs SET status = 1; DELETE FROM jobs',
    'UPDATE jobs SET status = 1\nDELETE FROM audit WHERE id = 2',
    "INSERT INTO jobs(id) VALUES (1)\nUPDATE users SET admin = 1",
    'DELETE FROM jobs WHERE id = 1\nDROP TABLE audit',
    "UPDATE jobs SET status = E'a\\\''; DROP TABLE audit; -- '",
    "UPDATE jobs SET status = q'[a'b]' || UTL_INADDR.GET_HOST_ADDRESS(NULL) -- '",
    'CREATE TABLE jobs(id int)',
    'ALTER TABLE jobs ADD COLUMN note text',
    "CALL finish_job(1)",
    "INSERT INTO jobs EXEC dbo.next_job",
    'INSERT INTO audit_log(ok) SELECT pg_terminate_backend(123)',
    "INSERT INTO fetched(value) SELECT UTL_HTTP.REQUEST('https://example.invalid') FROM dual",
    "INSERT INTO fetched(value) VALUES (DBMS_XMLQUERY.GETXML('SELECT * FROM secrets@prod_link'))",
    "INSERT INTO local_copy SELECT * FROM OPENROWSET('provider', 'source', 'query')",
    "UPDATE OtherDb.dbo.jobs SET status = 'done'",
    "UPDATE [LinkedSrv].[OtherDb].[dbo].[jobs] SET status = 'done'",
    "UPDATE OtherDb..jobs SET status = 'done'",
    "DELETE LinkedSrv.OtherDb..jobs WHERE id = 1",
    "INSERT OtherDb.dbo.jobs(id) VALUES (1)",
    "DELETE [LinkedSrv].[OtherDb].[dbo].[jobs] WHERE id = 1",
    "UPDATE local_jobs SET status = OtherDb.dbo.remote_status()",
    "UPDATE jobs@prod_link SET status = 'done'",
    "UPDATE local_jobs SET status = remote_fn@prod_link(1)",
    'UPDATE jobs SET status = U&"identifier"(1)',
    "UPDATE jobs /* outer /* nested */ outer */ SET status = 'done'",
    'WITH changed AS (DELETE FROM jobs RETURNING *) SELECT * FROM changed',
  ]) {
    assert.throws(() => requireSqlMutation(sql), { code: 'UNSUPPORTED_OPERATION' });
  }
});

test('MongoDB read policy accepts typed reads and rejects write stages', () => {
  assert.equal(classifyMongoRead({ operation: 'find', collection: 'users', filter: {} }).classification, 'read');
  assert.equal(classifyMongoRead({
    operation: 'aggregate',
    collection: 'users',
    pipeline: [{ $facet: { persisted: [{ $merge: 'archive' }] } }],
  }).classification, 'mutation');
  assert.throws(
    () => requireReadOperation('mongodb', { operation: 'deleteMany', collection: 'users' }),
    { code: 'READ_ONLY_VIOLATION' },
  );
  assert.throws(
    () => requireReadOperation('mongodb', { operation: 'find', collection: 'users', filters: { active: true } }),
    { code: 'INVALID_ARGUMENT' },
  );
});

test('MongoDB policy applies optional collection scope and blocks server-side JavaScript', () => {
  const target = { allowedNamespaces: ['orders', 'customers'] };
  assert.equal(classifyMongoRead({
    operation: 'aggregate',
    collection: 'orders',
    pipeline: [{ $lookup: { from: 'customers', pipeline: [], as: 'customer' } }],
  }, target).classification, 'read');
  for (const operation of [
    { operation: 'find', collection: 'orders', filter: { $where: 'sleep(1000)' } },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $lookup: { from: 'secrets', pipeline: [], as: 'x' } }] },
    { operation: 'aggregate', collection: 'orders', pipeline: [{ $project: { value: { $function: { body: 'function(){}', args: [], lang: 'js' } } } }] },
  ]) {
    assert.notEqual(classifyMongoRead(operation, target).classification, 'read');
  }
});

test('MongoDB mutation policy allows typed data changes only', () => {
  const target = { allowedNamespaces: ['orders'] };
  const operation = {
    operation: 'updateOne',
    collection: 'orders',
    filter: { id: 1 },
    update: { $set: { status: 'done' } },
    options: { upsert: false, comment: 'approved' },
  };
  assert.equal(requireMongoMutation(operation, target).operation, 'updateOne');
  for (const rejected of [
    { operation: 'find', collection: 'orders' },
    { operation: 'command', command: { dropDatabase: 1 } },
    { operation: 'createCollection', collection: 'orders' },
    { operation: 'createIndex', collection: 'orders', keys: { id: 1 } },
    { operation: 'updateOne', collection: 'secrets', update: { $set: { x: 1 } } },
    { operation: 'updateOne', collection: 'orders', update: { $set: { x: { $function: {} } } } },
    { operation: 'updateMany', collection: 'orders', filters: { tenant: 'A' }, update: { $set: { status: 'done' } } },
    { operation: 'deleteMany', collection: 'orders' },
    { operation: 'deleteMany', collection: 'orders', filters: { tenant: 'A' } },
  ]) {
    assert.throws(() => requireMongoMutation(rejected, target));
  }
  assert.equal(requireMongoMutation({
    operation: 'deleteMany', collection: 'orders', filter: {},
  }, target).operation, 'deleteMany');
});

test('transaction strategy wraps PostgreSQL DML and stays explicit elsewhere', () => {
  assert.equal(resolveTransactionMode('postgresql', 'UPDATE jobs SET status = 1'), 'always');
  assert.equal(resolveTransactionMode('oracle', 'UPDATE jobs SET status = 1'), 'never');
  assert.equal(resolveTransactionMode('postgresql', 'UPDATE jobs SET status = 1', 'never'), 'never');
  assert.throws(
    () => resolveTransactionMode('sqlserver', 'UPDATE jobs SET status = 1', 'always'),
    { code: 'UNSUPPORTED_OPERATION' },
  );
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

test('Redis read policy accepts typed reads with optional key scoping', () => {
  const unscoped = classifyRedisRead({
    operation: 'command', command: 'GET', arguments: { key: 'user:42' },
  });
  assert.deepEqual(unscoped.operation.argv, ['GET', 'user:42']);

  const scoped = classifyRedisRead({
    operation: 'command', command: 'SCAN',
    arguments: { cursor: '0', matchSuffix: 'user:*', count: 25, type: 'hash' },
  }, { keyPrefix: 'app:' }, { maxRows: 50 });
  assert.deepEqual(scoped.operation.argv, ['SCAN', '0', 'MATCH', 'app:user:*', 'COUNT', '25', 'TYPE', 'hash']);
  assert.throws(
    () => classifyRedisRead({ operation: 'command', command: 'GET', arguments: { key: 'other:user' } }, { keyPrefix: 'app:' }),
    { code: 'NAMESPACE_NOT_ALLOWED' },
  );
});

test('Redis mutation policy emits argv for the data-write allowlist', () => {
  assert.deepEqual(requireRedisMutation({
    operation: 'command', command: 'SET', arguments: { key: 'app:item', value: 'value', seconds: 60 },
  }).argv, ['SET', 'app:item', 'value', 'EX', '60']);
  assert.deepEqual(requireRedisMutation({
    operation: 'command', command: 'HSET', arguments: { key: 'app:hash', entries: { status: 'ready' } },
  }).argv, ['HSET', 'app:hash', 'status', 'ready']);
  assert.deepEqual(requireRedisMutation({
    operation: 'command', command: 'ZADD', arguments: { key: 'app:scores', entries: [{ score: 1.5, member: 'one' }] },
  }).argv, ['ZADD', 'app:scores', '1.5', 'one']);
});

test('Redis read and mutation policies reject commands outside their allowlists', () => {
  for (const command of ['FLUSHALL', 'CONFIG SET', 'ACL SETUSER', 'EVAL', 'FCALL', 'MODULE LOAD', 'PUBLISH']) {
    assert.throws(
      () => requireRedisMutation({ operation: 'command', command, arguments: {} }),
      { code: 'UNSUPPORTED_OPERATION' },
    );
  }
  assert.throws(
    () => requireReadOperation('redis', { operation: 'command', command: 'SET', arguments: { key: 'x', value: 'y' } }),
    { code: 'UNSUPPORTED_OPERATION' },
  );
});
