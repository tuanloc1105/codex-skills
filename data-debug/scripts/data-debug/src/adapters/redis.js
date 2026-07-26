import { DataDebugError, invariant } from '../core/errors.js';
import {
  boundedNormalizedValues,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
} from '../core/values.js';
import { requireRedisMutation, requireRedisRead } from '../security/safety.js';
import {
  assertMutationApprovalActive,
  databaseError,
  elapsed,
  mutationDatabaseError,
  verifyIdentity,
  verifyPlannedIdentity,
} from './common.js';

const MAX_VALUE_PREVIEW_BYTES = 64 * 1024;

async function module() {
  return import('@redis/client');
}

function endpointIdentity(target) {
  const host = target.connection.host.includes(':')
    ? `[${target.connection.host}]`
    : target.connection.host;
  return `${host}:${target.connection.port}`;
}

export function redisClientOptions(target, credential, timeoutMs = 15000) {
  const tls = Boolean(target.connection.tls);
  return {
    username: credential.username,
    password: credential.secret,
    database: Number(target.connection.database),
    RESP: 2,
    disableOfflineQueue: true,
    disableClientInfo: true,
    maintNotifications: 'disabled',
    commandOptions: { timeout: timeoutMs },
    socket: {
      host: target.connection.host,
      port: target.connection.port,
      tls,
      connectTimeout: timeoutMs,
      socketTimeout: timeoutMs,
      reconnectStrategy: false,
      ...(tls ? {
        servername: target.connection.host,
        rejectUnauthorized: !target.connection.trustServerCertificate,
      } : {}),
    },
  };
}

function redisText(value) {
  if (Buffer.isBuffer(value)) return value.toString('utf8');
  return String(value);
}

export function parseRedisInfo(value) {
  const result = {};
  for (const line of redisText(value).split(/\r?\n/)) {
    if (!line || line.startsWith('#')) continue;
    const separator = line.indexOf(':');
    if (separator <= 0) continue;
    result[line.slice(0, separator)] = line.slice(separator + 1);
  }
  return result;
}

export function parseRedisClientInfo(value) {
  const result = {};
  for (const field of redisText(value).trim().split(/\s+/)) {
    const separator = field.indexOf('=');
    if (separator <= 0) continue;
    result[field.slice(0, separator)] = field.slice(separator + 1);
  }
  return result;
}

function parseKeyspaceStats(value) {
  if (!value) return { keys: 0, expires: 0, avgTtl: 0 };
  const fields = Object.fromEntries(value.split(',').map((field) => {
    const separator = field.indexOf('=');
    return separator > 0 ? [field.slice(0, separator), field.slice(separator + 1)] : [field, '0'];
  }));
  return {
    keys: Number(fields.keys || 0),
    expires: Number(fields.expires || 0),
    avgTtl: Number(fields.avg_ttl || 0),
  };
}

function remainingDeadlineMs(deadline) {
  const remaining = deadline - Date.now();
  invariant(remaining > 0, 'DATABASE_TIMEOUT', 'Redis operation exceeded its total time budget');
  return Math.max(1, remaining);
}

function withDeadline(client, deadline, task) {
  const remaining = remainingDeadlineMs(deadline);
  return new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try { client.destroy(); } catch {}
      reject(new DataDebugError('DATABASE_TIMEOUT', 'Redis operation exceeded its total time budget'));
    }, remaining);
    Promise.resolve()
      .then(task)
      .then((value) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(value);
      }, (error) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        reject(error);
      });
  });
}

function send(client, deadline, argv) {
  return withDeadline(client, deadline, () => client.sendCommand(argv));
}

function destroy(client) {
  try {
    if (client?.isOpen) client.destroy();
  } catch {}
}

function redisDatabaseError(error, credential) {
  if (/timeout/i.test(error?.name || '') || error?.code === 'ETIMEDOUT') {
    return databaseError(error, credential, 'DATABASE_TIMEOUT');
  }
  return databaseError(error, credential);
}

async function identity(client, target, credential, deadline) {
  const clientInfo = parseRedisClientInfo(await send(client, deadline, ['CLIENT', 'INFO']));
  const principal = redisText(await send(client, deadline, ['ACL', 'WHOAMI']));
  const server = parseRedisInfo(await send(client, deadline, ['INFO', 'server']));
  invariant(clientInfo.db !== undefined, 'TARGET_IDENTITY_MISMATCH', 'Redis CLIENT INFO did not report the selected database');
  invariant(clientInfo.user !== undefined, 'TARGET_IDENTITY_MISMATCH', 'Redis CLIENT INFO did not report the authenticated user');
  invariant(clientInfo.user === principal, 'TARGET_IDENTITY_MISMATCH', 'Redis authenticated principal is inconsistent');
  invariant(principal === credential.username, 'TARGET_IDENTITY_MISMATCH', 'Redis authenticated principal does not match the credential username');
  invariant(server.redis_mode === 'standalone', 'UNSUPPORTED_OPERATION', `Redis topology is not supported in this version: ${server.redis_mode || 'unknown'}`);
  invariant(server.redis_version, 'TARGET_IDENTITY_MISMATCH', 'Redis INFO server did not report a version');
  invariant(server.run_id, 'TARGET_IDENTITY_MISMATCH', 'Redis INFO server did not report an instance run id');
  return verifyIdentity(target, {
    database: clientInfo.db,
    databaseAssurance: 'client-info',
    principal,
    serverIdentity: endpointIdentity(target),
    instanceRunId: server.run_id,
    version: server.redis_version,
    topology: server.redis_mode,
    identityAssurance: target.connection.tls
      ? 'tls-authenticated-endpoint'
      : 'configured-endpoint',
    credentialMode: credential.mode,
  });
}

function boundedArray(values, maxRows) {
  const bounded = boundedNormalizedValues(values, maxRows);
  return {
    values: bounded.values,
    rowCount: bounded.values.length,
    truncated: bounded.truncated,
    truncationReason: bounded.truncationReason,
    outputBytes: bounded.bytes,
  };
}

function pairRows(values, firstName, secondName) {
  invariant(Array.isArray(values) && values.length % 2 === 0, 'DATABASE_ERROR', 'Redis returned an invalid paired response');
  const rows = [];
  for (let index = 0; index < values.length; index += 2) {
    rows.push({ [firstName]: values[index], [secondName]: values[index + 1] });
  }
  return rows;
}

function completeScanPage(operation, reply, maxRows) {
  invariant(Array.isArray(reply) && reply.length === 2 && Array.isArray(reply[1]), 'DATABASE_ERROR', 'Redis returned an invalid SCAN response');
  const rawValues = reply[1];
  const paired = operation.resultKind === 'hscan' || operation.resultKind === 'zscan';
  invariant((paired ? rawValues.length / 2 : rawValues.length) <= maxRows, 'OUTPUT_TOO_LARGE', 'Redis SCAN page exceeds max-rows; retry with a smaller COUNT');
  const values = operation.resultKind === 'hscan'
    ? pairRows(rawValues, 'field', 'value')
    : operation.resultKind === 'zscan'
      ? pairRows(rawValues, 'member', 'score')
      : rawValues;
  if (operation.scope === 'keyspace') {
    for (const key of values) {
      invariant(redisText(key).startsWith(operation.keyPrefix), 'NAMESPACE_NOT_ALLOWED', 'Redis SCAN returned a key outside the target prefix');
    }
  }
  const bounded = boundedNormalizedValues(values, maxRows);
  invariant(!bounded.truncated, 'OUTPUT_TOO_LARGE', 'Redis SCAN page exceeds the output budget; retry with a smaller COUNT');
  return {
    nextCursor: redisText(reply[0]),
    values: bounded.values,
    rowCount: bounded.values.length,
    truncated: false,
    truncationReason: null,
    outputBytes: bounded.bytes,
  };
}

function sanitizeSlowlog(entries, maxRows) {
  invariant(Array.isArray(entries), 'DATABASE_ERROR', 'Redis returned an invalid SLOWLOG response');
  const sanitized = entries.map((entry) => {
    invariant(Array.isArray(entry) && entry.length >= 4 && Array.isArray(entry[3]), 'DATABASE_ERROR', 'Redis returned an invalid SLOWLOG entry');
    return {
      id: entry[0],
      timestamp: entry[1],
      durationMicroseconds: entry[2],
      command: entry[3][0] === undefined ? null : redisText(entry[3][0]),
      argumentCount: Math.max(0, entry[3].length - 1),
      commandArgumentsOmitted: true,
      clientMetadataOmitted: true,
    };
  });
  const bounded = boundedNormalizedValues(sanitized, maxRows);
  return {
    entries: bounded.values,
    rowCount: bounded.values.length,
    truncated: bounded.truncated,
    truncationReason: bounded.truncationReason,
    outputBytes: bounded.bytes,
  };
}

export function formatRedisReply(operation, reply, maxRows) {
  if (['scan', 'hscan', 'zscan'].includes(operation.resultKind)) {
    return completeScanPage(operation, reply, maxRows);
  }
  if (operation.resultKind === 'slowlog') return sanitizeSlowlog(reply, maxRows);
  if (operation.resultKind === 'info') {
    const value = normalizeDatabaseValue(parseRedisInfo(reply));
    const outputBytes = Buffer.byteLength(JSON.stringify(value));
    invariant(outputBytes <= MAX_OUTPUT_BYTES, 'OUTPUT_TOO_LARGE', 'Redis INFO response exceeds the output budget');
    return { value, rowCount: 1, truncated: false, truncationReason: null, outputBytes };
  }
  if (operation.resultKind === 'zrange-with-scores') {
    return boundedArray(pairRows(reply, 'member', 'score'), maxRows);
  }
  if (operation.resultKind === 'array') {
    invariant(Array.isArray(reply), 'DATABASE_ERROR', 'Redis returned an invalid array response');
    return boundedArray(reply, maxRows);
  }
  const bounded = boundedNormalizedValues([reply], 1);
  return {
    value: bounded.values[0] ?? null,
    rowCount: reply === null ? 0 : 1,
    truncated: bounded.truncated,
    truncationReason: bounded.truncationReason,
    outputBytes: bounded.bytes,
  };
}

async function executeBoundedGet(client, deadline, key) {
  const exists = Number(await send(client, deadline, ['EXISTS', key]));
  if (exists === 0) {
    return { value: null, byteLength: 0, rowCount: 0, truncated: false, truncationReason: null, outputBytes: 4 };
  }
  const byteLength = Number(await send(client, deadline, ['STRLEN', key]));
  const preview = await send(client, deadline, ['GETRANGE', key, '0', String(MAX_VALUE_PREVIEW_BYTES - 1)]);
  const bounded = boundedNormalizedValues([preview], 1);
  return {
    value: bounded.values[0] ?? null,
    byteLength,
    rowCount: 1,
    truncated: byteLength > MAX_VALUE_PREVIEW_BYTES || bounded.truncated,
    truncationReason: byteLength > MAX_VALUE_PREVIEW_BYTES ? 'max-scalar-bytes' : bounded.truncationReason,
    outputBytes: bounded.bytes,
  };
}

export async function createRedisAdapter(target, credential, redisModule = undefined) {
  const { createClient, RESP_TYPES } = redisModule || await module();
  const create = (timeoutMs) => {
    const client = createClient(redisClientOptions(target, credential, timeoutMs)).withTypeMapping({
      [RESP_TYPES.BLOB_STRING]: Buffer,
    });
    client.on('error', () => {});
    return client;
  };

  async function connect(client, deadline) {
    await withDeadline(client, deadline, () => client.connect());
  }

  return {
    async test({ timeoutMs = 15000 } = {}) {
      const deadline = Date.now() + timeoutMs;
      const client = create(timeoutMs);
      try {
        await connect(client, deadline);
        return { identity: await identity(client, target, credential, deadline) };
      } catch (error) {
        throw redisDatabaseError(error, credential);
      } finally {
        destroy(client);
      }
    },

    async inspect({ timeoutMs }) {
      const startedAt = Date.now();
      const deadline = startedAt + timeoutMs;
      const client = create(timeoutMs);
      try {
        await connect(client, deadline);
        const verifiedIdentity = await identity(client, target, credential, deadline);
        const keyspace = parseRedisInfo(await send(client, deadline, ['INFO', 'keyspace']));
        const replication = parseRedisInfo(await send(client, deadline, ['INFO', 'replication']));
        const database = Number(verifiedIdentity.database);
        return {
          identity: verifiedIdentity,
          schema: [{
            kind: 'redis-keyspace',
            database,
            keyPrefix: target.keyPrefix,
            keyspace: parseKeyspaceStats(keyspace[`db${database}`]),
            keyspaceScope: 'database-wide',
            capabilities: {
              version: verifiedIdentity.version,
              topology: verifiedIdentity.topology,
              role: replication.role || 'unknown',
            },
          }],
          schemaTruncated: false,
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        throw redisDatabaseError(error, credential);
      } finally {
        destroy(client);
      }
    },

    async executeRead(rawInput, { maxRows, timeoutMs }) {
      const startedAt = Date.now();
      const deadline = startedAt + timeoutMs;
      const client = create(timeoutMs);
      try {
        await connect(client, deadline);
        const verifiedIdentity = await identity(client, target, credential, deadline);
        const operation = requireRedisRead(rawInput, target, { maxRows });
        const scopedOperation = { ...operation, keyPrefix: target.keyPrefix };
        const result = operation.resultKind === 'get'
          ? await executeBoundedGet(client, deadline, operation.argv[1])
          : formatRedisReply(scopedOperation, await send(client, deadline, operation.argv), maxRows);
        return { identity: verifiedIdentity, result, elapsedMs: elapsed(startedAt) };
      } catch (error) {
        throw redisDatabaseError(error, credential);
      } finally {
        destroy(client);
      }
    },

    async executeMutation(rawInput, { timeoutMs, expectedIdentity, approvalExpiresAt }) {
      const startedAt = Date.now();
      const deadline = startedAt + timeoutMs;
      const client = create(timeoutMs);
      let operationSent = false;
      try {
        await connect(client, deadline);
        const verifiedIdentity = await identity(client, target, credential, deadline);
        verifyPlannedIdentity(expectedIdentity, verifiedIdentity);
        const operation = requireRedisMutation(rawInput, target);
        assertMutationApprovalActive(approvalExpiresAt);
        operationSent = true;
        const reply = await send(client, deadline, operation.argv);
        const bounded = boundedNormalizedValues([reply], 1);
        return {
          identity: verifiedIdentity,
          result: bounded.values[0] ?? null,
          resultTruncated: bounded.truncated,
          elapsedMs: elapsed(startedAt),
          transactional: false,
        };
      } catch (error) {
        if (operationSent && error instanceof DataDebugError && error.code !== 'MUTATION_OUTCOME_UNKNOWN') {
          throw mutationDatabaseError(new Error(error.message), credential, true);
        }
        throw mutationDatabaseError(error, credential, operationSent);
      } finally {
        destroy(client);
      }
    },
  };
}
