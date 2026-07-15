import { createHash } from 'node:crypto';
import { AgentDbError, invariant } from '../core/errors.js';

const SQL_READ_PREFIXES = new Set(['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']);
const SQL_BLOCKED_WORDS = new Set([
  'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE',
  'GRANT', 'REVOKE', 'CALL', 'EXEC', 'EXECUTE', 'DECLARE', 'BEGIN', 'DO', 'COPY', 'LOAD',
  'LOCK', 'VACUUM', 'REINDEX', 'BACKUP', 'RESTORE', 'KILL', 'SHUTDOWN', 'ATTACH', 'DETACH',
  'DENY', 'DBCC', 'CHECKPOINT', 'USE', 'SET', 'WAITFOR', 'WRITETEXT', 'UPDATETEXT',
  'RECONFIGURE', 'ENABLE', 'DISABLE', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SAVE',
  'RECEIVE', 'SEND', 'OPEN', 'OPENROWSET', 'OPENQUERY', 'OPENDATASOURCE',
]);
const MONGO_READ_OPERATIONS = new Set([
  'find', 'findOne', 'aggregate', 'countDocuments', 'estimatedDocumentCount', 'distinct',
  'listCollections', 'listIndexes',
]);
const MONGO_MUTATION_OPERATIONS = new Set([
  'command', 'createCollection', 'dropCollection', 'insertOne', 'insertMany', 'updateOne',
  'updateMany', 'replaceOne', 'deleteOne', 'deleteMany', 'createIndex', 'dropIndex',
]);

const MONGO_MUTATION_OPTION_KEYS = new Map([
  ['createCollection', new Set([
    'capped', 'size', 'max', 'validator', 'validationLevel', 'validationAction',
    'storageEngine', 'indexOptionDefaults', 'collation', 'expireAfterSeconds',
    'changeStreamPreAndPostImages', 'clusteredIndex', 'comment',
  ])],
  ['dropCollection', new Set(['comment'])],
  ['insertOne', new Set(['bypassDocumentValidation', 'forceServerObjectId', 'checkKeys', 'ignoreUndefined', 'comment'])],
  ['insertMany', new Set(['ordered', 'bypassDocumentValidation', 'forceServerObjectId', 'checkKeys', 'ignoreUndefined', 'comment'])],
  ['updateOne', new Set(['upsert', 'arrayFilters', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment', 'sort'])],
  ['updateMany', new Set(['upsert', 'arrayFilters', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment'])],
  ['replaceOne', new Set(['upsert', 'bypassDocumentValidation', 'collation', 'hint', 'let', 'comment', 'sort'])],
  ['deleteOne', new Set(['collation', 'hint', 'let', 'comment'])],
  ['deleteMany', new Set(['collation', 'hint', 'let', 'comment'])],
  ['createIndex', new Set([
    'name', 'unique', 'background', 'sparse', 'expireAfterSeconds', 'storageEngine',
    'version', 'default_language', 'language_override', 'textIndexVersion', 'weights',
    '2dsphereIndexVersion', 'bits', 'min', 'max', 'bucketSize', 'partialFilterExpression',
    'collation', 'wildcardProjection', 'hidden', 'commitQuorum', 'comment',
  ])],
  ['dropIndex', new Set(['comment'])],
]);

function blankQuotedSql(sql, { preserveIdentifiers = false } = {}) {
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
      const end = sql.indexOf('*/', index + 2);
      invariant(end >= 0, 'READ_ONLY_VIOLATION', 'Unterminated SQL block comment');
      output += ' '.repeat(end + 2 - index);
      index = end + 2;
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
    if (character === '\'' || character === '"' || character === '`' || character === '[') {
      const closing = character === '[' ? ']' : character;
      let cursor = index + 1;
      while (cursor < sql.length) {
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
        const inner = sql.slice(index + 1, cursor - 1).split(closing + closing).join(closing);
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

export function classifySqlRead(sql) {
  invariant(typeof sql === 'string' && sql.trim(), 'INVALID_ARGUMENT', 'SQL input is empty');
  const visible = blankQuotedSql(sql).toUpperCase();
  const identifierVisible = blankQuotedSql(sql, { preserveIdentifiers: true }).toUpperCase();
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
  if (/\b(?:PG_TERMINATE_BACKEND|PG_CANCEL_BACKEND|PG_RELOAD_CONF|PG_ROTATE_LOGFILE|PG_CREATE_RESTORE_POINT|PG_SWITCH_WAL|PG_WAL_REPLAY_PAUSE|PG_WAL_REPLAY_RESUME|PG_ADVISORY_(?:XACT_)?LOCK(?:_SHARED)?|PG_ADVISORY_UNLOCK(?:_ALL|_SHARED)?|PG_NOTIFY|PG_LOGICAL_EMIT_MESSAGE|SET_CONFIG|SETVAL|LO_IMPORT|LO_EXPORT|LO_UNLINK|DBLINK[A-Z0-9_]*)\s*\(/.test(identifierVisible)) {
    return { classification: 'mutation', reason: 'SQL calls a PostgreSQL function with administrative or state-changing effects' };
  }
  if (/\b(?:UTL_HTTP|UTL_TCP|UTL_SMTP|UTL_FILE|DBMS_LDAP|DBMS_LOCK|DBMS_PIPE|DBMS_ALERT|HTTPURITYPE)\b/.test(identifierVisible)) {
    return { classification: 'unknown', reason: 'Oracle network, filesystem, or coordination package is not permitted in read mode' };
  }
  return { classification: 'read', reason: 'Conservative SQL allowlist accepted the statement' };
}

export function parseMongoOperation(input) {
  let operation;
  try {
    operation = typeof input === 'string' ? JSON.parse(input) : input;
  } catch {
    throw new AgentDbError('INVALID_ARGUMENT', 'MongoDB input must be valid JSON');
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
    throw new AgentDbError('MUTATION_CONFIRMATION_REQUIRED', result.reason, { classification: result.classification });
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
  invariant(
    operation.operation !== 'command' || (target?.allowedNamespaces || []).length === 0,
    'NAMESPACE_NOT_ALLOWED',
    'Raw MongoDB commands require a separate target without a collection allowlist',
  );
  if (operation.operation === 'command') {
    invariant(
      operation.command?.writeConcern?.w !== 0,
      'UNSUPPORTED_OPERATION',
      'Unacknowledged MongoDB commands are not supported',
    );
  } else if (operation.options !== undefined) {
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
  return operation;
}

function hasSensitiveMongoField(value) {
  const sensitive = /(?:password|passwd|(?:^|[._-])pwd(?:$|[._-])|(?:^|[._-])auth(?:entication)?(?:$|[._-])|(?:^|[._-])login(?:$|[._-])|secret|token|api[_-]?key|private[_-]?key|access[_-]?key|encryption[_-]?key|signing[_-]?key|connection[_-]?string|credential)/i;
  const credentialUri = /:\/\/[^\s/:@]+:[^\s/@]+@/;
  let found = typeof value === 'string' && (credentialUri.test(value) || sensitive.test(value));
  visitMongoTree(value, (key, child) => {
    if (sensitive.test(key) || (typeof child === 'string' && (credentialUri.test(child) || sensitive.test(child)))) found = true;
  });
  return found;
}

export function assertNoEmbeddedSecret(engine, input) {
  if (engine === 'mongodb') {
    invariant(!hasSensitiveMongoField(parseMongoOperation(input)), 'SECRET_IN_OPERATION', 'Mutation payload appears to contain a credential or secret; use a local database-native secret workflow');
    return;
  }
  const sql = String(input);
  const visible = blankQuotedSql(sql, { preserveIdentifiers: true });
  const credentialAssignment = /\b(?:PASSWORD|PASSWD|PWD|IDENTIFIED\s+BY|AUTH(?:ENTICATION)?|LOGIN|SP_ADDLOGIN|SP_PASSWORD|TOKEN|API[_-]?KEY|SECRET|PRIVATE[_-]?KEY|ACCESS[_-]?KEY|ENCRYPTION[_-]?KEY|SIGNING[_-]?KEY|CONNECTION[_-]?STRING)\b/i;
  const credentialUri = /:\/\/[^\s/:@]+:[^\s/@]+@/;
  invariant(
    !credentialAssignment.test(visible) && !credentialAssignment.test(sql) && !credentialUri.test(sql),
    'SECRET_IN_OPERATION',
    'Mutation payload appears to contain a credential or secret; use a local database-native secret workflow',
  );
}

export function resolveTransactionMode(engine, input, requested = 'auto') {
  invariant(['auto', 'always', 'never'].includes(requested), 'INVALID_ARGUMENT', 'Transaction mode must be auto, always, or never');
  if (requested === 'never') return 'never';
  if (engine !== 'postgresql') {
    invariant(requested !== 'always', 'UNSUPPORTED_OPERATION', `Forced transactions are not supported for ${engine}`);
    return 'never';
  }
  if (requested === 'always') return 'always';

  const visible = blankQuotedSql(input).toUpperCase();
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

export function requireReadOperation(engine, input, target = undefined) {
  const result = engine === 'mongodb' ? classifyMongoRead(input, target) : classifySqlRead(input);
  if (result.classification !== 'read') {
    throw new AgentDbError('MUTATION_CONFIRMATION_REQUIRED', result.reason, { classification: result.classification });
  }
  return result.operation || input;
}

export function operationHash(input) {
  return createHash('sha256').update(typeof input === 'string' ? input : JSON.stringify(input)).digest('hex');
}
