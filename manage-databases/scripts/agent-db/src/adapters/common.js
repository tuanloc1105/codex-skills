import { AgentDbError, invariant } from '../core/errors.js';

export function redactMessage(error, secrets = []) {
  let message = error instanceof Error ? error.message : String(error);
  for (const secret of secrets.filter(Boolean)) {
    message = message.split(secret).join('[REDACTED]');
  }
  return message.replace(/(password|pwd)\s*=\s*[^;\s]+/gi, '$1=[REDACTED]');
}

export function databaseError(error, credential, code = 'DATABASE_ERROR') {
  if (error instanceof AgentDbError) return error;
  return new AgentDbError(code, redactMessage(error, [credential?.secret]));
}

export function mutationDatabaseError(error, credential, outcomeMayBeUnknown) {
  if (error instanceof AgentDbError) return error;
  if (!outcomeMayBeUnknown) return databaseError(error, credential);
  return new AgentDbError(
    'MUTATION_OUTCOME_UNKNOWN',
    `The database operation was sent but its final outcome is not safe to infer: ${redactMessage(error, [credential?.secret])}`,
    { requiresVerification: true },
  );
}

export function verifyIdentity(target, identity) {
  const expectedDatabase = target.engine === 'oracle'
    ? target.connection.service || target.connection.database
    : target.connection.database;
  const sameDatabase = target.engine === 'oracle'
    ? identity.database?.toLowerCase() === expectedDatabase?.toLowerCase()
    : identity.database === expectedDatabase;
  invariant(sameDatabase, 'TARGET_IDENTITY_MISMATCH', 'Connected database does not match the configured target', {
    expectedDatabase,
    actualDatabase: identity.database,
  });
  if (target.expectedServerIdentity) {
    invariant(
      identity.serverIdentity === target.expectedServerIdentity,
      'TARGET_IDENTITY_MISMATCH',
      'Connected server identity does not match the configured target',
      { expected: target.expectedServerIdentity, actual: identity.serverIdentity },
    );
  }
  return identity;
}

export function verifyPlannedIdentity(expected, actual) {
  invariant(expected && typeof expected === 'object', 'PLAN_CHANGED', 'Mutation plan has no verified database identity');
  for (const key of ['database', 'principal', 'serverIdentity']) {
    invariant(
      expected[key] === actual[key],
      'TARGET_IDENTITY_MISMATCH',
      `Connected ${key} changed after mutation preview`,
      { key, expected: expected[key], actual: actual[key] },
    );
  }
  return actual;
}

export function assertMutationApprovalActive(expiresAt, now = Date.now()) {
  const expiry = Date.parse(expiresAt);
  invariant(Number.isFinite(expiry) && expiry > now, 'PLAN_EXPIRED', 'Mutation approval expired before the database operation was sent');
}

export function assertAllowedNamespace(target, namespace) {
  const allowed = target.allowedNamespaces || [];
  if (allowed.length > 0) {
    invariant(allowed.includes(namespace), 'NAMESPACE_NOT_ALLOWED', `Namespace is not allowed for this target: ${namespace}`, { allowedNamespaces: allowed });
  }
}

export function elapsed(startedAt) {
  return Math.max(0, Date.now() - startedAt);
}
