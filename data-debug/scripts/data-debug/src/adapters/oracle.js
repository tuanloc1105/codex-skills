import {
  estimateValueBytes,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
  tabularResult,
} from '../core/values.js';
import { invariant } from '../core/errors.js';
import { requireReadOperation, requireSqlMutation } from '../security/safety.js';
import { assertMutationApprovalActive, databaseError, elapsed, mutationDatabaseError, verifyIdentity, verifyPlannedIdentity } from './common.js';

async function module() {
  const imported = await import('oracledb');
  return imported.default || imported;
}

function connectString(target) {
  const service = target.connection.service || target.connection.database;
  const protocol = target.connection.tls ? 'tcps://' : '';
  const tlsOptions = target.connection.tls ? '?ssl_server_dn_match=on' : '';
  return `${protocol}${target.connection.host}:${target.connection.port}/${service}${tlsOptions}`;
}

async function identity(connection, target, credential, oracledb) {
  const result = await connection.execute(
    `SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS DATABASE_NAME,
            SYS_CONTEXT('USERENV', 'CURRENT_USER') AS PRINCIPAL,
            SYS_CONTEXT('USERENV', 'SERVER_HOST') AS SERVER_IDENTITY
       FROM DUAL`,
    [],
    { outFormat: oracledb.OUT_FORMAT_OBJECT },
  );
  const row = result.rows[0];
  return verifyIdentity(target, {
    database: row.DATABASE_NAME,
    principal: row.PRINCIPAL,
    serverIdentity: row.SERVER_IDENTITY,
    version: connection.oracleServerVersionString,
    credentialMode: credential.mode,
  });
}

function oracleLobType(value, oracledb) {
  if (!value || typeof value.close !== 'function' || value.type === undefined) return null;
  if (value?.type === oracledb.DB_TYPE_BLOB) return 'BLOB';
  if (value?.type === oracledb.DB_TYPE_CLOB) return 'CLOB';
  if (value?.type === oracledb.DB_TYPE_NCLOB) return 'NCLOB';
  if (value?.type === oracledb.DB_TYPE_BFILE) return 'BFILE';
  return null;
}

async function sanitizeOracleValue(value, oracledb, seen = new WeakSet()) {
  const lobType = oracleLobType(value, oracledb);
  if (lobType) {
    const summary = {
      $oracleLob: {
        type: lobType,
        length: Number.isSafeInteger(value.length) ? value.length : null,
        contentOmitted: true,
      },
    };
    await value.close().catch(() => {});
    return summary;
  }
  if (!value || typeof value !== 'object' || value instanceof Date || Buffer.isBuffer(value) || ArrayBuffer.isView(value)) {
    return value;
  }
  if (seen.has(value)) return '[Circular]';
  seen.add(value);
  const normalized = Array.isArray(value) ? [] : {};
  for (const [name, item] of Object.entries(value)) {
    normalized[name] = await sanitizeOracleValue(item, oracledb, seen);
  }
  seen.delete(value);
  return normalized;
}

async function sanitizeOracleRow(row, oracledb) {
  return sanitizeOracleValue(row, oracledb);
}

export async function collectOracleResultSet(resultSet, maxRows, oracledb, maxBytes = MAX_OUTPUT_BYTES) {
  const rows = [];
  let bytes = 0;
  let truncationReason = null;
  try {
    while (true) {
      const row = await resultSet.getRow();
      if (!row) break;
      const safeRow = await sanitizeOracleRow(row, oracledb);
      if (rows.length >= maxRows) {
        truncationReason = 'max-rows';
        break;
      }
      const remainingBytes = maxBytes - bytes;
      if (estimateValueBytes(safeRow, new WeakSet(), remainingBytes + 1) > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      const normalizedRow = normalizeDatabaseValue(safeRow);
      const rowBytes = Buffer.byteLength(JSON.stringify(normalizedRow));
      if (rowBytes > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      rows.push(normalizedRow);
      bytes += rowBytes;
    }
  } finally {
    await resultSet.close().catch(() => {});
  }
  return { rows, bytes, truncationReason };
}

function oracleTabularResult(columns, collected, maxRows) {
  const result = tabularResult(columns, collected.rows, maxRows);
  if (collected.truncationReason) {
    result.truncated = true;
    result.truncationReason = collected.truncationReason;
  }
  return result;
}

async function closeReturnedResultSets(result) {
  const resultSets = [result.resultSet, ...(result.implicitResults || [])]
    .filter((value) => value && typeof value.close === 'function');
  for (const resultSet of resultSets) await resultSet.close().catch(() => {});
  return resultSets.length;
}

export async function createOracleAdapter(target, credential) {
  invariant(!target.connection.trustServerCertificate, 'UNSUPPORTED_OPERATION', 'Oracle TCPS certificate verification cannot be disabled');
  const oracledb = await module();
  async function connect(timeoutMs) {
    const connection = await oracledb.getConnection({
      user: credential.username,
      password: credential.secret,
      connectString: connectString(target),
      connectTimeout: Math.max(1, Math.ceil(timeoutMs / 1000)),
    });
    connection.callTimeout = timeoutMs;
    return connection;
  }

  return {
    async test({ timeoutMs = 15000 } = {}) {
      let connection;
      try {
        connection = await connect(timeoutMs);
        return { identity: await identity(connection, target, credential, oracledb) };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await connection?.close().catch(() => {});
      }
    },

    async inspect({ timeoutMs }) {
      const startedAt = Date.now();
      let connection;
      try {
        connection = await connect(timeoutMs);
        await connection.execute('SET TRANSACTION READ ONLY');
        const verifiedIdentity = await identity(connection, target, credential, oracledb);
        const result = await connection.execute(
          `SELECT OWNER, TABLE_NAME, COLUMN_NAME, COLUMN_ID, DATA_TYPE, NULLABLE,
                  DATA_LENGTH, DATA_PRECISION, DATA_SCALE
             FROM ALL_TAB_COLUMNS
            ORDER BY OWNER, TABLE_NAME, COLUMN_ID`,
          [],
          { outFormat: oracledb.OUT_FORMAT_ARRAY, resultSet: true, fetchArraySize: 1 },
        );
        const rows = await collectOracleResultSet(result.resultSet, 10000, oracledb);
        await connection.rollback();
        return {
          identity: verifiedIdentity,
          schema: oracleTabularResult(
            result.metaData.map((column) => ({ name: column.name, dbTypeName: column.dbTypeName })),
            rows,
            10000,
          ),
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        await connection?.rollback().catch(() => {});
        throw databaseError(error, credential);
      } finally {
        await connection?.close().catch(() => {});
      }
    },

    async executeRead(sql, options) {
      requireReadOperation('oracle', sql, target, options);
      const { maxRows, timeoutMs } = options;
      const startedAt = Date.now();
      let connection;
      try {
        connection = await connect(timeoutMs);
        await connection.execute('SET TRANSACTION READ ONLY');
        const verifiedIdentity = await identity(connection, target, credential, oracledb);
        const result = await connection.execute(sql, [], {
          outFormat: oracledb.OUT_FORMAT_ARRAY,
          resultSet: true,
          fetchArraySize: 1,
        });
        const rows = await collectOracleResultSet(result.resultSet, maxRows, oracledb);
        await connection.rollback();
        return {
          identity: verifiedIdentity,
          result: oracleTabularResult(
            result.metaData?.map((column) => ({ name: column.name, dbTypeName: column.dbTypeName })) || [],
            rows,
            maxRows,
          ),
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        await connection?.rollback().catch(() => {});
        throw databaseError(error, credential);
      } finally {
        await connection?.close().catch(() => {});
      }
    },

    async executeMutation(sql, { timeoutMs, expectedIdentity, approvalExpiresAt }) {
      requireSqlMutation(sql, target.engine);
      const startedAt = Date.now();
      let connection;
      let operationSent = false;
      try {
        connection = await connect(timeoutMs);
        const verifiedIdentity = await identity(connection, target, credential, oracledb);
        verifyPlannedIdentity(expectedIdentity, verifiedIdentity);
        assertMutationApprovalActive(approvalExpiresAt);
        operationSent = true;
        const result = await connection.execute(sql, [], {
          autoCommit: false,
          outFormat: oracledb.OUT_FORMAT_OBJECT,
          resultSet: true,
          fetchArraySize: 1,
        });
        const returnedResultSetsDiscarded = await closeReturnedResultSets(result);
        await connection.commit();
        return {
          identity: verifiedIdentity,
          result: { rowsAffected: result.rowsAffected, returnedResultSetsDiscarded },
          elapsedMs: elapsed(startedAt),
          transactional: true,
        };
      } catch (error) {
        await connection?.rollback().catch(() => {});
        throw mutationDatabaseError(error, credential, operationSent);
      } finally {
        await connection?.close().catch(() => {});
      }
    },
  };
}
