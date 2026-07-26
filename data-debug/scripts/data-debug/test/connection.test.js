import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { connectionFromFlags } from '../src/connection.js';

test('connection URL stays in memory and public context omits credentials', (t) => {
  const name = `DATA_DEBUG_TEST_URL_${process.pid}`;
  process.env[name] = 'postgresql://reader:do-not-print@db.internal:5433/application?tls=true';
  t.after(() => { delete process.env[name]; });

  const connection = connectionFromFlags({ 'connection-env': name });
  assert.equal(connection.target.engine, 'postgresql');
  assert.equal(connection.target.connection.port, 5433);
  assert.equal(connection.target.connection.tls, true);
  assert.deepEqual(connection.credential, { username: 'reader', secret: 'do-not-print', mode: 'read' });
  assert.doesNotMatch(JSON.stringify(connection.context), /reader|do-not-print/);
});

test('direct connection flags reference password environment and optional scopes', (t) => {
  const name = `DATA_DEBUG_TEST_PASSWORD_${process.pid}`;
  process.env[name] = 'do-not-print';
  t.after(() => { delete process.env[name]; });
  const connection = connectionFromFlags({
    engine: 'mongodb',
    host: 'mongo.internal',
    database: 'application',
    username: 'debugger',
    'password-env': name,
    tls: true,
    namespace: ['orders', 'customers'],
    'auth-source': 'admin',
  }, { mode: 'mutation' });
  assert.equal(connection.credential.secret, 'do-not-print');
  assert.equal(connection.credential.mode, 'mutation');
  assert.deepEqual(connection.target.allowedNamespaces, ['orders', 'customers']);
  assert.equal(connection.target.connection.authSource, 'admin');
});

test('env files can provide a named connection URL', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'data-debug-env-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const name = `DATA_DEBUG_FILE_URL_${process.pid}`;
  const file = path.join(root, '.env');
  await writeFile(file, `${name}=rediss://:secret@cache.internal:6380/2\n`);
  t.after(() => { delete process.env[name]; });

  const connection = connectionFromFlags({ 'env-file': file, 'connection-env': name });
  assert.equal(connection.target.engine, 'redis');
  assert.equal(connection.target.connection.database, '2');
  assert.equal(connection.target.connection.port, 6380);
  assert.equal(connection.credential.secret, 'secret');
  assert.equal(connection.target.connection.tls, true);
});

test('remote credentials require verified encryption for every engine', (t) => {
  const passwordEnvironment = `DATA_DEBUG_TRANSPORT_PASSWORD_${process.pid}`;
  process.env[passwordEnvironment] = 'do-not-print';
  t.after(() => { delete process.env[passwordEnvironment]; });

  for (const engine of ['postgresql', 'mongodb', 'oracle', 'redis', 'sqlserver']) {
    const flags = {
      engine,
      host: 'db.internal',
      database: engine === 'redis' ? '0' : 'application',
      ...(engine === 'redis' ? {} : { username: 'debugger' }),
      'password-env': passwordEnvironment,
      ...(engine === 'sqlserver' ? { encrypt: false } : { tls: false }),
    };
    assert.throws(
      () => connectionFromFlags(flags),
      { code: 'INSECURE_CREDENTIAL_TRANSPORT' },
      engine,
    );

    const secureFlags = {
      ...flags,
      ...(engine === 'sqlserver' ? { encrypt: true } : { tls: true }),
    };
    assert.doesNotThrow(() => connectionFromFlags(secureFlags), engine);
  }
});

test('loopback credentials may use plaintext transport', (t) => {
  const passwordEnvironment = `DATA_DEBUG_LOOPBACK_PASSWORD_${process.pid}`;
  process.env[passwordEnvironment] = 'do-not-print';
  t.after(() => { delete process.env[passwordEnvironment]; });

  for (const host of ['localhost', '127.0.0.1', '127.42.0.9', '::1', '[::1]', '::ffff:127.0.0.1']) {
    assert.doesNotThrow(() => connectionFromFlags({
      engine: 'postgresql',
      host,
      database: 'application',
      username: 'debugger',
      'password-env': passwordEnvironment,
    }), host);
  }
});

test('unverified remote transport needs a fingerprint-bound explicit override', (t) => {
  const passwordEnvironment = `DATA_DEBUG_OVERRIDE_PASSWORD_${process.pid}`;
  process.env[passwordEnvironment] = 'do-not-print';
  t.after(() => { delete process.env[passwordEnvironment]; });
  const base = {
    engine: 'postgresql',
    host: 'db.internal',
    database: 'application',
    username: 'debugger',
    'password-env': passwordEnvironment,
    tls: true,
    'trust-server-certificate': true,
  };
  assert.throws(() => connectionFromFlags(base), { code: 'INSECURE_CREDENTIAL_TRANSPORT' });

  const overridden = connectionFromFlags({
    ...base,
    'allow-insecure-credential-transport': true,
  });
  assert.equal(overridden.context.target.allowInsecureCredentialTransport, true);

  const withoutOverride = connectionFromFlags({ engine: 'redis', host: 'cache.internal', database: '0' });
  const withOverride = connectionFromFlags({
    engine: 'redis',
    host: 'cache.internal',
    database: '0',
    'allow-insecure-credential-transport': true,
  });
  assert.notEqual(withoutOverride.target.targetFingerprint, withOverride.target.targetFingerprint);
});

test('Redis URL transport distinguishes redis and rediss schemes', (t) => {
  const name = `DATA_DEBUG_REDIS_TRANSPORT_URL_${process.pid}`;
  t.after(() => { delete process.env[name]; });

  process.env[name] = 'redis://:do-not-print@cache.internal/0';
  assert.throws(
    () => connectionFromFlags({ 'connection-env': name }),
    { code: 'INSECURE_CREDENTIAL_TRANSPORT' },
  );
  const overridden = connectionFromFlags({
    'connection-env': name,
    'allow-insecure-credential-transport': true,
  });
  assert.equal(overridden.context.target.allowInsecureCredentialTransport, true);

  process.env[name] = 'rediss://:do-not-print@cache.internal/0';
  assert.equal(connectionFromFlags({ 'connection-env': name }).target.connection.tls, true);
});

test('connection parser rejects unsupported engines and cross-engine scopes', () => {
  assert.throws(() => connectionFromFlags({
    engine: 'mysql', host: 'db.internal', database: 'application', username: 'reader',
  }), { code: 'UNSUPPORTED_ENGINE' });
  assert.throws(() => connectionFromFlags({
    engine: 'postgresql', host: 'db.internal', database: 'application', username: 'reader', 'key-prefix': 'app:',
  }), { code: 'INVALID_ARGUMENT' });
});

test('connection parser rejects mixed URI and direct connection sources', (t) => {
  const name = `DATA_DEBUG_MIXED_URL_${process.pid}`;
  process.env[name] = 'postgresql://reader@db.internal/application';
  t.after(() => { delete process.env[name]; });
  assert.throws(() => connectionFromFlags({
    'connection-env': name,
    host: 'other.internal',
  }), { code: 'INVALID_ARGUMENT' });
});
