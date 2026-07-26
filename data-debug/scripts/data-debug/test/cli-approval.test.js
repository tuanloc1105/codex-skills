import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { runCli } from '../src/cli.js';
import { PlanStore } from '../src/security/plans.js';

function capture() {
  return {
    value: '',
    write(chunk) { this.value += chunk; },
  };
}

const connection = [
  '--engine', 'postgresql', '--host', 'db.internal', '--database', 'application', '--username', 'writer',
];
const identity = { database: 'application', principal: 'writer', serverIdentity: 'db.internal:5432' };

test('CLI preview requires the exact approval hash and executes one single-use plan', async (t) => {
  const stateRoot = await mkdtemp(path.join(os.tmpdir(), 'data-debug-cli-plan-'));
  t.after(() => rm(stateRoot, { recursive: true, force: true }));
  const planStore = new PlanStore({ stateRoot });
  const executions = [];
  const adapterFactory = async (_target, credential) => ({
    async test() {
      assert.equal(credential.mode, 'mutation');
      return { identity };
    },
    async executeMutation(input, options) {
      executions.push({ input, options });
      return { identity, result: { rowsAffected: 1 }, transactional: true };
    },
  });
  const sql = "UPDATE jobs SET status = 'done' WHERE id = 42";
  const previewOut = capture();
  const previewErr = capture();
  const previewStatus = await runCli(
    ['mutation', 'preview', ...connection, '--text', sql],
    { stdout: previewOut, stderr: previewErr, planStore, adapterFactory },
  );
  assert.equal(previewStatus, 0, previewErr.value);
  assert.equal(executions.length, 0);
  const preview = JSON.parse(previewOut.value);
  const { plan } = preview.data;
  assert.equal(plan.operation, sql);
  assert.equal(plan.expectedIdentity.principal, 'writer');
  assert.equal(plan.transactionMode, 'always');
  assert.equal(preview.data.approvalRequired, true);

  const wrongOut = capture();
  const wrongErr = capture();
  const wrongStatus = await runCli(
    ['mutation', 'execute', ...connection, '--plan', plan.planId, '--approved', 'wrong-hash'],
    { stdout: wrongOut, stderr: wrongErr, planStore, adapterFactory },
  );
  assert.equal(wrongStatus, 1);
  assert.equal(JSON.parse(wrongErr.value).error.code, 'USER_APPROVAL_REQUIRED');
  assert.equal(executions.length, 0);

  const executeOut = capture();
  const executeErr = capture();
  const executeStatus = await runCli(
    ['mutation', 'execute', ...connection, '--plan', plan.planId, '--approved', plan.approvalHash],
    { stdout: executeOut, stderr: executeErr, planStore, adapterFactory },
  );
  assert.equal(executeStatus, 0, executeErr.value);
  assert.equal(executions.length, 1);
  assert.equal(executions[0].input, sql);
  assert.deepEqual(executions[0].options.expectedIdentity, identity);
  assert.equal(JSON.parse(executeOut.value).data.execution.result.rowsAffected, 1);

  const reuseErr = capture();
  const reuseStatus = await runCli(
    ['mutation', 'execute', ...connection, '--plan', plan.planId, '--approved', plan.approvalHash],
    { stdout: capture(), stderr: reuseErr, planStore, adapterFactory },
  );
  assert.equal(reuseStatus, 1);
  assert.equal(JSON.parse(reuseErr.value).error.code, 'PLAN_ALREADY_USED');
  assert.equal(executions.length, 1);
});
