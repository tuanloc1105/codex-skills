import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const cli = fileURLToPath(new URL('../bin/data-debug.js', import.meta.url));

function invoke(args, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cli, ...args], {
      env: { ...process.env, ...env },
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (status) => resolve({ status, stdout, stderr }));
  });
}

const postgres = [
  '--engine', 'postgresql', '--host', 'db.internal', '--database', 'application', '--username', 'reader',
];

test('CLI exposes the renamed entrypoint and stateless help', async () => {
  const version = await invoke(['--version']);
  assert.equal(version.status, 0);
  assert.equal(JSON.parse(version.stdout).data.version, '0.3.0');

  const help = await invoke(['--help']);
  assert.equal(help.status, 0);
  const payload = JSON.parse(help.stdout);
  assert.equal(payload.command, 'help');
  assert.match(payload.data.usage.join('\n'), /data-debug mutation preview/);
  assert.match(JSON.stringify(payload.data), /--auth-source/);
  assert.match(JSON.stringify(payload.data), /--trust-server-certificate/);
  assert.match(JSON.stringify(payload.data), /--allow-insecure-credential-transport/);
  assert.match(JSON.stringify(payload.data), /--max-rows/);
  assert.doesNotMatch(help.stdout, /project init|credential set/);
});

test('read command rejects mutation input before any connection attempt', async () => {
  const result = await invoke(['read', ...postgres, '--text', "UPDATE jobs SET status = 'done'"]);
  assert.equal(result.status, 1);
  assert.equal(result.stdout, '');
  assert.equal(JSON.parse(result.stderr).error.code, 'READ_ONLY_VIOLATION');
});

test('mutation preview rejects DDL and Redis admin commands before connecting', async () => {
  const ddl = await invoke(['mutation', 'preview', ...postgres, '--text', 'DROP TABLE jobs']);
  assert.equal(ddl.status, 1);
  assert.equal(JSON.parse(ddl.stderr).error.code, 'UNSUPPORTED_OPERATION');

  const redis = await invoke([
    'mutation', 'preview', '--engine', 'redis', '--host', 'cache.internal', '--database', '0',
    '--text', JSON.stringify({ operation: 'command', command: 'FLUSHALL', arguments: {} }),
  ]);
  assert.equal(redis.status, 1);
  assert.equal(JSON.parse(redis.stderr).error.code, 'UNSUPPORTED_OPERATION');
});

test('CLI accepts connection URLs only through environment references', async () => {
  const result = await invoke([
    'read', '--connection-env', 'TEST_DATA_DEBUG_URL', '--text', 'DELETE FROM jobs',
  ], { TEST_DATA_DEBUG_URL: 'postgresql://reader:do-not-print@db.internal/application?tls=true' });
  assert.equal(result.status, 1);
  assert.equal(JSON.parse(result.stderr).error.code, 'READ_ONLY_VIOLATION');
  assert.doesNotMatch(result.stderr, /do-not-print/);
});

test('CLI rejects insecure remote credential transport before connecting', async () => {
  const result = await invoke([
    'test', '--connection-env', 'TEST_DATA_DEBUG_INSECURE_URL',
  ], { TEST_DATA_DEBUG_INSECURE_URL: 'redis://:do-not-print@cache.internal/0' });
  assert.equal(result.status, 1);
  assert.equal(JSON.parse(result.stderr).error.code, 'INSECURE_CREDENTIAL_TRANSPORT');
  assert.doesNotMatch(result.stderr, /do-not-print|redis:\/\//);
});
