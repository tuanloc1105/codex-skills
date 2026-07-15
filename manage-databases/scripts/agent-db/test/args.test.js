import assert from 'node:assert/strict';
import test from 'node:test';
import { assertAllowedFlags, booleanFlag, listFlag, parseArgs, requiredString } from '../src/core/args.js';

test('parseArgs preserves positionals, repeated values, and negated booleans', () => {
  const parsed = parseArgs(['target', 'add', '--namespace', 'public', '--namespace=audit,reporting', '--no-tls']);
  assert.deepEqual(parsed.positionals, ['target', 'add']);
  assert.deepEqual(listFlag(parsed.flags, 'namespace'), ['public', 'audit', 'reporting']);
  assert.equal(booleanFlag(parsed.flags, 'tls', true), false);
});

test('parseArgs uses a null-prototype flag map', () => {
  const parsed = parseArgs(['--__proto__=polluted']);
  assert.equal(Object.getPrototypeOf(parsed.flags), null);
  assert.equal(parsed.flags.__proto__, 'polluted');
  assert.throws(() => assertAllowedFlags(parsed.flags, []), { code: 'INVALID_ARGUMENT' });
});

test('requiredString rejects missing and repeated values', () => {
  assert.throws(() => requiredString(parseArgs([]).flags, 'target'), { code: 'INVALID_ARGUMENT' });
  const flags = parseArgs(['--target', 'one', '--target', 'two']).flags;
  assert.throws(() => requiredString(flags, 'target'), { code: 'INVALID_ARGUMENT' });
});
