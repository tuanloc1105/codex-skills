import assert from 'node:assert/strict';
import { access, mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { withFileLock } from '../src/core/fs.js';

test('stale plan locks fail closed and are not deleted automatically', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'data-debug-lock-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const lock = path.join(root, 'state.lock');
  await writeFile(lock, JSON.stringify({ pid: 2_147_483_647, createdAt: new Date(0).toISOString() }));
  await assert.rejects(withFileLock(lock, async () => {}), { code: 'STALE_LOCK' });
  await access(lock);
});
