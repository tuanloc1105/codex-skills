import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { PlanStore } from '../src/security/plans.js';

const target = {
  engine: 'postgresql',
  host: 'db.internal',
  port: 5432,
  database: 'application',
  targetFingerprint: 'target-fingerprint',
};
const identity = { database: 'application', principal: 'writer', serverIdentity: 'db.internal:5432' };

async function storeFixture(t, options = {}) {
  const stateRoot = await mkdtemp(path.join(os.tmpdir(), 'data-debug-plan-'));
  t.after(() => rm(stateRoot, { recursive: true, force: true }));
  return { stateRoot, store: new PlanStore({ stateRoot, ...options }) };
}

test('mutation plan is non-secret, short-lived, hash-bound, and single-use', async (t) => {
  let now = Date.parse('2026-07-26T00:00:00.000Z');
  const { stateRoot, store } = await storeFixture(t, { now: () => now, ttlMs: 60_000 });
  const plan = await store.prepare({
    publicTarget: target,
    rawInput: "UPDATE jobs SET status = 'done' WHERE id = 1",
    operationType: 'postgresql.update',
    transactionMode: 'always',
    expectedIdentity: identity,
  });
  assert.match(plan.planId, /^[0-9a-f-]{36}$/);
  assert.equal(plan.status, 'pending');
  assert.equal(plan.expiresAt, '2026-07-26T00:01:00.000Z');
  assert.equal(JSON.stringify(plan).includes('password'), false);

  await assert.rejects(store.consume(plan.planId, 'wrong-hash', { targetFingerprint: 'target-fingerprint' }), { code: 'USER_APPROVAL_REQUIRED' });
  const consumed = await store.consume(plan.planId, plan.approvalHash, { targetFingerprint: 'target-fingerprint' });
  assert.equal(consumed.status, 'consumed');
  await assert.rejects(store.consume(plan.planId, plan.approvalHash, { targetFingerprint: 'target-fingerprint' }), { code: 'PLAN_ALREADY_USED' });

  const stored = JSON.parse(await readFile(path.join(stateRoot, 'plans', `${plan.planId}.json`), 'utf8'));
  assert.equal(stored.status, 'pending');
  const tombstone = JSON.parse(await readFile(path.join(stateRoot, 'plans', `${plan.planId}.json.consumed`), 'utf8'));
  assert.equal(tombstone.status, 'consumed');
  assert.equal(tombstone.approvalHash, plan.approvalHash);
  now += 1;
});

test('concurrent mutation consumption creates exactly one durable tombstone', async (t) => {
  const { store } = await storeFixture(t);
  const plan = await store.prepare({
    publicTarget: target,
    rawInput: 'DELETE FROM jobs WHERE id = 9',
    operationType: 'postgresql.delete',
    transactionMode: 'always',
    expectedIdentity: identity,
  });
  const results = await Promise.allSettled([
    store.consume(plan.planId, plan.approvalHash, { targetFingerprint: 'target-fingerprint' }),
    store.consume(plan.planId, plan.approvalHash, { targetFingerprint: 'target-fingerprint' }),
  ]);
  assert.equal(results.filter(({ status }) => status === 'fulfilled').length, 1);
  const rejected = results.find(({ status }) => status === 'rejected');
  assert.equal(rejected.reason.code, 'PLAN_ALREADY_USED');
});

test('mutation plan rejects target changes, expiry, and payload tampering', async (t) => {
  let now = Date.parse('2026-07-26T00:00:00.000Z');
  const { stateRoot, store } = await storeFixture(t, { now: () => now, ttlMs: 10 });
  const prepared = await store.prepare({
    publicTarget: target,
    rawInput: 'DELETE FROM jobs WHERE id = 1',
    operationType: 'postgresql.delete',
    transactionMode: 'always',
    expectedIdentity: identity,
  });
  await assert.rejects(
    store.consume(prepared.planId, prepared.approvalHash, { targetFingerprint: 'different' }),
    { code: 'TARGET_CHANGED' },
  );
  now += 11;
  await assert.rejects(
    store.consume(prepared.planId, prepared.approvalHash, { targetFingerprint: 'target-fingerprint' }),
    { code: 'PLAN_EXPIRED' },
  );

  now = Date.parse('2026-07-26T00:00:00.000Z');
  const tampered = await store.prepare({
    publicTarget: target,
    rawInput: 'DELETE FROM jobs WHERE id = 2',
    operationType: 'postgresql.delete',
    transactionMode: 'always',
    expectedIdentity: identity,
  });
  const file = path.join(stateRoot, 'plans', `${tampered.planId}.json`);
  const contents = JSON.parse(await readFile(file, 'utf8'));
  contents.rawInput = 'DELETE FROM jobs';
  await writeFile(file, `${JSON.stringify(contents)}\n`, { mode: 0o600 });
  await assert.rejects(store.load(tampered.planId), { code: 'PLAN_CHANGED' });
});
