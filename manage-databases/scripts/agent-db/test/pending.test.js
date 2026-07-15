import assert from 'node:assert/strict';
import { access, mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { runtimePaths } from '../src/config/paths.js';
import { atomicWriteJson } from '../src/core/fs.js';
import { PendingStore } from '../src/security/pending.js';
import { Vault } from '../src/security/vault.js';

function memoryKeyring() {
  const values = new Map();
  return {
    name: 'memory-test-keyring',
    async get(account) { return values.get(account) || null; },
    async set(account, value) { values.set(account, value); },
  };
}

async function fixture(t, options = {}) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-pending-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const paths = runtimePaths({ AGENT_DB_HOME: root });
  const vault = new Vault(paths, { keyring: memoryKeyring() });
  const pending = new PendingStore(paths, vault, options);
  pending.testVault = vault;
  return pending;
}

const project = { id: 'project-1', name: 'Payments', bindingRevision: 'binding-1' };
const target = {
  id: 'primary', engine: 'postgresql', environment: 'production', targetFingerprint: 'fingerprint-1',
  credentials: { mutation: 'credential-1' },
};
const verifiedIdentity = { database: 'payments', principal: 'dba', serverIdentity: 'db-01' };

function prepare(pending, rawInput, operationType = 'postgresql.sql') {
  return pending.prepare({ project, target, rawInput, operationType, verifiedIdentity, transactionMode: 'always' });
}

async function mintTestApproval(pending, plan) {
  const scope = {
    kind: 'mutation-approval',
    planId: plan.planId,
    projectId: plan.projectId,
    targetId: plan.targetId,
    approvalHash: plan.approvalHash,
  };
  const approval = {
    formatVersion: 1,
    ...scope,
    projectBindingRevision: plan.projectBindingRevision,
    targetFingerprint: plan.targetFingerprint,
    credentialId: target.credentials.mutation,
    approvedAt: new Date(pending.now()).toISOString(),
    expiresAt: plan.expiresAt,
  };
  await atomicWriteJson(pending.approvalFile(plan.planId), {
    formatVersion: 1,
    ...scope,
    envelope: await pending.testVault.encryptObject(approval, scope),
  });
  return pending.show(plan.planId, project, target);
}

test('mutation plan exposes the exact preview and is consumable once', async (t) => {
  const pending = await fixture(t);
  const rawInput = "UPDATE invoices SET status = 'paid' WHERE id = 42";
  const prepared = await prepare(pending, rawInput);
  assert.equal(prepared.operationPreview.exact, rawInput);
  assert.deepEqual(prepared.approval, { approved: false });
  await assert.rejects(pending.consume(prepared.planId, project, target), { code: 'MUTATION_APPROVAL_REQUIRED' });
  const approved = await mintTestApproval(pending, prepared);
  assert.equal(approved.approval.approved, true);
  const consumed = await pending.consume(prepared.planId, project, target);
  assert.equal(consumed.rawInput, rawInput);
  await assert.rejects(
    pending.consume(prepared.planId, project, target),
    { code: 'PLAN_NOT_FOUND' },
  );
});

test('execution remains blocked until a separate approval receipt exists', async (t) => {
  const pending = await fixture(t);
  const prepared = await prepare(pending, 'DELETE FROM jobs');
  await assert.rejects(pending.consume(prepared.planId, project, target), { code: 'MUTATION_APPROVAL_REQUIRED' });
  await mintTestApproval(pending, prepared);
  assert.equal((await pending.consume(prepared.planId, project, target)).planId, prepared.planId);
});

test('approval cannot be minted from a captured non-TTY process', {
  skip: Boolean(process.stdin.isTTY || process.stderr.isTTY || process.stdout.isTTY),
}, async (t) => {
  const pending = await fixture(t);
  const prepared = await prepare(pending, 'DELETE FROM jobs WHERE id = 9');
  await assert.rejects(pending.approve(prepared.planId, project, target), { code: 'LOCAL_TTY_REQUIRED' });
  await assert.rejects(pending.consume(prepared.planId, project, target), { code: 'MUTATION_APPROVAL_REQUIRED' });
});

test('confirmation phrase binds the whole plan, not only the raw operation', async (t) => {
  const pending = await fixture(t);
  const rawInput = 'UPDATE jobs SET status = 1';
  const first = await pending.prepare({
    project, target, rawInput, operationType: 'postgresql.sql', verifiedIdentity, transactionMode: 'always',
  });
  const second = await pending.prepare({
    project, target, rawInput, operationType: 'postgresql.sql',
    verifiedIdentity: { ...verifiedIdentity, serverIdentity: 'db-02' }, transactionMode: 'never',
  });
  assert.equal(first.operationHash, second.operationHash);
  assert.notEqual(first.approvalHash, second.approvalHash);
  assert.notEqual(first.confirmationPhrase, second.confirmationPhrase);
  assert.match(first.confirmationPhrase, /^MUTATE primary [0-9a-f]{12}$/);
});

test('plan expires and changes in target or credential invalidate it', async (t) => {
  let now = 1_700_000_000_000;
  const pending = await fixture(t, { now: () => now, ttlMs: 1000 });
  const first = await prepare(pending, 'DROP TABLE old_data');
  now += 1001;
  await assert.rejects(pending.show(first.planId, project, target), { code: 'PLAN_EXPIRED' });

  const second = await prepare(pending, 'DROP TABLE old_data');
  await mintTestApproval(pending, second);
  const changed = { ...target, credentials: { mutation: 'credential-2' } };
  await assert.rejects(
    pending.consume(second.planId, project, changed),
    { code: 'PLAN_CHANGED' },
  );

  const third = await prepare(pending, 'DROP TABLE old_data');
  await mintTestApproval(pending, third);
  await assert.rejects(
    pending.consume(third.planId, { ...project, bindingRevision: 'binding-2' }, target),
    { code: 'PLAN_CHANGED' },
  );
});

test('cancel atomically invalidates both plan and approval', async (t) => {
  const pending = await fixture(t);
  const prepared = await prepare(pending, 'DELETE FROM jobs WHERE id = 7');
  await mintTestApproval(pending, prepared);
  await pending.cancel(prepared.planId, project, target);
  await assert.rejects(pending.show(prepared.planId, project, target), { code: 'PLAN_NOT_FOUND' });
  await assert.rejects(pending.consume(prepared.planId, project, target), { code: 'PLAN_NOT_FOUND' });
});

test('plan ids cannot traverse outside the pending directory', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'agent-db-pending-traversal-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const paths = runtimePaths({ AGENT_DB_HOME: root });
  const victim = path.join(root, 'victim.json.enc');
  await writeFile(victim, 'must remain');
  const pending = new PendingStore(paths, new Vault(paths, { keyring: memoryKeyring() }));
  await assert.rejects(
    pending.consume('../victim', project, target),
    { code: 'INVALID_ARGUMENT' },
  );
  await access(victim);
});
