import { AgentDbError, invariant } from '../core/errors.js';

export function requireTty({ input = process.stdin, output = process.stderr } = {}) {
  invariant(input.isTTY && output.isTTY, 'LOCAL_TTY_REQUIRED', 'This command must be run directly in a local terminal');
}

export async function readHidden(prompt, { input = process.stdin, output = process.stderr, maxLength = 65536 } = {}) {
  requireTty({ input, output });
  output.write(prompt);
  input.setRawMode(true);
  input.resume();
  input.setEncoding('utf8');

  return new Promise((resolve, reject) => {
    let value = '';
    const cleanup = () => {
      input.off('data', onData);
      input.setRawMode(false);
      input.pause();
      output.write('\n');
    };
    const onData = (chunk) => {
      for (const character of chunk) {
        if (character === '\u0003') {
          cleanup();
          reject(new AgentDbError('USER_CANCELLED', 'Input cancelled by user'));
          return;
        }
        if (character === '\r' || character === '\n') {
          cleanup();
          resolve(value);
          return;
        }
        if (character === '\u007f' || character === '\b') {
          value = value.slice(0, -1);
          continue;
        }
        value += character;
        if (value.length > maxLength) {
          cleanup();
          reject(new AgentDbError('INPUT_TOO_LARGE', `Interactive input exceeds ${maxLength} characters`));
          return;
        }
      }
    };
    input.on('data', onData);
  });
}

export async function readVisibleLine(prompt, { input = process.stdin, output = process.stderr, maxLength = 4096 } = {}) {
  requireTty({ input, output });
  output.write(prompt);
  input.resume();
  input.setEncoding('utf8');
  return new Promise((resolve, reject) => {
    let value = '';
    const cleanup = () => {
      input.off('data', onData);
      input.pause();
    };
    const onData = (chunk) => {
      if (chunk.includes('\u0003')) {
        cleanup();
        reject(new AgentDbError('USER_CANCELLED', 'Input cancelled by user'));
        return;
      }
      value += chunk;
      const newline = value.search(/[\r\n]/);
      if (newline >= 0) {
        cleanup();
        resolve(value.slice(0, newline).trim());
        return;
      }
      if (value.length > maxLength) {
        cleanup();
        reject(new AgentDbError('INPUT_TOO_LARGE', `Interactive input exceeds ${maxLength} characters`));
        return;
      }
    };
    input.on('data', onData);
  });
}
