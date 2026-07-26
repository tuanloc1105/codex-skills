import { DataDebugError, invariant } from '../core/errors.js';
import {
  boundedNormalizedValues,
  estimateValueBytes,
  MAX_OUTPUT_BYTES,
  normalizeDatabaseValue,
} from '../core/values.js';
import { requireMongoMutation, requireMongoRead } from '../security/safety.js';
import { assertAllowedNamespace, assertMutationApprovalActive, databaseError, elapsed, mutationDatabaseError, verifyIdentity, verifyPlannedIdentity } from './common.js';

async function module() {
  return import('mongodb');
}

export function mongoClientOptions(target, credential, timeoutMs = 15000) {
  return {
    auth: { username: credential.username, password: credential.secret },
    authSource: target.connection.authSource || target.connection.database,
    tls: target.connection.tls ?? false,
    appName: 'data-debug',
    serverSelectionTimeoutMS: timeoutMs,
    connectTimeoutMS: timeoutMs,
    socketTimeoutMS: timeoutMs,
    maxPoolSize: 2,
    retryWrites: false,
  };
}

function remainingDeadlineMs(deadline) {
  const remaining = deadline - Date.now();
  invariant(remaining > 0, 'DATABASE_TIMEOUT', 'MongoDB operation exceeded its total time budget');
  return Math.max(1, remaining);
}

export function mongoHelloServerIdentity(hello) {
  const serviceId = hello.serviceId?.toString?.();
  if (serviceId) return `service:${serviceId}`;
  const processId = hello.topologyVersion?.processId?.toString?.();
  if (processId) return `${hello.setName ? `set:${hello.setName}|` : ''}process:${processId}`;
  if (hello.me) return `address:${hello.me}`;
  return hello.setName ? `set:${hello.setName}` : null;
}

async function identity(client, target, credential, { timeoutMs = 15000, deadline } = {}) {
  const operationTimeout = () => deadline ? remainingDeadlineMs(deadline) : timeoutMs;
  const hello = await client.db('admin').command({ hello: 1 }, { maxTimeMS: operationTimeout() });
  let serverIdentity = mongoHelloServerIdentity(hello);
  let identityAssurance = hello.serviceId
    ? 'service-id'
    : hello.topologyVersion?.processId
      ? 'topology-process-id'
      : hello.me
        ? 'server-reported-address'
        : hello.setName
          ? 'replica-set-name'
          : 'unverified';
  if (!serverIdentity) {
    try {
      const status = await client.db('admin').command({ serverStatus: 1 }, { maxTimeMS: operationTimeout() });
      serverIdentity = status.host || null;
      if (serverIdentity) identityAssurance = 'server-status-host';
    } catch {
      // A least-privilege read account may not have serverStatus. Mutations require an expected identity.
    }
  }
  if (credential.mode === 'mutation') {
    invariant(serverIdentity, 'TARGET_IDENTITY_MISMATCH', 'MongoDB mutation requires a stable server or topology identity');
    invariant(identityAssurance !== 'replica-set-name', 'TARGET_IDENTITY_MISMATCH', 'MongoDB mutation requires identity stronger than a replica-set name');
  }
  return verifyIdentity(target, {
    database: target.connection.database,
    databaseAssurance: 'configured-namespace',
    principal: credential.username,
    serverIdentity,
    version: hello.maxWireVersion,
    topology: hello.setName ? 'replica-set' : hello.msg === 'isdbgrid' ? 'sharded' : 'standalone',
    identityAssurance,
    credentialMode: credential.mode,
  });
}

function requireCollection(target, operation) {
  invariant(typeof operation.collection === 'string' && operation.collection, 'INVALID_ARGUMENT', 'MongoDB operation requires collection');
  assertAllowedNamespace(target, operation.collection);
  return operation.collection;
}

function bounded(values, maxRows, fetchResult = {}) {
  const result = boundedNormalizedValues(values, maxRows);
  const fetchReason = fetchResult.truncationReason || null;
  return {
    documents: result.values,
    rowCount: result.values.length,
    truncated: Boolean(fetchReason) || result.truncated,
    truncationReason: fetchReason || result.truncationReason,
    outputBytes: result.bytes,
  };
}

function requireAcknowledged(result) {
  if (result?.acknowledged !== true) {
    throw new DataDebugError(
      'MUTATION_OUTCOME_UNKNOWN',
      'MongoDB did not acknowledge the write, so its final outcome cannot be inferred',
      { requiresVerification: true },
    );
  }
  return result;
}

export async function collectBoundedMongoCursor(
  cursor,
  maxRows,
  { maxBytes = MAX_OUTPUT_BYTES, deadline } = {},
) {
  const values = [];
  let bytes = 0;
  let truncationReason = null;
  try {
    for await (const value of cursor) {
      if (deadline) remainingDeadlineMs(deadline);
      if (values.length >= maxRows) {
        truncationReason = 'max-rows';
        break;
      }
      const remainingBytes = maxBytes - bytes;
      if (estimateValueBytes(value, new WeakSet(), remainingBytes + 1) > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      const normalizedValue = normalizeDatabaseValue(value);
      const valueBytes = Buffer.byteLength(JSON.stringify(normalizedValue));
      if (valueBytes > remainingBytes) {
        truncationReason = 'max-output-bytes';
        break;
      }
      values.push(normalizedValue);
      bytes += valueBytes;
    }
  } finally {
    await cursor.close().catch(() => {});
  }
  return { values, bytes, truncationReason };
}

async function executeMongoRead(db, target, operation, maxRows, timeoutMs) {
  if (operation.operation === 'listCollections') {
    const allowed = target.allowedNamespaces || [];
    const filter = allowed.length > 0
      ? { $and: [operation.filter || {}, { name: { $in: allowed } }] }
      : operation.filter || {};
    const rows = await collectBoundedMongoCursor(
      db.listCollections(filter, { nameOnly: false, maxTimeMS: timeoutMs, batchSize: Math.min(maxRows + 1, 1000) }),
      maxRows,
    );
    return bounded(rows.values, maxRows, rows);
  }
  const collection = db.collection(requireCollection(target, operation));
  switch (operation.operation) {
    case 'find': {
      const cursor = collection.find(operation.filter || {}, {
        projection: operation.projection,
        sort: operation.sort,
        skip: operation.skip,
        maxTimeMS: timeoutMs,
      }).limit(maxRows + 1);
      const rows = await collectBoundedMongoCursor(cursor, maxRows);
      return bounded(rows.values, maxRows, rows);
    }
    case 'findOne':
      return bounded([await collection.findOne(operation.filter || {}, { projection: operation.projection, maxTimeMS: timeoutMs })].filter(Boolean), maxRows);
    case 'aggregate': {
      const pipeline = [...(operation.pipeline || []), { $limit: maxRows + 1 }];
      const rows = await collectBoundedMongoCursor(collection.aggregate(pipeline, { maxTimeMS: timeoutMs }), maxRows);
      return bounded(rows.values, maxRows, rows);
    }
    case 'countDocuments':
      return { value: await collection.countDocuments(operation.filter || {}, { maxTimeMS: timeoutMs }) };
    case 'estimatedDocumentCount':
      return { value: await collection.estimatedDocumentCount({ maxTimeMS: timeoutMs }) };
    case 'distinct': {
      invariant(typeof operation.field === 'string' && operation.field, 'INVALID_ARGUMENT', 'distinct requires field');
      const values = await collection.distinct(operation.field, operation.filter || {}, { maxTimeMS: timeoutMs });
      const result = boundedNormalizedValues(values, maxRows);
      return { values: result.values, rowCount: result.values.length, truncated: result.truncated, truncationReason: result.truncationReason, outputBytes: result.bytes };
    }
    case 'listIndexes': {
      const indexes = await collectBoundedMongoCursor(
        collection.listIndexes({ maxTimeMS: timeoutMs, batchSize: Math.min(maxRows + 1, 1000) }),
        maxRows,
      );
      return bounded(indexes.values, maxRows, indexes);
    }
    default:
      throw new Error(`Unsupported MongoDB read operation: ${operation.operation}`);
  }
}

async function executeMongoMutation(db, target, operation, timeoutMs) {
  const collection = db.collection(requireCollection(target, operation));
  const common = { ...(operation.options || {}), maxTimeMS: timeoutMs, timeoutMS: timeoutMs };
  switch (operation.operation) {
    case 'insertOne': {
      const result = requireAcknowledged(await collection.insertOne(operation.document, common));
      return { acknowledged: result.acknowledged, insertedId: result.insertedId };
    }
    case 'insertMany': {
      const result = requireAcknowledged(await collection.insertMany(operation.documents, common));
      return { acknowledged: result.acknowledged, insertedCount: result.insertedCount, insertedIdsOmitted: true };
    }
    case 'updateOne':
    case 'updateMany':
    case 'replaceOne': {
      const method = collection[operation.operation].bind(collection);
      const args = operation.operation === 'replaceOne'
        ? [operation.filter, operation.replacement, common]
        : [operation.filter, operation.update, common];
      const result = requireAcknowledged(await method(...args));
      return {
        acknowledged: result.acknowledged,
        matchedCount: result.matchedCount,
        modifiedCount: result.modifiedCount,
        upsertedCount: result.upsertedCount,
        upsertedId: result.upsertedId,
      };
    }
    case 'deleteOne':
    case 'deleteMany': {
      const result = requireAcknowledged(await collection[operation.operation](operation.filter, common));
      return { acknowledged: result.acknowledged, deletedCount: result.deletedCount };
    }
    default: throw new Error(`Unsupported MongoDB mutation operation: ${operation.operation}`);
  }
}

export async function createMongoAdapter(target, credential) {
  const { MongoClient } = await module();
  const uri = `mongodb://${target.connection.host}:${target.connection.port}`;
  const createClient = (timeoutMs = 15000) => new MongoClient(uri, mongoClientOptions(target, credential, timeoutMs));

  return {
    async test({ timeoutMs = 15000 } = {}) {
      const client = createClient(timeoutMs);
      try {
        await client.connect();
        return { identity: await identity(client, target, credential, { timeoutMs }) };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await client.close().catch(() => {});
      }
    },

    async inspect({ timeoutMs }) {
      const startedAt = Date.now();
      const deadline = startedAt + timeoutMs;
      const client = createClient(timeoutMs);
      try {
        await client.connect();
        const verifiedIdentity = await identity(client, target, credential, { deadline });
        const db = client.db(target.connection.database);
        const allowed = target.allowedNamespaces || [];
        const collectionFilter = allowed.length > 0 ? { name: { $in: allowed } } : {};
        const collectionCursor = db.listCollections(collectionFilter, {
          nameOnly: false,
          maxTimeMS: remainingDeadlineMs(deadline),
          batchSize: 1,
        });
        const schema = [];
        let schemaBytes = 0;
        let schemaTruncated = false;
        try {
          for await (const collectionInfo of collectionCursor) {
            remainingDeadlineMs(deadline);
            if (schema.length >= 1000) {
              schemaTruncated = true;
              break;
            }
            const remainingBytes = MAX_OUTPUT_BYTES - schemaBytes;
            const base = {
              name: collectionInfo.name,
              type: collectionInfo.type,
              options: collectionInfo.options,
              validator: collectionInfo.options?.validator,
            };
            if (estimateValueBytes(base, new WeakSet(), remainingBytes + 1) > remainingBytes) {
              schemaTruncated = true;
              break;
            }
            const normalizedBase = normalizeDatabaseValue(base);
            const baseBytes = Buffer.byteLength(JSON.stringify(normalizedBase));
            if (baseBytes > remainingBytes) {
              schemaTruncated = true;
              break;
            }
            const indexes = await collectBoundedMongoCursor(
              db.collection(collectionInfo.name).listIndexes({
                maxTimeMS: remainingDeadlineMs(deadline),
                batchSize: 1,
              }),
              1000,
              { maxBytes: Math.max(0, remainingBytes - baseBytes - 256), deadline },
            );
            const entry = normalizeDatabaseValue({
              ...normalizedBase,
              indexes: indexes.values,
              indexesTruncated: Boolean(indexes.truncationReason),
            });
            const entryBytes = Buffer.byteLength(JSON.stringify(entry));
            if (entryBytes > remainingBytes) {
              schemaTruncated = true;
              break;
            }
            schema.push(entry);
            schemaBytes += entryBytes;
            if (indexes.truncationReason === 'max-output-bytes') {
              schemaTruncated = true;
              break;
            }
            if (indexes.truncationReason) schemaTruncated = true;
          }
        } finally {
          await collectionCursor.close().catch(() => {});
        }
        return {
          identity: verifiedIdentity,
          schema,
          schemaTruncated,
          elapsedMs: elapsed(startedAt),
        };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await client.close().catch(() => {});
      }
    },

    async executeRead(rawInput, { maxRows, timeoutMs }) {
      const startedAt = Date.now();
      const client = createClient(timeoutMs);
      try {
        await client.connect();
        const verifiedIdentity = await identity(client, target, credential, { timeoutMs });
        const operation = requireMongoRead(rawInput, target);
        const result = await executeMongoRead(client.db(target.connection.database), target, operation, maxRows, timeoutMs);
        return { identity: verifiedIdentity, result, elapsedMs: elapsed(startedAt) };
      } catch (error) {
        throw databaseError(error, credential);
      } finally {
        await client.close().catch(() => {});
      }
    },

    async executeMutation(rawInput, { timeoutMs, expectedIdentity, approvalExpiresAt }) {
      const startedAt = Date.now();
      const client = createClient(timeoutMs);
      let operationSent = false;
      try {
        await client.connect();
        const verifiedIdentity = await identity(client, target, credential, { timeoutMs });
        verifyPlannedIdentity(expectedIdentity, verifiedIdentity);
        const operation = requireMongoMutation(rawInput, target);
        assertMutationApprovalActive(approvalExpiresAt);
        operationSent = true;
        const result = await executeMongoMutation(client.db(target.connection.database), target, operation, timeoutMs);
        const boundedResult = boundedNormalizedValues([result], 1);
        return {
          identity: verifiedIdentity,
          result: boundedResult.values[0] || null,
          resultTruncated: boundedResult.truncated,
          elapsedMs: elapsed(startedAt),
          transactional: false,
        };
      } catch (error) {
        throw mutationDatabaseError(error, credential, operationSent);
      } finally {
        await client.close().catch(() => {});
      }
    },
  };
}
