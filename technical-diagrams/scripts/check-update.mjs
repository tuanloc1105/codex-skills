import path from 'node:path';
import { fileURLToPath } from 'node:url';

const disabledReceipt = () => ({ status: 'silent', reason: 'disabled' });

export async function checkForUpdate() {
  return disabledReceipt();
}

export async function acknowledgeUpdate() {
  return disabledReceipt();
}

if (process.argv[1]
  && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.stdout.write(`${JSON.stringify(disabledReceipt())}\n`);
}
