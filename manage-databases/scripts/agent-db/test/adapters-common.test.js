import assert from 'node:assert/strict';
import test from 'node:test';
import { assertMutationApprovalActive, mutationDatabaseError, verifyIdentity, verifyPlannedIdentity } from '../src/adapters/common.js';

test('Oracle identity uses the configured service and ignores service-name case', () => {
  const target = {
    engine: 'oracle',
    connection: { database: 'ORCL', service: 'PaymentsPDB' },
    expectedServerIdentity: 'oracle-01',
  };
  const identity = { database: 'paymentspdb', principal: 'READER', serverIdentity: 'oracle-01' };
  assert.equal(verifyIdentity(target, identity), identity);
});

test('planned mutation identity must still match immediately before execution', () => {
  const expected = { database: 'payments', principal: 'dba', serverIdentity: 'db-01' };
  assert.equal(verifyPlannedIdentity(expected, { ...expected, version: 'new-version' }).database, 'payments');
  assert.throws(
    () => verifyPlannedIdentity(expected, { ...expected, serverIdentity: 'db-02' }),
    { code: 'TARGET_IDENTITY_MISMATCH' },
  );
  assert.throws(() => verifyPlannedIdentity(undefined, expected), { code: 'PLAN_CHANGED' });
});

test('mutation errors become outcome-unknown only after an operation may have been sent', () => {
  const credential = { secret: 'top-secret' };
  const beforeSend = mutationDatabaseError(new Error('login failed for top-secret'), credential, false);
  assert.equal(beforeSend.code, 'DATABASE_ERROR');
  assert.doesNotMatch(beforeSend.message, /top-secret/);
  const afterSend = mutationDatabaseError(new Error('socket closed for top-secret'), credential, true);
  assert.equal(afterSend.code, 'MUTATION_OUTCOME_UNKNOWN');
  assert.equal(afterSend.details.requiresVerification, true);
  assert.doesNotMatch(afterSend.message, /top-secret/);
});

test('mutation approval must still be active immediately before send', () => {
  assert.doesNotThrow(() => assertMutationApprovalActive('2026-01-01T00:00:01.000Z', Date.parse('2026-01-01T00:00:00.000Z')));
  assert.throws(
    () => assertMutationApprovalActive('2026-01-01T00:00:00.000Z', Date.parse('2026-01-01T00:00:00.000Z')),
    { code: 'PLAN_EXPIRED' },
  );
  assert.throws(() => assertMutationApprovalActive(undefined), { code: 'PLAN_EXPIRED' });
});
