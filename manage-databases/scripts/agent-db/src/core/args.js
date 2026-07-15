import { AgentDbError, invariant } from './errors.js';

function addFlag(flags, key, value) {
  if (Object.hasOwn(flags, key)) {
    flags[key] = Array.isArray(flags[key]) ? [...flags[key], value] : [flags[key], value];
    return;
  }
  flags[key] = value;
}

export function parseArgs(argv) {
  const positionals = [];
  const flags = Object.create(null);

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--') {
      positionals.push(...argv.slice(index + 1));
      break;
    }
    if (!token.startsWith('--')) {
      positionals.push(token);
      continue;
    }

    const equalsIndex = token.indexOf('=');
    if (equalsIndex > 2) {
      addFlag(flags, token.slice(2, equalsIndex), token.slice(equalsIndex + 1));
      continue;
    }

    if (token.startsWith('--no-')) {
      addFlag(flags, token.slice(5), false);
      continue;
    }

    const key = token.slice(2);
    const next = argv[index + 1];
    if (next !== undefined && !next.startsWith('--')) {
      addFlag(flags, key, next);
      index += 1;
    } else {
      addFlag(flags, key, true);
    }
  }

  return { positionals, flags };
}

export function assertAllowedFlags(flags, allowed) {
  const unknown = Object.keys(flags).filter((key) => !allowed.includes(key));
  invariant(unknown.length === 0, 'INVALID_ARGUMENT', `Unknown option(s): ${unknown.join(', ')}`);
}

export function optionalString(flags, name) {
  const value = flags[name];
  if (value === undefined) return undefined;
  invariant(!Array.isArray(value) && typeof value === 'string', 'INVALID_ARGUMENT', `--${name} expects one value`);
  invariant(value.trim().length > 0, 'INVALID_ARGUMENT', `--${name} cannot be empty`);
  return value.trim();
}

export function requiredString(flags, name) {
  const value = optionalString(flags, name);
  invariant(value !== undefined, 'INVALID_ARGUMENT', `Missing required option --${name}`);
  return value;
}

export function booleanFlag(flags, name, defaultValue = false) {
  const value = flags[name];
  if (value === undefined) return defaultValue;
  if (typeof value === 'boolean') return value;
  invariant(!Array.isArray(value), 'INVALID_ARGUMENT', `--${name} expects one boolean value`);
  if (value === 'true' || value === '1') return true;
  if (value === 'false' || value === '0') return false;
  throw new AgentDbError('INVALID_ARGUMENT', `--${name} expects true or false`);
}

export function integerFlag(flags, name, defaultValue, { min, max } = {}) {
  const raw = optionalString(flags, name);
  if (raw === undefined) return defaultValue;
  const value = Number(raw);
  invariant(Number.isSafeInteger(value), 'INVALID_ARGUMENT', `--${name} expects an integer`);
  if (min !== undefined) invariant(value >= min, 'INVALID_ARGUMENT', `--${name} must be at least ${min}`);
  if (max !== undefined) invariant(value <= max, 'INVALID_ARGUMENT', `--${name} must be at most ${max}`);
  return value;
}

export function listFlag(flags, name) {
  const value = flags[name];
  if (value === undefined) return [];
  const values = Array.isArray(value) ? value : [value];
  invariant(values.every((item) => typeof item === 'string'), 'INVALID_ARGUMENT', `--${name} expects values`);
  return values.flatMap((item) => item.split(',')).map((item) => item.trim()).filter(Boolean);
}
