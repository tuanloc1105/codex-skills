import assert from 'node:assert/strict';
import { access, chmod, mkdtemp, rm, stat, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { atomicWriteInExistingDirectory, withFileLock } from '../src/core/fs.js';

test('stale locks fail closed and are not deleted automatically', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-lock-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const lock = path.join(root, 'state.lock');
  await writeFile(lock, JSON.stringify({ pid: 2_147_483_647, createdAt: new Date(0).toISOString() }));
  await assert.rejects(withFileLock(lock, async () => {}), { code: 'STALE_LOCK' });
  await access(lock);
});

test('project marker writes do not tighten permissions on an existing POSIX parent', {
  skip: process.platform === 'win32',
}, async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-marker-mode-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await chmod(root, 0o750);
  await atomicWriteInExistingDirectory(path.join(root, '.agent-db-project.json'), '{}\n');
  assert.equal((await stat(root)).mode & 0o777, 0o750);
  assert.equal((await stat(path.join(root, '.agent-db-project.json'))).mode & 0o777, 0o600);
});
