import { open } from 'node:fs/promises';
import { AgentDbError, invariant } from './errors.js';
import { booleanFlag, optionalString } from './args.js';

const MAX_INPUT_BYTES = 1024 * 1024;

async function readStdin() {
  const chunks = [];
  let size = 0;
  for await (const chunk of process.stdin) {
    const buffer = Buffer.from(chunk);
    size += buffer.length;
    invariant(size <= MAX_INPUT_BYTES, 'INPUT_TOO_LARGE', `Input exceeds ${MAX_INPUT_BYTES} bytes`);
    chunks.push(buffer);
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function readBoundedFile(filePath) {
  const handle = await open(filePath, 'r');
  const buffer = Buffer.allocUnsafe(MAX_INPUT_BYTES + 1);
  let offset = 0;
  try {
    while (offset < buffer.length) {
      const { bytesRead } = await handle.read(buffer, offset, buffer.length - offset, offset);
      if (bytesRead === 0) break;
      offset += bytesRead;
    }
  } finally {
    await handle.close();
  }
  invariant(offset <= MAX_INPUT_BYTES, 'INPUT_TOO_LARGE', `Input exceeds ${MAX_INPUT_BYTES} bytes`);
  return buffer.subarray(0, offset).toString('utf8');
}

export async function operationInput(flags) {
  const file = optionalString(flags, 'file');
  const text = optionalString(flags, 'text');
  const stdin = booleanFlag(flags, 'stdin');
  const selected = [file !== undefined, text !== undefined, stdin].filter(Boolean).length;
  invariant(selected === 1, 'INVALID_ARGUMENT', 'Provide exactly one of --file, --text, or --stdin');

  let value;
  if (file !== undefined) {
    value = await readBoundedFile(file);
  } else if (text !== undefined) {
    value = text;
  } else {
    value = await readStdin();
  }

  invariant(Buffer.byteLength(value, 'utf8') <= MAX_INPUT_BYTES, 'INPUT_TOO_LARGE', `Input exceeds ${MAX_INPUT_BYTES} bytes`);
  if (!value.trim()) throw new AgentDbError('INVALID_ARGUMENT', 'Operation input is empty');
  return value;
}
