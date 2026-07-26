import { randomUUID } from 'node:crypto';
import { mkdir, open, readFile, rename, chmod, rm } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { DataDebugError } from './errors.js';

export async function ensurePrivateDirectory(directory) {
  await mkdir(directory, { recursive: true, mode: 0o700 });
  if (process.platform !== 'win32') {
    await chmod(directory, 0o700);
  }
}

export async function readJson(filePath, fallback = undefined) {
  try {
    return JSON.parse(await readFile(filePath, 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT' && fallback !== undefined) return fallback;
    throw error;
  }
}

async function writeAtomically(filePath, content, mode) {
  const temporaryPath = `${filePath}.${randomUUID()}.tmp`;
  const handle = await open(temporaryPath, 'wx', mode);
  try {
    await handle.writeFile(content, 'utf8');
    await handle.sync();
  } finally {
    await handle.close();
  }
  await rename(temporaryPath, filePath);
  if (process.platform !== 'win32') {
    await chmod(filePath, mode);
  }
}

export async function atomicWrite(filePath, content, mode = 0o600) {
  await ensurePrivateDirectory(path.dirname(filePath));
  await writeAtomically(filePath, content, mode);
}

export async function atomicWriteJson(filePath, value) {
  await atomicWrite(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

export async function writeJsonExclusive(filePath, value) {
  await ensurePrivateDirectory(path.dirname(filePath));
  const handle = await open(filePath, 'wx', 0o600);
  try {
    await handle.writeFile(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
    await handle.sync();
  } finally {
    await handle.close();
  }
}

export async function removeIfExists(filePath) {
  await rm(filePath, { force: true });
}

async function lockOwnerIsAlive(lockPath) {
  let owner;
  try {
    owner = JSON.parse(await readFile(lockPath, 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT') return false;
    return true;
  }
  if (!Number.isSafeInteger(owner.pid) || owner.pid <= 0) return true;
  try {
    process.kill(owner.pid, 0);
    return true;
  } catch (error) {
    if (error?.code === 'EPERM') return true;
    return false;
  }
}

export async function withFileLock(lockPath, task, { timeoutMs = 15000, pollMs = 50 } = {}) {
  await ensurePrivateDirectory(path.dirname(lockPath));
  const startedAt = Date.now();
  let handle;

  while (!handle) {
    try {
      handle = await open(lockPath, 'wx', 0o600);
      await handle.writeFile(`${JSON.stringify({ pid: process.pid, createdAt: new Date().toISOString() })}\n`, 'utf8');
      await handle.sync();
    } catch (error) {
      if (error?.code !== 'EEXIST') throw error;
      if (!(await lockOwnerIsAlive(lockPath))) {
        throw new DataDebugError('STALE_LOCK', `A stale plan lock requires manual removal: ${path.basename(lockPath)}`);
      }
      if (Date.now() - startedAt >= timeoutMs) {
        throw new DataDebugError('LOCK_TIMEOUT', `Timed out waiting for lock: ${path.basename(lockPath)}`);
      }
      await delay(pollMs);
    }
  }

  try {
    return await task();
  } finally {
    await handle.close().catch(() => {});
    await removeIfExists(lockPath);
  }
}

export function validateUuid(value, label = 'UUID') {
  if (typeof value !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)) {
    throw new DataDebugError('INVALID_ARGUMENT', `${label} is not a valid UUID`);
  }
  return value;
}
