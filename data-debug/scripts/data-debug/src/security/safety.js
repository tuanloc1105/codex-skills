import { DataDebugError, invariant } from '../core/errors.js';

const SQL_READ_PREFIXES = new Set(['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']);
const SQL_MUTATION_PREFIXES = new Set(['INSERT', 'UPDATE', 'DELETE']);
const SQL_MUTATION_FORBIDDEN_WORDS = new Set([
  'MERGE', 'UPSERT', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'GRANT', 'REVOKE',
  'CALL', 'EXEC', 'EXECUTE', 'DECLARE', 'BEGIN', 'DO', 'COPY', 'LOAD', 'LOCK',
  'VACUUM', 'REINDEX', 'BACKUP', 'RESTORE', 'KILL', 'SHUTDOWN', 'ATTACH', 'DETACH',
  'DENY', 'DBCC', 'CHECKPOINT', 'USE', 'WAITFOR', 'WRITETEXT', 'UPDATETEXT',
  'RECONFIGURE', 'ENABLE', 'DISABLE', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SAVE',
  'RECEIVE', 'SEND', 'OPEN',
]);
const SQL_BLOCKED_WORDS = new Set([
  'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE',
  'GRANT', 'REVOKE', 'CALL', 'EXEC', 'EXECUTE', 'DECLARE', 'BEGIN', 'DO', 'COPY', 'LOAD',
  'LOCK', 'VACUUM', 'REINDEX', 'BACKUP', 'RESTORE', 'KILL', 'SHUTDOWN', 'ATTACH', 'DETACH',
  'DENY', 'DBCC', 'CHECKPOINT', 'USE', 'SET', 'WAITFOR', 'WRITETEXT', 'UPDATETEXT',
  'RECONFIGURE', 'ENABLE', 'DISABLE', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SAVE',
  'RECEIVE', 'SEND', 'OPEN', 'OPENROWSET', 'OPENQUERY', 'OPENDATASOURCE',
]);
const POSTGRES_STATEFUL_FUNCTION = /\b(?:PG_TERMINATE_BACKEND|PG_CANCEL_BACKEND|PG_RELOAD_CONF|PG_ROTATE_LOGFILE|PG_CREATE_RESTORE_POINT|PG_SWITCH_WAL|PG_WAL_REPLAY_PAUSE|PG_WAL_REPLAY_RESUME|PG_PROMOTE|PG_(?:START|STOP)_BACKUP|PG_BACKUP_(?:START|STOP)|PG_CREATE_(?:PHYSICAL|LOGICAL)_REPLICATION_SLOT|PG_DROP_REPLICATION_SLOT|PG_REPLICATION_ORIGIN_[A-Z0-9_]+|PG_STAT_RESET[A-Z0-9_]*|PG_READ_FILE|PG_READ_BINARY_FILE|PG_STAT_FILE|PG_LS_[A-Z0-9_]+|PG_ADVISORY_(?:XACT_)?LOCK(?:_SHARED)?|PG_ADVISORY_UNLOCK(?:_ALL|_SHARED)?|PG_NOTIFY|PG_LOGICAL_EMIT_MESSAGE|SET_CONFIG|SETVAL|LO_CREATE|LO_FROM_BYTEA|LO_PUT|LOWRITE|LO_TRUNCATE|LO_IMPORT|LO_EXPORT|LO_UNLINK|DBLINK[A-Z0-9_]*)\s*\(/;
const ORACLE_UNSAFE_PACKAGE = /\b(?:UTL_HTTP|UTL_TCP|UTL_SMTP|UTL_FILE|UTL_INADDR|UTL_MAIL|DBMS_LDAP|DBMS_LOCK|DBMS_PIPE|DBMS_ALERT|DBMS_SQL|DBMS_XMLGEN|DBMS_XMLQUERY|DBMS_HS_PASSTHROUGH|DBMS_UTILITY|DBMS_SCHEDULER|DBMS_JOB|DBMS_DATAPUMP|DBMS_AQ|DBMS_AQADM|DBMS_JAVA|DBMS_XSLPROCESSOR|HTTPURITYPE)\b/;
const SQL_EXTERNAL_ACCESS = /\b(?:OPENROWSET|OPENQUERY|OPENDATASOURCE)\b/;
const SQL_IDENTIFIER = '[A-Z_][A-Z0-9_$#]*';
const SQL_TARGET_PREFIX = '(?:FROM|JOIN|UPDATE|INTO|INSERT|DELETE)\\s+(?:ONLY\\s+)?(?:TOP\\s*\\([^)]*\\)\\s+)?';
const SQL_THREE_PART_SOURCE = new RegExp(`\\b${SQL_TARGET_PREFIX}${SQL_IDENTIFIER}\\s*\\.\\s*${SQL_IDENTIFIER}\\s*\\.\\s*${SQL_IDENTIFIER}\\b`);
const SQL_OMITTED_SCHEMA_SOURCE = new RegExp(`\\b${SQL_TARGET_PREFIX}(?:${SQL_IDENTIFIER}\\s*\\.\\s*){1,2}\\.\\s*${SQL_IDENTIFIER}\\b`);
const SQL_CROSS_DATABASE_FUNCTION = new RegExp(`\\b${SQL_IDENTIFIER}\\s*\\.\\s*${SQL_IDENTIFIER}\\s*\\.\\s*${SQL_IDENTIFIER}\\s*\\(`);
const ORACLE_DATABASE_LINK = new RegExp(`\\b${SQL_TARGET_PREFIX}(?:${SQL_IDENTIFIER}\\s*\\.\\s*)?${SQL_IDENTIFIER}\\s*@\\s*${SQL_IDENTIFIER}\\b`);
const ORACLE_DATABASE_LINK_FUNCTION = new RegExp(`\\b${SQL_IDENTIFIER}\\s*@\\s*${SQL_IDENTIFIER}\\s*\\(`);

function hasCrossTargetSqlAccess(identifierVisible) {
  return SQL_THREE_PART_SOURCE.test(identifierVisible)
    || SQL_OMITTED_SCHEMA_SOURCE.test(identifierVisible)
    || SQL_CROSS_DATABASE_FUNCTION.test(identifierVisible)
    || ORACLE_DATABASE_LINK.test(identifierVisible)
    || ORACLE_DATABASE_LINK_FUNCTION.test(identifierVisible);
}
const MONGO_READ_OPERATIONS = new Set([
  'find', 'findOne', 'aggregate', 'countDocuments', 'estimatedDocumentCount', 'distinct',
  'listCollections', 'listIndexes',
]);
const MONGO_READ_FIELDS = new Map([
  ['find', new Set(['operation', 'collection', 'filter', 'projection', 'sort', 'skip'])],
  ['findOne', new Set(['operation', 'collection', 'filter', 'projection'])],
  ['aggregate', new Set(['operation', 'collection', 'pipeline'])],
  ['countDocuments', new Set(['operation', 'collection', 'filter'])],
  ['estimatedDocumentCount', new Set(['operation', 'collection'])],
  ['distinct', new Set(['operation', 'collection', 'field', 'filter'])],
  ['listCollections', new Set(['operation', 'filter'])],
  ['listIndexes', new Set(['operation', 'collection'])],
]);
const MONGO_MUTATION_OPERATIONS = new Set([
  'insertOne', 'insertMany', 'updateOne', 'updateMany', 'replaceOne', 'deleteOne', 'deleteMany',
]);

const MONGO_MUTATION_OPTION_KEYS = new Map([
  ['insertOne', new Set(['bypassDocumentValidation', 'forceServerObjectId', 'checkKeys', 'ignoreUndefined', 'comment'])],
  ['insertMany', new Set(['ordered', 'bypassDocumentValidation', 'forceServerObjectId', 'checkKeys', 'ignoreUndefined', 'comment'])],
  ['updateOne', new Set(['upsert', 'arrayFilters', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment', 'sort'])],
  ['updateMany', new Set(['upsert', 'arrayFilters', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment'])],
  ['replaceOne', new Set(['upsert', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment', 'sort'])],
  ['deleteOne', new Set(['collation', 'hint', 'let', 'comment'])],
  ['deleteMany', new Set(['collation', 'hint', 'let', 'comment'])],
]);
const MONGO_MUTATION_FIELDS = new Map([
  ['insertOne', new Set(['operation', 'collection', 'document', 'options'])],
  ['insertMany', new Set(['operation', 'collection', 'documents', 'options'])],
  ['updateOne', new Set(['operation', 'collection', 'filter', 'update', 'options'])],
  ['updateMany', new Set(['operation', 'collection', 'filter', 'update', 'options'])],
  ['replaceOne', new Set(['operation', 'collection', 'filter', 'replacement', 'options'])],
  ['deleteOne', new Set(['operation', 'collection', 'filter', 'options'])],
  ['deleteMany', new Set(['operation', 'collection', 'filter', 'options'])],
]);
const REDIS_INFO_SECTIONS = new Set([
  'server', 'clients', 'memory', 'persistence', 'stats', 'replication', 'cpu', 'keyspace',
  'errorstats', 'commandstats', 'latencystats',
]);
const REDIS_VALUE_PREVIEW_BYTES = 64 * 1024;

function blankQuotedSql(sql, { preserveIdentifiers = false, dialect = 'generic' } = {}) {
  let output = '';
  let index = 0;
  while (index < sql.length) {
    const character = sql[index];
    const next = sql[index + 1];

    if (character === '-' && next === '-') {
      const end = sql.indexOf('\n', index + 2);
      const stop = end < 0 ? sql.length : end;
      output += ' '.repeat(stop - index);
      index = stop;
      continue;
    }
    if (character === '/' && next === '*') {
      let cursor = index + 2;
      let closed = false;
      while (cursor < sql.length) {
        if (sql[cursor] === '/' && sql[cursor + 1] === '*') {
          throw new DataDebugError(
            'UNSUPPORTED_OPERATION',
            'Nested SQL block comments are ambiguous across supported engines',
          );
        } else if (sql[cursor] === '*' && sql[cursor + 1] === '/') {
          cursor += 2;
          closed = true;
          break;
        } else {
          cursor += 1;
        }
      }
      invariant(closed, 'READ_ONLY_VIOLATION', 'Unterminated SQL block comment');
      output += ' '.repeat(cursor - index);
      index = cursor;
      continue;
    }
    if (character === '$') {
      const match = sql.slice(index).match(/^\$[A-Za-z0-9_]*\$/);
      if (match) {
        const tag = match[0];
        const end = sql.indexOf(tag, index + tag.length);
        invariant(end >= 0, 'READ_ONLY_VIOLATION', 'Unterminated SQL dollar-quoted string');
        output += ' '.repeat(end + tag.length - index);
        index = end + tag.length;
        continue;
      }
    }
    if (
      (character === 'u' || character === 'U')
      && next === '&'
      && sql[index + 2] === '"'
      && (index === 0 || !/[A-Za-z0-9_$#]/.test(sql[index - 1]))
    ) {
      throw new DataDebugError(
        'UNSUPPORTED_OPERATION',
        'Unicode-escaped SQL identifiers are not supported by the safety classifier',
      );
    }
    const oracleQuotePrefixLength = (
      (character === 'q' || character === 'Q') && next === '\''
    ) ? 1 : (
      (character === 'n' || character === 'N')
      && (next === 'q' || next === 'Q')
      && sql[index + 2] === '\''
    ) ? 2 : 0;
    if (
      oracleQuotePrefixLength > 0
      && (index === 0 || !/[A-Za-z0-9_$#]/.test(sql[index - 1]))
    ) {
      const delimiter = sql[index + oracleQuotePrefixLength + 1];
      invariant(delimiter && !/\s/.test(delimiter), 'UNSUPPORTED_OPERATION', 'Invalid Oracle alternative-quoted string');
      const paired = { '[': ']', '{': '}', '(': ')', '<': '>' };
      const closing = paired[delimiter] || delimiter;
      const end = sql.indexOf(`${closing}'`, index + oracleQuotePrefixLength + 2);
      invariant(end >= 0, 'UNSUPPORTED_OPERATION', 'Unterminated Oracle alternative-quoted string');
      output += ' '.repeat(end + 2 - index);
      index = end + 2;
      continue;
    }
    if (character === '`') {
      throw new DataDebugError('UNSUPPORTED_OPERATION', 'Backtick-quoted SQL identifiers are not supported');
    }
    if (character === '\'' || character === '"' || (character === '[' && ['generic', 'sqlserver'].includes(dialect))) {
      const closing = character === '[' ? ']' : character;
      let cursor = index + 1;
      while (cursor < sql.length) {
        if (character === '\'' && sql[cursor] === '\\') {
          throw new DataDebugError(
            'UNSUPPORTED_OPERATION',
            'Backslash escapes inside SQL string literals are ambiguous across supported engines',
          );
        }
        if (sql[cursor] === closing) {
          if (sql[cursor + 1] === closing) {
            cursor += 2;
            continue;
          }
          cursor += 1;
          break;
        }
        cursor += 1;
      }
      invariant(cursor <= sql.length && sql[cursor - 1] === closing, 'READ_ONLY_VIOLATION', 'Unterminated SQL quoted value');
      if (preserveIdentifiers && character !== '\'') {
        const inner = sql.slice(index + 1, cursor - 1)
          .split(closing + closing).join(closing)
          .replace(/[^A-Za-z0-9_$#]+/g, '_');
        output += ` ${inner} `;
      } else {
        output += ' '.repeat(cursor - index);
      }
      index = cursor;
      continue;
    }
    output += character;
    index += 1;
  }
  return output;
}

export function classifySqlRead(sql, engine = 'generic') {
  invariant(typeof sql === 'string' && sql.trim(), 'INVALID_ARGUMENT', 'SQL input is empty');
  const visible = blankQuotedSql(sql, { dialect: engine }).toUpperCase();
  const identifierVisible = blankQuotedSql(sql, { preserveIdentifiers: true, dialect: engine }).toUpperCase();
  const statements = visible.split(';').map((part) => part.trim()).filter(Boolean);
  if (statements.length !== 1) {
    return { classification: 'unknown', reason: 'Multi-statement SQL is not allowed in read mode' };
  }

  const words = statements[0].match(/[A-Z_][A-Z0-9_$#]*/g) || [];
  if (!SQL_READ_PREFIXES.has(words[0])) {
    return { classification: 'mutation', reason: `SQL begins with ${words[0] || 'an unknown token'}` };
  }
  const blocked = words.find((word) => SQL_BLOCKED_WORDS.has(word));
  if (blocked) return { classification: 'mutation', reason: `SQL contains ${blocked}` };
  if (/\bEXPLAIN\s+(?:\([^)]*\bANALYZE\b[^)]*\)|ANALYZE\b)/.test(statements[0])) {
    return { classification: 'mutation', reason: 'EXPLAIN ANALYZE executes the statement' };
  }
  if (/\bEXPLAIN\s+PLAN\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'Oracle EXPLAIN PLAN writes to PLAN_TABLE' };
  }
  if (/\bINTO\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'SELECT INTO creates or writes an object' };
  }
  if (/\bFOR\s+(?:UPDATE|SHARE)\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'Locking reads are not permitted in read mode' };
  }
  if (/\bFOR\s+(?:NO\s+KEY\s+UPDATE|KEY\s+SHARE)\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'Locking reads are not permitted in read mode' };
  }
  if (/\bWITH\s*\([^)]*\b(?:UPDLOCK|XLOCK|TABLOCKX|HOLDLOCK)\b[^)]*\)/.test(statements[0])) {
    return { classification: 'mutation', reason: 'SQL Server locking hints are not permitted in read mode' };
  }
  if (/\bNEXTVAL\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'Sequence NEXTVAL changes database state' };
  }
  if (/\bNEXT\s+VALUE\s+FOR\b/.test(statements[0])) {
    return { classification: 'mutation', reason: 'SQL Server NEXT VALUE FOR changes sequence state' };
  }
  if (POSTGRES_STATEFUL_FUNCTION.test(identifierVisible)) {
    return { classification: 'mutation', reason: 'SQL calls a PostgreSQL function with administrative or state-changing effects' };
  }
  if (ORACLE_UNSAFE_PACKAGE.test(identifierVisible)) {
    return { classification: 'unknown', reason: 'Oracle network, filesystem, or coordination package is not permitted in read mode' };
  }
  if (hasCrossTargetSqlAccess(identifierVisible)) {
    return { classification: 'unknown', reason: 'Cross-database, linked-server, and database-link access is not permitted' };
  }
  return { classification: 'read', reason: 'Conservative SQL allowlist accepted the statement' };
}

export function classifySqlMutation(sql, engine = 'generic') {
  invariant(typeof sql === 'string' && sql.trim(), 'INVALID_ARGUMENT', 'SQL input is empty');
  const visible = blankQuotedSql(sql, { dialect: engine }).toUpperCase();
  const identifierVisible = blankQuotedSql(sql, { preserveIdentifiers: true, dialect: engine }).toUpperCase();
  const statements = visible.split(';').map((part) => part.trim()).filter(Boolean);
  if (statements.length !== 1) {
    return { classification: 'unknown', reason: 'SQL mutations must contain exactly one statement' };
  }

  const words = statements[0].match(/[A-Z_][A-Z0-9_$#]*/g) || [];
  if (!SQL_MUTATION_PREFIXES.has(words[0])) {
    return {
      classification: 'unknown',
      reason: `Only INSERT, UPDATE, and DELETE are supported; SQL begins with ${words[0] || 'an unknown token'}`,
    };
  }
  const mutationWords = words.filter((word) => SQL_MUTATION_PREFIXES.has(word));
  const postgresUpsert = words[0] === 'INSERT'
    && mutationWords.length === 2
    && mutationWords[1] === 'UPDATE'
    && /\bON\s+CONFLICT\b[\s\S]*\bDO\s+UPDATE\b/.test(statements[0]);
  const forbidden = words.slice(1).find((word) => (
    SQL_MUTATION_FORBIDDEN_WORDS.has(word) && !(postgresUpsert && word === 'DO')
  ));
  if (forbidden) {
    return { classification: 'unknown', reason: `SQL mutation contains unsupported ${forbidden}` };
  }
  if (mutationWords.length !== 1 && !postgresUpsert) {
    return { classification: 'unknown', reason: 'SQL mutation contains more than one data-change statement' };
  }
  if (POSTGRES_STATEFUL_FUNCTION.test(identifierVisible) || ORACLE_UNSAFE_PACKAGE.test(identifierVisible)) {
    return { classification: 'unknown', reason: 'Administrative, network, filesystem, or state-changing functions are not supported' };
  }
  if (SQL_EXTERNAL_ACCESS.test(identifierVisible)) {
    return { classification: 'unknown', reason: 'External or linked-server access is not supported in mutations' };
  }
  if (hasCrossTargetSqlAccess(identifierVisible)) {
    return { classification: 'unknown', reason: 'Cross-database, linked-server, and database-link access is not supported in mutations' };
  }
  return { classification: 'mutation', reason: `Single ${words[0]} statement accepted` };
}

export function requireSqlMutation(input, engine = 'generic') {
  const result = classifySqlMutation(input, engine);
  if (result.classification !== 'mutation') {
    throw new DataDebugError('UNSUPPORTED_OPERATION', result.reason, { classification: result.classification });
  }
  return input;
}

export function parseMongoOperation(input) {
  let operation;
  try {
    operation = typeof input === 'string' ? JSON.parse(input) : input;
  } catch {
    throw new DataDebugError('INVALID_ARGUMENT', 'MongoDB input must be valid JSON');
  }
  invariant(operation && typeof operation === 'object' && !Array.isArray(operation), 'INVALID_ARGUMENT', 'MongoDB input must be a JSON object');
  invariant(typeof operation.operation === 'string', 'INVALID_ARGUMENT', 'MongoDB input requires an operation field');
  return operation;
}

function visitMongoTree(root, visitor) {
  const stack = [{ value: root, depth: 0 }];
  let nodes = 0;
  while (stack.length > 0) {
    const { value, depth } = stack.pop();
    if (!value || typeof value !== 'object') continue;
    invariant(depth <= 128, 'INPUT_TOO_COMPLEX', 'MongoDB operation nesting exceeds 128 levels');
    nodes += 1;
    invariant(nodes <= 100000, 'INPUT_TOO_COMPLEX', 'MongoDB operation contains too many nested values');
    for (const [key, child] of Object.entries(value)) {
      visitor(key, child);
      if (child && typeof child === 'object') stack.push({ value: child, depth: depth + 1 });
    }
  }
}

function hasMongoWriteStage(value) {
  let found = false;
  visitMongoTree(value, (key) => {
    if (key === '$out' || key === '$merge') found = true;
  });
  return found;
}

function inspectMongoReadTree(value, state) {
  visitMongoTree(value, (key, child) => {
    if (key === '$where' || key === '$function' || key === '$accumulator') state.unsafeOperator = key;
    if ((key === '$lookup' || key === '$graphLookup') && child && typeof child === 'object' && typeof child.from === 'string') {
      state.referencedCollections.add(child.from);
    }
    if (key === '$unionWith') {
      if (typeof child === 'string') state.referencedCollections.add(child);
      else if (child && typeof child === 'object' && typeof child.coll === 'string') state.referencedCollections.add(child.coll);
    }
  });
}

export function classifyMongoRead(input, target = undefined) {
  const operation = parseMongoOperation(input);
  if (!MONGO_READ_OPERATIONS.has(operation.operation)) {
    return { classification: 'mutation', reason: `MongoDB operation ${operation.operation} is not on the read allowlist`, operation };
  }
  const allowedFields = MONGO_READ_FIELDS.get(operation.operation);
  const unsupportedFields = Object.keys(operation).filter((key) => !allowedFields.has(key));
  invariant(
    unsupportedFields.length === 0,
    'INVALID_ARGUMENT',
    `Unsupported MongoDB ${operation.operation} field(s): ${unsupportedFields.join(', ')}`,
  );
  if (operation.operation !== 'listCollections') {
    invariant(typeof operation.collection === 'string' && operation.collection, 'INVALID_ARGUMENT', `MongoDB ${operation.operation} requires a collection`);
  }
  for (const field of ['filter', 'projection', 'sort']) {
    if (operation[field] !== undefined) {
      invariant(operation[field] && typeof operation[field] === 'object' && !Array.isArray(operation[field]), 'INVALID_ARGUMENT', `MongoDB ${field} must be an object`);
    }
  }
  if (operation.skip !== undefined) {
    invariant(Number.isSafeInteger(operation.skip) && operation.skip >= 0, 'INVALID_ARGUMENT', 'MongoDB skip must be a non-negative integer');
  }
  if (operation.operation === 'aggregate') {
    invariant(Array.isArray(operation.pipeline), 'INVALID_ARGUMENT', 'MongoDB aggregate requires a pipeline array');
  }
  if (operation.operation === 'distinct') {
    invariant(typeof operation.field === 'string' && operation.field, 'INVALID_ARGUMENT', 'MongoDB distinct requires a field');
  }
  if (operation.operation === 'aggregate' && hasMongoWriteStage(operation.pipeline)) {
    return { classification: 'mutation', reason: 'MongoDB aggregation contains $out or $merge', operation };
  }
  const tree = { unsafeOperator: null, referencedCollections: new Set() };
  inspectMongoReadTree(operation, tree);
  if (tree.unsafeOperator) {
    return { classification: 'unknown', reason: `MongoDB operator ${tree.unsafeOperator} is not permitted in read mode`, operation };
  }
  const allowed = target?.allowedNamespaces || [];
  if (allowed.length > 0 && typeof operation.collection === 'string' && !allowed.includes(operation.collection)) {
    return { classification: 'unknown', reason: `MongoDB collection is outside the target allowlist: ${operation.collection}`, operation };
  }
  const outsideScope = [...tree.referencedCollections].find((collection) => allowed.length > 0 && !allowed.includes(collection));
  if (outsideScope) {
    return { classification: 'unknown', reason: `MongoDB pipeline references collection outside the target allowlist: ${outsideScope}`, operation };
  }
  return { classification: 'read', reason: 'Typed MongoDB read operation accepted', operation };
}

export function requireMongoRead(input, target = undefined) {
  const result = classifyMongoRead(input, target);
  if (result.classification !== 'read') {
    throw new DataDebugError('READ_ONLY_VIOLATION', result.reason, { classification: result.classification });
  }
  return result.operation;
}

export function requireMongoMutation(input, target = undefined) {
  const operation = parseMongoOperation(input);
  invariant(
    MONGO_MUTATION_OPERATIONS.has(operation.operation),
    'UNSUPPORTED_OPERATION',
    `Unsupported MongoDB mutation operation: ${operation.operation}`,
  );
  const allowedFields = MONGO_MUTATION_FIELDS.get(operation.operation);
  const unsupportedFields = Object.keys(operation).filter((key) => !allowedFields.has(key));
  invariant(
    unsupportedFields.length === 0,
    'INVALID_ARGUMENT',
    `Unsupported MongoDB ${operation.operation} field(s): ${unsupportedFields.join(', ')}`,
  );
  invariant(
    typeof operation.collection === 'string' && operation.collection,
    'INVALID_ARGUMENT',
    'MongoDB mutation requires a collection',
  );
  const allowedNamespaces = target?.allowedNamespaces || [];
  invariant(
    allowedNamespaces.length === 0 || allowedNamespaces.includes(operation.collection),
    'NAMESPACE_NOT_ALLOWED',
    `MongoDB collection is outside the target allowlist: ${operation.collection}`,
  );
  if (operation.options !== undefined) {
    invariant(
      operation.options && typeof operation.options === 'object' && !Array.isArray(operation.options),
      'INVALID_ARGUMENT',
      'MongoDB mutation options must be an object',
    );
    const allowed = MONGO_MUTATION_OPTION_KEYS.get(operation.operation) || new Set();
    const unsupported = Object.keys(operation.options).filter((key) => !allowed.has(key));
    invariant(
      unsupported.length === 0,
      'UNSUPPORTED_OPERATION',
      `Unsupported or unsafe MongoDB ${operation.operation} option(s): ${unsupported.join(', ')}`,
    );
  }
  if (operation.operation === 'insertOne') {
    invariant(operation.document && typeof operation.document === 'object' && !Array.isArray(operation.document), 'INVALID_ARGUMENT', 'MongoDB insertOne requires a document object');
  }
  if (operation.operation === 'insertMany') {
    invariant(Array.isArray(operation.documents) && operation.documents.length > 0, 'INVALID_ARGUMENT', 'MongoDB insertMany requires a non-empty documents array');
    invariant(operation.documents.every((document) => document && typeof document === 'object' && !Array.isArray(document)), 'INVALID_ARGUMENT', 'MongoDB insertMany documents must be objects');
  }
  if (['updateOne', 'updateMany'].includes(operation.operation)) {
    invariant(
      Object.hasOwn(operation, 'filter') && operation.filter && typeof operation.filter === 'object' && !Array.isArray(operation.filter),
      'INVALID_ARGUMENT',
      `MongoDB ${operation.operation} requires an explicit filter object`,
    );
    invariant(operation.update && typeof operation.update === 'object', 'INVALID_ARGUMENT', `MongoDB ${operation.operation} requires an update object or pipeline`);
  }
  if (operation.operation === 'replaceOne') {
    invariant(
      Object.hasOwn(operation, 'filter') && operation.filter && typeof operation.filter === 'object' && !Array.isArray(operation.filter),
      'INVALID_ARGUMENT',
      'MongoDB replaceOne requires an explicit filter object',
    );
    invariant(operation.replacement && typeof operation.replacement === 'object' && !Array.isArray(operation.replacement), 'INVALID_ARGUMENT', 'MongoDB replaceOne requires a replacement object');
  }
  if (['deleteOne', 'deleteMany'].includes(operation.operation)) {
    invariant(
      Object.hasOwn(operation, 'filter') && operation.filter && typeof operation.filter === 'object' && !Array.isArray(operation.filter),
      'INVALID_ARGUMENT',
      `MongoDB ${operation.operation} requires an explicit filter object`,
    );
  }
  const tree = { unsafeOperator: null, referencedCollections: new Set() };
  inspectMongoReadTree(operation, tree);
  invariant(!tree.unsafeOperator, 'UNSUPPORTED_OPERATION', `MongoDB operator ${tree.unsafeOperator} is not supported in mutations`);
  invariant(!hasMongoWriteStage(operation), 'UNSUPPORTED_OPERATION', 'MongoDB $out and $merge stages are not supported in mutations');
  return operation;
}

export function parseRedisOperation(input) {
  let operation;
  try {
    operation = typeof input === 'string' ? JSON.parse(input) : input;
  } catch {
    throw new DataDebugError('INVALID_ARGUMENT', 'Redis input must be valid JSON');
  }
  invariant(operation && typeof operation === 'object' && !Array.isArray(operation), 'INVALID_ARGUMENT', 'Redis input must be a JSON object');
  const unsupported = Object.keys(operation).filter((key) => !['operation', 'command', 'arguments'].includes(key));
  invariant(unsupported.length === 0, 'INVALID_ARGUMENT', `Unsupported Redis input field(s): ${unsupported.join(', ')}`);
  invariant(operation.operation === 'command', 'INVALID_ARGUMENT', 'Redis input operation must be command');
  invariant(typeof operation.command === 'string' && operation.command.trim(), 'INVALID_ARGUMENT', 'Redis input requires a command field');
  invariant(operation.arguments && typeof operation.arguments === 'object' && !Array.isArray(operation.arguments), 'INVALID_ARGUMENT', 'Redis input arguments must be an object');
  return {
    operation: 'command',
    command: operation.command.trim().toUpperCase().replace(/\s+/g, ' '),
    arguments: operation.arguments,
  };
}

function redisFields(argumentsValue, allowed) {
  const unsupported = Object.keys(argumentsValue).filter((key) => !allowed.includes(key));
  invariant(unsupported.length === 0, 'INVALID_ARGUMENT', `Unsupported Redis argument field(s): ${unsupported.join(', ')}`);
}

function redisString(argumentsValue, name, { optional = false } = {}) {
  const value = argumentsValue[name];
  if (optional && value === undefined) return undefined;
  invariant(typeof value === 'string' && value.length > 0, 'INVALID_ARGUMENT', `Redis argument ${name} must be a non-empty string`);
  return value;
}

function redisInteger(argumentsValue, name, { optional = false, min, max } = {}) {
  const value = argumentsValue[name];
  if (optional && value === undefined) return undefined;
  invariant(Number.isSafeInteger(value), 'INVALID_ARGUMENT', `Redis argument ${name} must be an integer`);
  if (min !== undefined) invariant(value >= min, 'INVALID_ARGUMENT', `Redis argument ${name} must be at least ${min}`);
  if (max !== undefined) invariant(value <= max, 'INVALID_ARGUMENT', `Redis argument ${name} must be at most ${max}`);
  return value;
}

function redisBoolean(argumentsValue, name, { optional = false } = {}) {
  const value = argumentsValue[name];
  if (optional && value === undefined) return undefined;
  invariant(typeof value === 'boolean', 'INVALID_ARGUMENT', `Redis argument ${name} must be true or false`);
  return value;
}

function redisStringList(argumentsValue, name, maxItems) {
  const value = argumentsValue[name];
  invariant(Array.isArray(value) && value.length > 0, 'INVALID_ARGUMENT', `Redis argument ${name} must be a non-empty array`);
  invariant(value.length <= maxItems, 'INVALID_ARGUMENT', `Redis argument ${name} exceeds the ${maxItems}-item limit`);
  invariant(value.every((item) => typeof item === 'string' && item.length > 0), 'INVALID_ARGUMENT', `Redis argument ${name} must contain non-empty strings`);
  return value;
}

function redisCursor(argumentsValue) {
  const cursor = redisString(argumentsValue, 'cursor');
  invariant(/^\d+$/.test(cursor), 'INVALID_ARGUMENT', 'Redis cursor must be a non-negative decimal string');
  return cursor;
}

function redisKey(target, value) {
  invariant(typeof value === 'string' && value.length > 0, 'INVALID_ARGUMENT', 'Redis key must be a non-empty string');
  if (typeof target?.keyPrefix === 'string' && target.keyPrefix) {
    invariant(value.startsWith(target.keyPrefix), 'NAMESPACE_NOT_ALLOWED', `Redis key is outside the target prefix: ${value}`, { keyPrefix: target.keyPrefix });
  }
  return value;
}

function redisKeys(target, values) {
  for (const value of values) redisKey(target, value);
  return values;
}

function redisCount(argumentsValue, maxRows, { optional = true, max = 1000 } = {}) {
  const value = redisInteger(argumentsValue, 'count', { optional, min: 1, max: Math.min(maxRows, max) });
  return value ?? Math.min(maxRows, 100);
}

function redisRange(argumentsValue, maxRows) {
  const start = redisInteger(argumentsValue, 'start', { min: 0 });
  const stop = redisInteger(argumentsValue, 'stop', { min: start });
  invariant(stop - start + 1 <= maxRows, 'INVALID_ARGUMENT', 'Redis range exceeds max-rows');
  return { start, stop };
}

function redisScanArguments(command, argumentsValue, target, maxRows) {
  const isKeyspaceScan = command === 'SCAN';
  redisFields(argumentsValue, isKeyspaceScan
    ? ['cursor', 'matchSuffix', 'count', 'type']
    : ['key', 'cursor', 'match', 'count']);
  const argv = [command];
  if (!isKeyspaceScan) argv.push(redisKey(target, redisString(argumentsValue, 'key')));
  argv.push(redisCursor(argumentsValue));
  if (isKeyspaceScan) {
    const suffix = redisString(argumentsValue, 'matchSuffix');
    argv.push('MATCH', `${target?.keyPrefix || ''}${suffix}`);
  } else if (argumentsValue.match !== undefined) {
    argv.push('MATCH', redisString(argumentsValue, 'match'));
  }
  argv.push('COUNT', String(redisCount(argumentsValue, maxRows)));
  if (isKeyspaceScan && argumentsValue.type !== undefined) {
    const type = redisString(argumentsValue, 'type').toLowerCase();
    invariant(['string', 'list', 'set', 'zset', 'hash', 'stream'].includes(type), 'INVALID_ARGUMENT', `Unsupported Redis SCAN type: ${type}`);
    argv.push('TYPE', type);
  }
  return argv;
}

function redisAccepted(operation, argv, resultKind = 'scalar', scope = 'key') {
  return {
    classification: 'read',
    reason: 'Typed Redis read command accepted',
    operation: { ...operation, argv, resultKind, scope },
  };
}

export function classifyRedisRead(input, target, { maxRows = 100 } = {}) {
  invariant(Number.isSafeInteger(maxRows) && maxRows >= 1 && maxRows <= 10000, 'INVALID_ARGUMENT', 'Redis maxRows must be between 1 and 10000');
  const operation = parseRedisOperation(input);
  const args = operation.arguments;
  const { command } = operation;

  if (['PING', 'DBSIZE', 'TIME'].includes(command)) {
    redisFields(args, []);
    return redisAccepted(operation, [command], 'scalar', 'server');
  }
  if (command === 'INFO') {
    redisFields(args, ['section']);
    const section = redisString(args, 'section').toLowerCase();
    invariant(REDIS_INFO_SECTIONS.has(section), 'UNSUPPORTED_OPERATION', `Unsupported Redis INFO section: ${section}`);
    return redisAccepted(operation, ['INFO', section], 'info', 'server');
  }
  if (command === 'SCAN') {
    return redisAccepted(operation, redisScanArguments(command, args, target, maxRows), 'scan', 'keyspace');
  }

  const singleKeyCommands = new Set([
    'TYPE', 'TTL', 'PTTL', 'EXPIRETIME', 'PEXPIRETIME', 'GET', 'STRLEN', 'HLEN', 'LLEN',
    'SCARD', 'ZCARD', 'XLEN',
  ]);
  if (singleKeyCommands.has(command)) {
    redisFields(args, ['key']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisAccepted(operation, [command, key], command === 'GET' ? 'get' : 'scalar');
  }
  if (command === 'EXISTS') {
    redisFields(args, ['keys']);
    const keys = redisKeys(target, redisStringList(args, 'keys', maxRows));
    return redisAccepted(operation, [command, ...keys]);
  }
  if (command === 'GETRANGE') {
    redisFields(args, ['key', 'start', 'end']);
    const key = redisKey(target, redisString(args, 'key'));
    const start = redisInteger(args, 'start', { min: 0 });
    const end = redisInteger(args, 'end', { min: start });
    invariant(end - start + 1 <= REDIS_VALUE_PREVIEW_BYTES, 'INVALID_ARGUMENT', `Redis GETRANGE exceeds ${REDIS_VALUE_PREVIEW_BYTES} bytes`);
    return redisAccepted(operation, [command, key, String(start), String(end)]);
  }

  if (['HGET', 'HEXISTS', 'HSTRLEN'].includes(command)) {
    redisFields(args, ['key', 'field']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), redisString(args, 'field')]);
  }
  if (command === 'HMGET') {
    redisFields(args, ['key', 'fields']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), ...redisStringList(args, 'fields', maxRows)], 'array');
  }
  if (command === 'HSCAN') {
    return redisAccepted(operation, redisScanArguments(command, args, target, maxRows), 'hscan');
  }

  if (command === 'LINDEX') {
    redisFields(args, ['key', 'index']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), String(redisInteger(args, 'index'))]);
  }
  if (command === 'LRANGE') {
    redisFields(args, ['key', 'start', 'stop']);
    const key = redisKey(target, redisString(args, 'key'));
    const { start, stop } = redisRange(args, maxRows);
    return redisAccepted(operation, [command, key, String(start), String(stop)], 'array');
  }

  if (command === 'SISMEMBER') {
    redisFields(args, ['key', 'member']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), redisString(args, 'member')]);
  }
  if (command === 'SMISMEMBER') {
    redisFields(args, ['key', 'members']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), ...redisStringList(args, 'members', maxRows)], 'array');
  }
  if (command === 'SSCAN') {
    return redisAccepted(operation, redisScanArguments(command, args, target, maxRows), 'scan');
  }

  if (['ZCOUNT', 'ZLEXCOUNT'].includes(command)) {
    redisFields(args, ['key', 'min', 'max']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), redisString(args, 'min'), redisString(args, 'max')]);
  }
  if (['ZSCORE', 'ZRANK', 'ZREVRANK'].includes(command)) {
    redisFields(args, ['key', 'member']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), redisString(args, 'member')]);
  }
  if (command === 'ZMSCORE') {
    redisFields(args, ['key', 'members']);
    return redisAccepted(operation, [command, redisKey(target, redisString(args, 'key')), ...redisStringList(args, 'members', maxRows)], 'array');
  }
  if (command === 'ZRANGE') {
    redisFields(args, ['key', 'start', 'stop', 'withScores']);
    const key = redisKey(target, redisString(args, 'key'));
    const { start, stop } = redisRange(args, maxRows);
    const withScores = redisBoolean(args, 'withScores', { optional: true }) || false;
    return redisAccepted(
      operation,
      [command, key, String(start), String(stop), ...(withScores ? ['WITHSCORES'] : [])],
      withScores ? 'zrange-with-scores' : 'array',
    );
  }
  if (command === 'ZSCAN') {
    return redisAccepted(operation, redisScanArguments(command, args, target, maxRows), 'zscan');
  }

  if (['XRANGE', 'XREVRANGE'].includes(command)) {
    redisFields(args, ['key', 'start', 'end', 'count']);
    const key = redisKey(target, redisString(args, 'key'));
    const start = redisString(args, 'start');
    const end = redisString(args, 'end');
    const count = redisInteger(args, 'count', { min: 1, max: maxRows });
    const bounds = command === 'XREVRANGE' ? [end, start] : [start, end];
    return redisAccepted(operation, [command, key, ...bounds, 'COUNT', String(count)], 'array');
  }
  if (command === 'XINFO STREAM') {
    redisFields(args, ['key']);
    return redisAccepted(operation, ['XINFO', 'STREAM', redisKey(target, redisString(args, 'key'))], 'array');
  }

  if (command === 'MEMORY USAGE') {
    redisFields(args, ['key', 'samples']);
    const key = redisKey(target, redisString(args, 'key'));
    const samples = redisInteger(args, 'samples', { optional: true, min: 1, max: 64 });
    return redisAccepted(operation, ['MEMORY', 'USAGE', key, ...(samples ? ['SAMPLES', String(samples)] : [])]);
  }
  if (['OBJECT ENCODING', 'OBJECT FREQ', 'OBJECT IDLETIME', 'OBJECT REFCOUNT'].includes(command)) {
    redisFields(args, ['key']);
    const subcommand = command.slice('OBJECT '.length);
    return redisAccepted(operation, ['OBJECT', subcommand, redisKey(target, redisString(args, 'key'))]);
  }
  if (command === 'SLOWLOG LEN') {
    redisFields(args, []);
    return redisAccepted(operation, ['SLOWLOG', 'LEN'], 'scalar', 'server');
  }
  if (command === 'SLOWLOG GET') {
    redisFields(args, ['count']);
    const count = redisInteger(args, 'count', { min: 1, max: Math.min(maxRows, 100) });
    return redisAccepted(operation, ['SLOWLOG', 'GET', String(count)], 'slowlog', 'server');
  }

  return {
    classification: 'unknown',
    reason: `Redis command ${command} is not on the read/debug allowlist`,
    operation,
  };
}

export function requireRedisRead(input, target, options = undefined) {
  const result = classifyRedisRead(input, target, options);
  if (result.classification !== 'read') {
    throw new DataDebugError(
      'UNSUPPORTED_OPERATION',
      result.reason,
      { classification: result.classification },
    );
  }
  return result.operation;
}

function redisMutationAccepted(operation, argv) {
  return {
    classification: 'mutation',
    reason: `Typed Redis ${operation.command} mutation accepted`,
    operation: { ...operation, argv, resultKind: 'mutation', scope: 'key' },
  };
}

function redisRecord(argumentsValue, name, maxItems = 1000) {
  const value = argumentsValue[name];
  invariant(value && typeof value === 'object' && !Array.isArray(value), 'INVALID_ARGUMENT', `Redis argument ${name} must be an object`);
  const entries = Object.entries(value);
  invariant(entries.length > 0 && entries.length <= maxItems, 'INVALID_ARGUMENT', `Redis argument ${name} must contain between 1 and ${maxItems} entries`);
  invariant(entries.every(([key, item]) => key.length > 0 && typeof item === 'string'), 'INVALID_ARGUMENT', `Redis argument ${name} must map non-empty names to strings`);
  return entries;
}

function redisScoreEntries(argumentsValue, name, maxItems = 1000) {
  const value = argumentsValue[name];
  invariant(Array.isArray(value) && value.length > 0 && value.length <= maxItems, 'INVALID_ARGUMENT', `Redis argument ${name} must contain between 1 and ${maxItems} entries`);
  return value.map((entry) => {
    invariant(entry && typeof entry === 'object' && !Array.isArray(entry), 'INVALID_ARGUMENT', `Redis argument ${name} entries must be objects`);
    const unsupported = Object.keys(entry).filter((key) => !['score', 'member'].includes(key));
    invariant(unsupported.length === 0, 'INVALID_ARGUMENT', `Unsupported Redis sorted-set entry field(s): ${unsupported.join(', ')}`);
    invariant(typeof entry.member === 'string' && entry.member.length > 0, 'INVALID_ARGUMENT', 'Redis sorted-set member must be a non-empty string');
    const score = typeof entry.score === 'number' ? String(entry.score) : entry.score;
    invariant(typeof score === 'string' && /^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?$/.test(score), 'INVALID_ARGUMENT', 'Redis sorted-set score must be a finite number');
    return [score, entry.member];
  });
}

export function requireRedisMutation(input, target = undefined) {
  const operation = parseRedisOperation(input);
  const args = operation.arguments;
  const { command } = operation;

  if (command === 'SET') {
    redisFields(args, [
      'key', 'value', 'seconds', 'milliseconds', 'expireAtSeconds', 'expireAtMilliseconds',
      'keepTtl', 'condition', 'get',
    ]);
    const key = redisKey(target, redisString(args, 'key'));
    const value = redisString(args, 'value');
    const expiries = [
      ['EX', redisInteger(args, 'seconds', { optional: true, min: 1 })],
      ['PX', redisInteger(args, 'milliseconds', { optional: true, min: 1 })],
      ['EXAT', redisInteger(args, 'expireAtSeconds', { optional: true, min: 1 })],
      ['PXAT', redisInteger(args, 'expireAtMilliseconds', { optional: true, min: 1 })],
    ].filter(([, expiry]) => expiry !== undefined);
    invariant(expiries.length <= 1, 'INVALID_ARGUMENT', 'Redis SET accepts only one expiry option');
    const keepTtl = redisBoolean(args, 'keepTtl', { optional: true }) || false;
    invariant(!keepTtl || expiries.length === 0, 'INVALID_ARGUMENT', 'Redis SET keepTtl cannot be combined with an expiry');
    const condition = redisString(args, 'condition', { optional: true })?.toUpperCase();
    invariant(condition === undefined || ['NX', 'XX'].includes(condition), 'INVALID_ARGUMENT', 'Redis SET condition must be NX or XX');
    const get = redisBoolean(args, 'get', { optional: true }) || false;
    const expiry = expiries[0] || [];
    return redisMutationAccepted(operation, [
      command, key, value,
      ...expiry.flatMap((item) => [String(item)]),
      ...(keepTtl ? ['KEEPTTL'] : []),
      ...(condition ? [condition] : []),
      ...(get ? ['GET'] : []),
    ]).operation;
  }

  if (['DEL', 'UNLINK'].includes(command)) {
    redisFields(args, ['keys']);
    const keys = redisKeys(target, redisStringList(args, 'keys', 1000));
    return redisMutationAccepted(operation, [command, ...keys]).operation;
  }

  const expiryArguments = {
    EXPIRE: 'seconds',
    PEXPIRE: 'milliseconds',
    EXPIREAT: 'unixTimeSeconds',
    PEXPIREAT: 'unixTimeMilliseconds',
  };
  if (expiryArguments[command]) {
    const timeField = expiryArguments[command];
    redisFields(args, ['key', timeField]);
    const key = redisKey(target, redisString(args, 'key'));
    const value = redisInteger(args, timeField, { min: 0 });
    return redisMutationAccepted(operation, [command, key, String(value)]).operation;
  }
  if (command === 'PERSIST') {
    redisFields(args, ['key']);
    return redisMutationAccepted(operation, [command, redisKey(target, redisString(args, 'key'))]).operation;
  }

  if (command === 'HSET') {
    redisFields(args, ['key', 'entries']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisMutationAccepted(operation, [command, key, ...redisRecord(args, 'entries').flat()]).operation;
  }
  if (command === 'HDEL') {
    redisFields(args, ['key', 'fields']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisMutationAccepted(operation, [command, key, ...redisStringList(args, 'fields', 1000)]).operation;
  }

  if (['LPUSH', 'RPUSH'].includes(command)) {
    redisFields(args, ['key', 'values']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisMutationAccepted(operation, [command, key, ...redisStringList(args, 'values', 1000)]).operation;
  }
  if (['LPOP', 'RPOP'].includes(command)) {
    redisFields(args, ['key', 'count']);
    const key = redisKey(target, redisString(args, 'key'));
    const count = redisInteger(args, 'count', { optional: true, min: 1, max: 1000 });
    return redisMutationAccepted(operation, [command, key, ...(count === undefined ? [] : [String(count)])]).operation;
  }
  if (command === 'LTRIM') {
    redisFields(args, ['key', 'start', 'stop']);
    const key = redisKey(target, redisString(args, 'key'));
    const start = redisInteger(args, 'start');
    const stop = redisInteger(args, 'stop');
    return redisMutationAccepted(operation, [command, key, String(start), String(stop)]).operation;
  }

  if (['SADD', 'SREM'].includes(command)) {
    redisFields(args, ['key', 'members']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisMutationAccepted(operation, [command, key, ...redisStringList(args, 'members', 1000)]).operation;
  }
  if (command === 'ZADD') {
    redisFields(args, ['key', 'entries', 'condition', 'change']);
    const key = redisKey(target, redisString(args, 'key'));
    const condition = redisString(args, 'condition', { optional: true })?.toUpperCase();
    invariant(condition === undefined || ['NX', 'XX'].includes(condition), 'INVALID_ARGUMENT', 'Redis ZADD condition must be NX or XX');
    const change = redisBoolean(args, 'change', { optional: true }) || false;
    const entries = redisScoreEntries(args, 'entries').flat();
    return redisMutationAccepted(operation, [command, key, ...(condition ? [condition] : []), ...(change ? ['CH'] : []), ...entries]).operation;
  }
  if (command === 'ZREM') {
    redisFields(args, ['key', 'members']);
    const key = redisKey(target, redisString(args, 'key'));
    return redisMutationAccepted(operation, [command, key, ...redisStringList(args, 'members', 1000)]).operation;
  }

  throw new DataDebugError('UNSUPPORTED_OPERATION', `Redis command ${command} is not on the mutation allowlist`);
}

export function resolveTransactionMode(engine, input, requested = 'auto') {
  invariant(['auto', 'always', 'never'].includes(requested), 'INVALID_ARGUMENT', 'Transaction mode must be auto, always, or never');
  if (requested === 'never') return 'never';
  if (engine !== 'postgresql') {
    invariant(requested !== 'always', 'UNSUPPORTED_OPERATION', `Forced transactions are not supported for ${engine}`);
    return 'never';
  }
  if (requested === 'always') return 'always';

  const visible = blankQuotedSql(input, { dialect: engine }).toUpperCase();
  const requiresTopLevelExecution = [
    /\b(?:CREATE|DROP)\s+DATABASE\b/,
    /\b(?:CREATE|DROP)\s+TABLESPACE\b/,
    /\bALTER\s+SYSTEM\b/,
    /\bVACUUM\b/,
    /\b(?:CREATE|DROP|REINDEX)\b[^;]*\bCONCURRENTLY\b/,
    /\b(?:CALL|DO)\b/,
    /\b(?:BEGIN|START\s+TRANSACTION|COMMIT|ROLLBACK)\b/,
  ];
  return requiresTopLevelExecution.some((pattern) => pattern.test(visible)) ? 'never' : 'always';
}

export function requireReadOperation(engine, input, target = undefined, options = undefined) {
  if (engine === 'redis') return requireRedisRead(input, target, options);
  const result = engine === 'mongodb' ? classifyMongoRead(input, target) : classifySqlRead(input, engine);
  if (result.classification !== 'read') {
    throw new DataDebugError('READ_ONLY_VIOLATION', result.reason, { classification: result.classification });
  }
  return result.operation || input;
}
