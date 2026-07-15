import assert from 'node:assert/strict';
import test from 'node:test';
import { emitJson, success } from '../src/core/output.js';
import { MAX_OUTPUT_BYTES } from '../src/core/values.js';

test('serialized stdout has a hard byte cap including envelope and escaping', () => {
  let output = '';
  const stream = { write(value) { output += value; } };
  emitJson(success('read', { value: 'x'.repeat(MAX_OUTPUT_BYTES) }), stream);
  assert.ok(Buffer.byteLength(output) <= MAX_OUTPUT_BYTES);
  const parsed = JSON.parse(output);
  assert.equal(parsed.ok, false);
  assert.equal(parsed.error.code, 'OUTPUT_TOO_LARGE');
});
