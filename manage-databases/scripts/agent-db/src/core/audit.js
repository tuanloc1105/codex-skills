import { appendFile, chmod, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { ensurePrivateDirectory } from './fs.js';

export async function appendAudit(paths, event) {
  const month = new Date().toISOString().slice(0, 7);
  const filePath = path.join(paths.audit, `${month}.jsonl`);
  await ensurePrivateDirectory(paths.audit);
  const record = {
    timestamp: new Date().toISOString(),
    ...event,
  };
  await appendFile(filePath, `${JSON.stringify(record)}\n`, { encoding: 'utf8', mode: 0o600 });
  if (process.platform !== 'win32') await chmod(filePath, 0o600);
}

export async function readAudit(paths, { projectId, targetId, limit = 50 } = {}) {
  let files;
  try {
    files = (await readdir(paths.audit)).filter((name) => name.endsWith('.jsonl')).sort().reverse();
  } catch (error) {
    if (error?.code === 'ENOENT') return [];
    throw error;
  }

  const records = [];
  for (const file of files) {
    const lines = (await readFile(path.join(paths.audit, file), 'utf8')).split(/\r?\n/).filter(Boolean).reverse();
    for (const line of lines) {
      const record = JSON.parse(line);
      if (projectId && record.projectId !== projectId) continue;
      if (targetId && record.targetId !== targetId) continue;
      records.push(record);
      if (records.length >= limit) return records;
    }
  }
  return records;
}
