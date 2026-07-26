import {
  estimateValueBytes,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
  tabularResult,
} from '../core/values.js';
import { invariant } from '../core/errors.js';
import { requireReadOperation, requireSqlMutation } from '../security/safety.js';
import { assertMutationApprovalActive, databaseError, elapsed, mutationDatabaseError, verifyIdentity, verifyPlannedIdentity } from './common.js';

async function modules() {
  const [{ default: pgDefault, ...pgNamed }, { default: Cursor }] = await Promise.all([import('pg'), import('pg-cursor')]);
  return { pg: pgDefault || pgNamed, Cursor };
}

function config(target, credential, timeoutMs = 15000) {
  return {
    host: target.connection.host,
    port: target.connection.port,
    database: target.connection.database,
    user: credential.username,
    password: credential.secret,
    application_name: 'data-debug',
    connectionTimeoutMillis: timeoutMs,
    ssl: target.connection.tls
      ? { rejectUnauthorized: !target.connection.trustServerCertificate }
      : undefined,
  };
}

export function postgresqlIdentityFromRow(target, credential, row) {
  const databaseIdentity = {
    database: row.database,
    principal: row.principal,
    serverIdentity: row.server_identity,
    version: row.version,
    credentialMode: credential.mode,
  };
  if (credential.mode === 'mutation') {
    const clusterSystemIdentifier = typeof row?.cluster_system_identifier === 'string'
      ? row.cluster_system_identifier.trim()
      : '';
    invariant(
      clusterSystemIdentifier,
      'TARGET_IDENTITY_MISMATCH',
      'PostgreSQL did not report a cluster system identifier',
    );
    databaseIdentity.clusterSystemIdentifier = clusterSystemIdentifier;
  }
  return verifyIdentity(target, databaseIdentity);
}

async function identity(client, target, credential) {
  const result = await client.query(`
    SELECT current_database() AS database,
           current_user AS principal,
           COALESCE(inet_server_addr()::text, 'local') AS server_identity,
           version() AS version
  `);
  const row = result.rows[0];
  if (credential.mode === 'mutation') {
    const control = await client.query(`
      SELECT system_identifier::text AS cluster_system_identifier
        FROM pg_control_system()
    `);
    row.cluster_system_identifier = control.rows[0]?.cluster_system_identifier;
  }
  return postgresqlIdentityFromRow(target, credential, row);
}

export async function executePostgresqlMutationStreaming(client, Query, sql) {
  const query = new Query(sql);
  const returnedRows = new Map();
  let returnedRowsDiscarded = 0;
  query.on('row', (_row, result) => {
    returnedRowsDiscarded = Math.min(Number.MAX_SAFE_INTEGER, returnedRowsDiscarded + 1);
    if (returnedRows.has(result) || returnedRows.size < 1000) {
      returnedRows.set(result, (returnedRows.get(result) || 0) + 1);
    }
  });

  return new Promise((resolve, reject) => {
    let settled = false;
    const fail = (error) => {
      if (settled) return;
      settled = true;
      reject(error);
    };
    query.once('error', fail);
    query.once('end', (result) => {
      if (settled) return;
      settled = true;
      const results = Array.isArray(result) ? result : [result];
      resolve({
        statements: results.slice(0, 1000).map((entry) => ({
          command: entry.command,
          rowCount: entry.rowCount,
          returnedRowsDiscarded: returnedRows.get(entry) || 0,
        })),
        statementCount: results.length,
        statementsTruncated: results.length > 1000,
        returnedRowsDiscarded,
      });
    });
    try {
      client.query(query);
    } catch (error) {
      fail(error);
    }
  });
}

export async function collectPostgresqlCursor(cursor, maxRows, maxBytes = MAX_OUTPUT_BYTES) {
  const rows = [];
  let bytes = 0;
  let truncationReason = null;
  try {
    while (true) {
      const batch = await cursor.read(1);
      if (batch.length === 0) break;
      if (rows.length >= maxRows) {
        truncationReason = 'max-rows';
        break;
      }
      const row = batch[0];
      const remainingBytes = maxBytes - bytes;
      if (estimateValueBytes(row, new WeakSet(), remainingBytes + 1) > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      const normalizedRow = normalizeDatabaseValue(row);
      const rowBytes = Buffer.byteLength(JSON.stringify(normalizedRow));
      if (rowBytes > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      rows.push(normalizedRow);
      bytes += rowBytes;
    }
  } finally {
    await cursor.close();
  }
  return { rows, bytes, truncationReason };
}

export async function createPostgresqlAdapter(target, credential) {
  const { pg, Cursor } = await modules();

  return {
    async test({ timeoutMs = 15000 } = {}) {
      const client = new pg.Client(config(target, credential, timeoutMs));
      try {
        await client.connect();
        return { identity: await identity(client, target, credential) };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await client.end().catch(() => {});
      }
    },

    async inspect({ timeoutMs }) {
      const startedAt = Date.now();
      const client = new pg.Client(config(target, credential, timeoutMs));
      try {
        await client.connect();
        await client.query('BEGIN READ ONLY');
        await client.query(`SET LOCAL statement_timeout = ${timeoutMs}`);
        const verifiedIdentity = await identity(client, target, credential);
        const result = await client.query({
          text: `
            SELECT c.table_schema, c.table_name, c.column_name, c.ordinal_position,
                   c.data_type, c.is_nullable,
                   EXISTS (
                     SELECT 1 FROM information_schema.table_constraints tc
                     JOIN information_schema.key_column_usage kcu
                       ON tc.constraint_name = kcu.constraint_name
                      AND tc.constraint_schema = kcu.constraint_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                      AND kcu.table_schema = c.table_schema
                      AND kcu.table_name = c.table_name
                      AND kcu.column_name = c.column_name
                   ) AS is_primary_key
             FROM information_schema.columns c
             WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
             ORDER BY c.table_schema, c.table_name, c.ordinal_position
             LIMIT 10001
          `,
          rowMode: 'array',
        });
        await client.query('ROLLBACK');
        return {
          identity: verifiedIdentity,
          schema: tabularResult(result.fields.map((field) => ({ name: field.name, dataTypeId: field.dataTypeID })), result.rows, 10000),
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        await client.query('ROLLBACK').catch(() => {});
        throw databaseError(error, credential);
      } finally {
        await client.end().catch(() => {});
      }
    },

    async executeRead(sql, options) {
      requireReadOperation('postgresql', sql, target, options);
      const { maxRows, timeoutMs } = options;
      const startedAt = Date.now();
      const client = new pg.Client(config(target, credential, timeoutMs));
      try {
        await client.connect();
        await client.query('BEGIN READ ONLY');
        await client.query(`SET LOCAL statement_timeout = ${timeoutMs}`);
        const verifiedIdentity = await identity(client, target, credential);
        const cursor = client.query(new Cursor(sql));
        const collected = await collectPostgresqlCursor(cursor, maxRows);
        await client.query('ROLLBACK');
        const columns = collected.rows[0] ? Object.keys(collected.rows[0]).map((name) => ({ name })) : [];
        const result = tabularResult(columns, collected.rows.map((row) => columns.map(({ name }) => row[name])), maxRows);
        if (collected.truncationReason) {
          result.truncated = true;
          result.truncationReason = collected.truncationReason;
        }
        return { identity: verifiedIdentity, result, elapsedMs: elapsed(startedAt) };
      } catch (error) {
        await client.query('ROLLBACK').catch(() => {});
        throw databaseError(error, credential);
      } finally {
        await client.end().catch(() => {});
      }
    },

    async executeMutation(sql, { timeoutMs, expectedIdentity, transactionMode, approvalExpiresAt }) {
      requireSqlMutation(sql, target.engine);
      const startedAt = Date.now();
      const client = new pg.Client(config(target, credential, timeoutMs));
      const useTransaction = transactionMode !== 'never';
      let operationSent = false;
      let commitStarted = false;
      try {
        await client.connect();
        const verifiedIdentity = await identity(client, target, credential);
        verifyPlannedIdentity(expectedIdentity, verifiedIdentity);
        if (useTransaction) await client.query('BEGIN');
        await client.query(`${useTransaction ? 'SET LOCAL' : 'SET'} statement_timeout = ${timeoutMs}`);
        assertMutationApprovalActive(approvalExpiresAt);
        operationSent = true;
        const result = await executePostgresqlMutationStreaming(client, pg.Query, sql);
        if (useTransaction) {
          commitStarted = true;
          await client.query('COMMIT');
        }
        return {
          identity: verifiedIdentity,
          result,
          resultTruncated: result.statementsTruncated || result.returnedRowsDiscarded > 0,
          elapsedMs: elapsed(startedAt),
          transactional: useTransaction,
        };
      } catch (error) {
        if (useTransaction && !commitStarted) {
          await client.query('ROLLBACK').catch(() => {});
        }
        throw mutationDatabaseError(error, credential, operationSent || commitStarted);
      } finally {
        await client.end().catch(() => {});
      }
    },
  };
}
