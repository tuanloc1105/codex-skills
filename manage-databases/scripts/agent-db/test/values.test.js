import assert from 'node:assert/strict';
import test from 'node:test';
import {
  boundedNormalizedValues,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
  tabularResult,
} from '../src/core/values.js';

test('large database scalars are summarized instead of base64/string-expanded', () => {
  const binary = Buffer.alloc(128 * 1024, 7);
  const text = 'x'.repeat(128 * 1024);
  const normalized = normalizeDatabaseValue({ binary, text });
  assert.equal(normalized.binary.$binarySummary.byteLength, binary.length);
  assert.equal(normalized.text.$stringSummary.byteLength, text.length);
  assert.equal(normalized.binary.$binarySummary.sha256.length, 64);
});

test('tabular output stops at a global byte budget', () => {
  const rows = Array.from({ length: 1000 }, (_, index) => [index, 'x'.repeat(32 * 1024)]);
  const result = tabularResult([{ name: 'id' }, { name: 'payload' }], rows, 1000);
  assert.equal(result.truncated, true);
  assert.equal(result.truncationReason, 'max-output-bytes');
  assert.ok(result.outputBytes <= MAX_OUTPUT_BYTES);
  assert.ok(result.rowCount < rows.length);
});

test('one oversized composite value becomes a small summary', () => {
  const value = Object.fromEntries(
    Array.from({ length: 200 }, (_, index) => [`field_${index}`, 'x'.repeat(64 * 1024)]),
  );
  const result = boundedNormalizedValues([value], 1);
  assert.equal(result.truncated, true);
  assert.equal(result.truncationReason, 'max-output-bytes');
  assert.equal(result.values[0].$valueSummary.truncated, true);
  assert.ok(result.bytes < 1024);
});

test('bounded arrays count JSON delimiters and separators', () => {
  const values = Array.from({ length: 10000 }, () => ({ x: 'x'.repeat(830) }));
  const result = boundedNormalizedValues(values, values.length);
  const serializedBytes = Buffer.byteLength(JSON.stringify(result.values));
  assert.ok(serializedBytes <= MAX_OUTPUT_BYTES);
  assert.equal(result.bytes, serializedBytes);
});
