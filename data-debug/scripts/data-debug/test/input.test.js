import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { operationInput } from '../src/core/input.js';

test('file input reads a bounded prefix and rejects content above 1 MiB', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'data-debug-input-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const accepted = path.join(root, 'accepted.sql');
  const rejected = path.join(root, 'rejected.sql');
  await writeFile(accepted, 'SELECT 1');
  await writeFile(rejected, Buffer.alloc((1024 * 1024) + 1, 0x41));

  assert.equal(await operationInput({ file: accepted }), 'SELECT 1');
  await assert.rejects(operationInput({ file: rejected }), { code: 'INPUT_TOO_LARGE' });
});
