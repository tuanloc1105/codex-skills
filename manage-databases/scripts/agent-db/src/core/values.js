import { createHash } from 'node:crypto';

export const MAX_OUTPUT_BYTES = 8 * 1024 * 1024;
const MAX_SCALAR_BYTES = 64 * 1024;
const STRING_PREVIEW_CHARACTERS = 8192;

function normalizeBson(value) {
  if (!value?._bsontype) return undefined;
  const type = String(value._bsontype);
  if (type === 'ObjectId') return { $oid: value.toHexString() };
  if (type === 'Decimal128') return { $numberDecimal: value.toString() };
  if (type === 'Long') return { $numberLong: value.toString() };
  if (type === 'Binary') return { $binary: Buffer.from(value.buffer).toString('base64') };
  return { $bsonType: type, value: value.toString() };
}

function binarySummary(buffer) {
  if (buffer.length <= MAX_SCALAR_BYTES) return { $binary: buffer.toString('base64') };
  return {
    $binarySummary: {
      byteLength: buffer.length,
      sha256: createHash('sha256').update(buffer).digest('hex'),
      truncated: true,
    },
  };
}

export function normalizeValue(value, seen = new WeakSet()) {
  if (value === null || value === undefined) return value ?? null;
  if (typeof value === 'bigint') return value.toString();
  if (typeof value === 'number' && !Number.isFinite(value)) return String(value);
  if (typeof value !== 'object') return value;
  if (value instanceof Date) return value.toISOString();
  if (Buffer.isBuffer(value)) return { $binary: value.toString('base64') };
  if (ArrayBuffer.isView(value)) {
    return { $binary: Buffer.from(value.buffer, value.byteOffset, value.byteLength).toString('base64') };
  }

  const bsonValue = normalizeBson(value);
  if (bsonValue) return bsonValue;
  if (seen.has(value)) return '[Circular]';
  seen.add(value);

  if (Array.isArray(value)) {
    const result = value.map((item) => normalizeValue(item, seen));
    seen.delete(value);
    return result;
  }

  const result = {};
  for (const [key, item] of Object.entries(value)) {
    result[key] = normalizeValue(item, seen);
  }
  seen.delete(value);
  return result;
}

export function normalizeDatabaseValue(value, seen = new WeakSet()) {
  if (value === null || value === undefined) return value ?? null;
  if (typeof value === 'string') {
    const byteLength = Buffer.byteLength(value);
    if (byteLength <= MAX_SCALAR_BYTES) return value;
    return {
      $stringSummary: {
        byteLength,
        preview: value.slice(0, STRING_PREVIEW_CHARACTERS),
        truncated: true,
      },
    };
  }
  if (typeof value === 'bigint') return value.toString();
  if (typeof value === 'number' && !Number.isFinite(value)) return String(value);
  if (typeof value !== 'object') return value;
  if (value instanceof Date) return value.toISOString();
  if (Buffer.isBuffer(value)) return binarySummary(value);
  if (ArrayBuffer.isView(value)) {
    return binarySummary(Buffer.from(value.buffer, value.byteOffset, value.byteLength));
  }
  if (value?._bsontype === 'Binary') return binarySummary(Buffer.from(value.buffer));

  const bsonValue = normalizeBson(value);
  if (bsonValue) return bsonValue;
  if (seen.has(value)) return '[Circular]';
  seen.add(value);
  const result = Array.isArray(value)
    ? value.map((item) => normalizeDatabaseValue(item, seen))
    : Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeDatabaseValue(item, seen)]));
  seen.delete(value);
  return result;
}

export function estimateValueBytes(value, seen = new WeakSet(), limit = MAX_OUTPUT_BYTES + 1) {
  if (value === null || value === undefined) return 4;
  if (typeof value === 'string') return Math.min(limit, Buffer.byteLength(value));
  if (typeof value === 'bigint' || typeof value === 'number' || typeof value === 'boolean') return 16;
  if (typeof value !== 'object') return 32;
  if (Buffer.isBuffer(value)) return Math.min(limit, value.length);
  if (ArrayBuffer.isView(value)) return Math.min(limit, value.byteLength);
  if (value?._bsontype === 'Binary') return Math.min(limit, value.buffer?.length || 0);
  if (seen.has(value)) return 16;
  seen.add(value);
  let total = 2;
  for (const [key, child] of Object.entries(value)) {
    total += Buffer.byteLength(key) + estimateValueBytes(child, seen, Math.max(0, limit - total));
    if (total >= limit) break;
  }
  seen.delete(value);
  return Math.min(limit, total);
}

export function boundedNormalizedValues(values, maxRows, maxBytes = MAX_OUTPUT_BYTES) {
  const normalized = [];
  let bytes = 2;
  let truncatedByBytes = false;
  for (const value of values.slice(0, maxRows)) {
    const item = normalizeDatabaseValue(value);
    const itemBytes = Buffer.byteLength(JSON.stringify(item));
    const separatorBytes = normalized.length > 0 ? 1 : 0;
    if (bytes + separatorBytes + itemBytes > maxBytes) {
      truncatedByBytes = true;
      if (normalized.length === 0) {
        const summary = { $valueSummary: { estimatedJsonBytes: itemBytes, truncated: true } };
        normalized.push(summary);
        bytes = 2 + Buffer.byteLength(JSON.stringify(summary));
      }
      break;
    }
    normalized.push(item);
    bytes += separatorBytes + itemBytes;
    if (bytes >= maxBytes) {
      truncatedByBytes = values.length > normalized.length;
      break;
    }
  }
  const truncatedByRows = values.length > normalized.length && !truncatedByBytes;
  return {
    values: normalized,
    bytes,
    truncated: truncatedByBytes || truncatedByRows,
    truncationReason: truncatedByBytes ? 'max-output-bytes' : truncatedByRows ? 'max-rows' : null,
  };
}

export function tabularResult(columns, rows, maxRows) {
  const bounded = boundedNormalizedValues(rows, maxRows);
  return {
    columns: columns.map((column) => normalizeDatabaseValue(column)),
    rows: bounded.values,
    rowCount: bounded.values.length,
    truncated: bounded.truncated,
    truncationReason: bounded.truncationReason,
    outputBytes: bounded.bytes,
  };
}
