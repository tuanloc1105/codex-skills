import {
  estimateValueBytes,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
  tabularResult,
} from '../core/values.js';
import { requireReadOperation, requireSqlMutation } from '../security/safety.js';
import { assertMutationApprovalActive, databaseError, elapsed, mutationDatabaseError, verifyIdentity, verifyPlannedIdentity } from './common.js';

async function module() {
  const imported = await import('mssql');
  return imported.default || imported;
}

function config(target, credential, timeoutMs = 15000) {
  return {
    user: credential.username,
    password: credential.secret,
    server: target.connection.host,
    port: target.connection.port,
    database: target.connection.database,
    connectionTimeout: timeoutMs,
    requestTimeout: timeoutMs,
    pool: { min: 0, max: 2, idleTimeoutMillis: 5000 },
    options: {
      appName: 'data-debug',
      encrypt: target.connection.encrypt ?? target.connection.tls ?? true,
      trustServerCertificate: target.connection.trustServerCertificate ?? false,
    },
  };
}

async function identity(pool, target, credential) {
  const result = await pool.request().query(`
    SELECT DB_NAME() AS database_name,
           SYSTEM_USER AS principal,
           CONVERT(nvarchar(256), SERVERPROPERTY('ServerName')) AS server_identity,
           CONVERT(nvarchar(256), SERVERPROPERTY('ProductVersion')) AS version
  `);
  const row = result.recordset[0];
  return verifyIdentity(target, {
    database: row.database_name,
    principal: row.principal,
    serverIdentity: row.server_identity,
    version: row.version,
    credentialMode: credential.mode,
  });
}

export async function streamSqlServerQuery(pool, sql, maxRows, timeoutMs, maxBytes = MAX_OUTPUT_BYTES) {
  const request = pool.request({ requestTimeout: timeoutMs });
  request.stream = true;
  const rows = [];
  let columns = [];
  let bytes = 0;
  let truncationReason = null;

  await new Promise((resolve, reject) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      resolve();
    };
    const fail = (error) => {
      if (settled) return;
      if (truncationReason && error.code === 'ECANCEL') finish();
      else {
        settled = true;
        reject(error);
      }
    };
    const stop = (reason) => {
      if (truncationReason) return;
      truncationReason = reason;
      try {
        request.cancel();
      } catch (error) {
        fail(error);
      }
    };
    request.on('recordset', (metadata) => {
      if (columns.length === 0) {
        columns = Object.entries(metadata).map(([name, detail]) => ({ name, type: detail.type?.name || String(detail.type || '') }));
      }
    });
    request.on('row', (row) => {
      if (truncationReason) return;
      if (rows.length >= maxRows) return stop('max-rows');
      const remainingBytes = maxBytes - bytes;
      if (estimateValueBytes(row, new WeakSet(), remainingBytes + 1) > remainingBytes) {
        return stop('max-output-bytes');
      }
      const normalizedRow = normalizeDatabaseValue(row);
      const rowBytes = Buffer.byteLength(JSON.stringify(normalizedRow));
      if (rowBytes > remainingBytes) return stop('max-output-bytes');
      rows.push(normalizedRow);
      bytes += rowBytes;
    });
    request.on('error', fail);
    request.on('done', finish);
    request.query(sql).catch(fail);
  });

  const names = columns.map((column) => column.name);
  const result = tabularResult(columns, rows.map((row) => names.map((name) => row[name])), maxRows);
  if (truncationReason) {
    result.truncated = true;
    result.truncationReason = truncationReason;
  }
  return result;
}

export async function streamSqlServerMutation(pool, sql, timeoutMs) {
  const request = pool.request({ requestTimeout: timeoutMs });
  request.stream = true;
  const rowsAffected = [];
  let rowsAffectedTruncated = false;
  let returnedRowsDiscarded = 0;
  await new Promise((resolve, reject) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      resolve();
    };
    const fail = (error) => {
      if (settled) return;
      settled = true;
      reject(error);
    };
    request.on('row', () => {
      returnedRowsDiscarded = Math.min(Number.MAX_SAFE_INTEGER, returnedRowsDiscarded + 1);
    });
    request.on('rowsaffected', (count) => {
      if (rowsAffected.length < 1000) rowsAffected.push(count);
      else rowsAffectedTruncated = true;
    });
    request.on('error', fail);
    request.on('done', finish);
    request.query(sql).catch(fail);
  });
  return { rowsAffected, rowsAffectedTruncated, returnedRowsDiscarded };
}

export async function createSqlServerAdapter(target, credential) {
  const sql = await module();

  return {
    async test({ timeoutMs = 15000 } = {}) {
      const pool = new sql.ConnectionPool(config(target, credential, timeoutMs));
      try {
        await pool.connect();
        return { identity: await identity(pool, target, credential) };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await pool.close().catch(() => {});
      }
    },

    async inspect({ timeoutMs }) {
      const startedAt = Date.now();
      const pool = new sql.ConnectionPool(config(target, credential, timeoutMs));
      try {
        await pool.connect();
        const verifiedIdentity = await identity(pool, target, credential);
        const schema = await streamSqlServerQuery(pool, `
          SELECT TOP (10001) s.name AS schema_name, t.name AS table_name, c.name AS column_name,
                 c.column_id, ty.name AS data_type, c.max_length, c.precision, c.scale,
                 c.is_nullable
            FROM sys.tables t
            JOIN sys.schemas s ON s.schema_id = t.schema_id
            JOIN sys.columns c ON c.object_id = t.object_id
            JOIN sys.types ty ON ty.user_type_id = c.user_type_id
           ORDER BY s.name, t.name, c.column_id
        `, 10000, timeoutMs);
        return {
          identity: verifiedIdentity,
          schema,
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await pool.close().catch(() => {});
      }
    },

    async executeRead(sqlText, options) {
      requireReadOperation('sqlserver', sqlText, target, options);
      const { maxRows, timeoutMs } = options;
      const startedAt = Date.now();
      const pool = new sql.ConnectionPool(config(target, credential, timeoutMs));
      try {
        await pool.connect();
        const verifiedIdentity = await identity(pool, target, credential);
        return {
          identity: verifiedIdentity,
          result: await streamSqlServerQuery(pool, sqlText, maxRows, timeoutMs),
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await pool.close().catch(() => {});
      }
    },

    async executeMutation(sqlText, { timeoutMs, expectedIdentity, approvalExpiresAt }) {
      requireSqlMutation(sqlText, target.engine);
      const startedAt = Date.now();
      const pool = new sql.ConnectionPool(config(target, credential, timeoutMs));
      let operationSent = false;
      try {
        await pool.connect();
        const verifiedIdentity = await identity(pool, target, credential);
        verifyPlannedIdentity(expectedIdentity, verifiedIdentity);
        assertMutationApprovalActive(approvalExpiresAt);
        operationSent = true;
        const result = await streamSqlServerMutation(pool, sqlText, timeoutMs);
        return {
          identity: verifiedIdentity,
          result,
          elapsedMs: elapsed(startedAt),
          transactional: false,
        };
      } catch (error) {
        throw mutationDatabaseError(error, credential, operationSent);
      } finally {
        await pool.close().catch(() => {});
      }
    },
  };
}
