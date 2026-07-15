import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import test from 'node:test';

const cli = fileURLToPath(new URL('../bin/agent-db.js', import.meta.url));

function invoke(args, { cwd, env }) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cli, ...args], {
      cwd,
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

test('CLI initializes a project, binds a target, and fails closed without credentials', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-cli-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const cwd = path.join(temp, 'workspace');
  await mkdir(cwd, { recursive: true });
  const env = { AGENT_DB_HOME: path.join(temp, 'runtime') };

  const version = await invoke(['--version'], { cwd, env });
  assert.equal(version.status, 0);
  assert.equal(JSON.parse(version.stdout).command, 'version');

  const initialized = await invoke(['project', 'init', '--name', 'CLI Test'], { cwd, env });
  assert.equal(initialized.status, 0, initialized.stderr || initialized.stdout);
  assert.equal(JSON.parse(initialized.stdout).data.name, 'CLI Test');

  const added = await invoke([
    'target', 'add', '--id', 'staging', '--engine', 'postgresql', '--environment', 'staging',
    '--host', 'db.internal', '--database', 'application',
  ], { cwd, env });
  assert.equal(added.status, 0, added.stderr || added.stdout);
  assert.equal(JSON.parse(added.stdout).data.id, 'staging');

  const shown = await invoke(['project', 'show'], { cwd, env });
  assert.equal(shown.status, 0, shown.stderr || shown.stdout);
  assert.equal(JSON.parse(shown.stdout).data.manifest.targets[0].id, 'staging');
  assert.equal(JSON.parse(shown.stdout).data.manifest.targets[0].connection.tls, true);

  const read = await invoke(['read', '--target', 'staging', '--text', 'SELECT 1'], { cwd, env });
  assert.equal(read.status, 1);
  assert.equal(JSON.parse(read.stdout).error.code, 'CREDENTIAL_REQUIRED');
});

test('CLI registers a scoped Redis target and rejects mutation mode before credentials', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-cli-redis-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const cwd = path.join(temp, 'workspace');
  await mkdir(cwd, { recursive: true });
  const env = { AGENT_DB_HOME: path.join(temp, 'runtime') };

  const initialized = await invoke(['project', 'init', '--name', 'Redis CLI Test'], { cwd, env });
  assert.equal(initialized.status, 0, initialized.stderr || initialized.stdout);
  const added = await invoke([
    'target', 'add', '--id', 'cache', '--engine', 'redis', '--environment', 'test',
    '--host', 'cache.internal', '--database', '0', '--key-prefix', 'app:',
    '--expected-server-identity', 'cache.internal:6379',
  ], { cwd, env });
  assert.equal(added.status, 0, added.stderr || added.stdout);
  const target = JSON.parse(added.stdout).data;
  assert.equal(target.connection.port, 6379);
  assert.equal(target.connection.tls, true);
  assert.equal(target.keyPrefix, 'app:');

  const read = await invoke([
    'read', '--target', 'cache', '--text',
    JSON.stringify({ operation: 'command', command: 'GET', arguments: { key: 'app:user:1' } }),
  ], { cwd, env });
  assert.equal(read.status, 1);
  assert.equal(JSON.parse(read.stdout).error.code, 'CREDENTIAL_REQUIRED');

  const mutation = await invoke([
    'mutation', 'prepare', '--target', 'cache', '--text', '{}',
  ], { cwd, env });
  assert.equal(mutation.status, 1);
  assert.equal(JSON.parse(mutation.stdout).error.code, 'UNSUPPORTED_OPERATION');

  const mutationCredential = await invoke([
    'credential', 'status', '--target', 'cache', '--mode', 'mutation',
  ], { cwd, env });
  assert.equal(mutationCredential.status, 1);
  assert.equal(JSON.parse(mutationCredential.stdout).error.code, 'UNSUPPORTED_OPERATION');
});
