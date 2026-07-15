import { createHash, randomUUID } from 'node:crypto';
import { readFile, rename } from 'node:fs/promises';
import path from 'node:path';
import { AgentDbError, invariant } from '../core/errors.js';
import { atomicWriteJson, removeIfExists, validateUuid, withFileLock } from '../core/fs.js';
import { readVisibleLine, requireTty } from './secret-input.js';

const DEFAULT_TTL_MS = 5 * 60 * 1000;

function hashOperation(rawInput) {
  return createHash('sha256').update(rawInput).digest('hex');
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(([, child]) => child !== undefined)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, child]) => [key, canonicalize(child)]),
  );
}

function hashApprovalSurface(plan) {
  const surface = {
    formatVersion: plan.formatVersion,
    planId: plan.planId,
    projectId: plan.projectId,
    projectBindingRevision: plan.projectBindingRevision,
    targetId: plan.targetId,
    targetFingerprint: plan.targetFingerprint,
    engine: plan.engine,
    environment: plan.environment,
    credentialId: plan.credentialId,
    operationType: plan.operationType,
    operationHash: plan.operationHash,
    transactionMode: plan.transactionMode,
    verifiedIdentity: canonicalize(plan.verifiedIdentity),
    createdAt: plan.createdAt,
    expiresAt: plan.expiresAt,
  };
  return createHash('sha256').update(JSON.stringify(surface)).digest('hex');
}

function planScope(planId, projectId, targetId) {
  return { kind: 'mutation-plan', planId, projectId, targetId };
}

function approvalScope(plan) {
  return {
    kind: 'mutation-approval',
    planId: plan.planId,
    projectId: plan.projectId,
    targetId: plan.targetId,
    approvalHash: plan.approvalHash,
  };
}

export class PendingStore {
  constructor(paths, vault, { now = () => Date.now(), ttlMs = DEFAULT_TTL_MS } = {}) {
    this.paths = paths;
    this.vault = vault;
    this.now = now;
    this.ttlMs = ttlMs;
  }

  file(planId) {
    validateUuid(planId, 'plan id');
    return path.join(this.paths.pending, `${planId}.json.enc`);
  }

  approvalFile(planId) {
    validateUuid(planId, 'plan id');
    return path.join(this.paths.pending, `${planId}.approval.json.enc`);
  }

  lockFile(planId) {
    return `${this.file(planId)}.lock`;
  }

  async prepare({ project, target, rawInput, operationType, verifiedIdentity, transactionMode }) {
    invariant(typeof rawInput === 'string' && rawInput.length > 0, 'INVALID_ARGUMENT', 'Mutation input is empty');
    invariant(['always', 'never'].includes(transactionMode), 'INVALID_ARGUMENT', 'Resolved transaction mode must be always or never');
    for (const key of ['database', 'principal', 'serverIdentity']) {
      invariant(typeof verifiedIdentity?.[key] === 'string' && verifiedIdentity[key], 'TARGET_IDENTITY_MISMATCH', `Verified identity is missing ${key}`);
    }
    const planId = randomUUID();
    const hash = hashOperation(rawInput);
    const createdAtMs = this.now();
    const plan = {
      formatVersion: 1,
      planId,
      projectId: project.id,
      projectName: project.name,
      projectBindingRevision: project.bindingRevision,
      targetId: target.id,
      targetFingerprint: target.targetFingerprint,
      engine: target.engine,
      environment: target.environment,
      credentialId: target.credentials.mutation,
      operationType,
      operationHash: hash,
      rawInput,
      verifiedIdentity,
      transactionMode,
      createdAt: new Date(createdAtMs).toISOString(),
      expiresAt: new Date(createdAtMs + this.ttlMs).toISOString(),
    };
    plan.approvalHash = hashApprovalSurface(plan);
    plan.confirmationPhrase = `MUTATE ${target.id} ${plan.approvalHash.slice(0, 12)}`;
    const scope = planScope(planId, project.id, target.id);
    const record = { formatVersion: 1, ...scope, envelope: await this.vault.encryptObject(plan, scope) };
    await atomicWriteJson(this.file(planId), record);
    return this.publicPlan(plan, null);
  }

  publicPlan(plan, approval = undefined) {
    return {
      planId: plan.planId,
      projectId: plan.projectId,
      projectName: plan.projectName,
      projectBindingRevision: plan.projectBindingRevision,
      targetId: plan.targetId,
      targetFingerprint: plan.targetFingerprint,
      engine: plan.engine,
      environment: plan.environment,
      operationType: plan.operationType,
      operationHash: plan.operationHash,
      approvalHash: plan.approvalHash,
      operationPreview: { encoding: 'utf8', exact: plan.rawInput },
      verifiedIdentity: plan.verifiedIdentity,
      transactionMode: plan.transactionMode,
      confirmationPhrase: plan.confirmationPhrase,
      approval: approval === undefined ? undefined : approval
        ? { approved: true, approvedAt: approval.approvedAt, expiresAt: approval.expiresAt }
        : { approved: false },
      createdAt: plan.createdAt,
      expiresAt: plan.expiresAt,
      warning: 'Execution requires a separate approval artifact created by mutation approve in a local interactive terminal.',
    };
  }

  async load(planId, projectId, targetId, filePath = this.file(planId)) {
    let record;
    try {
      record = JSON.parse(await readFile(filePath, 'utf8'));
    } catch (error) {
      if (error?.code === 'ENOENT') throw new AgentDbError('PLAN_NOT_FOUND', `Mutation plan not found: ${planId}`);
      throw error;
    }
    const scope = planScope(planId, projectId, targetId);
    for (const [key, value] of Object.entries(scope)) {
      invariant(record[key] === value, 'PLAN_CHANGED', `Mutation plan ${key} does not match`);
    }
    return this.vault.decryptObject(record.envelope, scope);
  }

  validatePlan(plan, project, target) {
    invariant(Date.parse(plan.expiresAt) > this.now(), 'PLAN_EXPIRED', 'Mutation plan has expired');
    invariant(plan.projectBindingRevision === project.bindingRevision, 'PLAN_CHANGED', 'Project binding changed after plan creation');
    invariant(plan.targetFingerprint === target.targetFingerprint, 'PLAN_CHANGED', 'Target fingerprint changed after plan creation');
    invariant(plan.credentialId === target.credentials.mutation, 'PLAN_CHANGED', 'Mutation credential changed after plan creation');
    invariant(hashOperation(plan.rawInput) === plan.operationHash, 'PLAN_CHANGED', 'Mutation payload hash does not match');
    invariant(hashApprovalSurface(plan) === plan.approvalHash, 'PLAN_CHANGED', 'Mutation approval surface hash does not match');
    return plan;
  }

  async loadApproval(plan) {
    let record;
    try {
      record = JSON.parse(await readFile(this.approvalFile(plan.planId), 'utf8'));
    } catch (error) {
      if (error?.code === 'ENOENT') return null;
      throw error;
    }
    const scope = approvalScope(plan);
    for (const [key, value] of Object.entries(scope)) {
      invariant(record[key] === value, 'APPROVAL_CHANGED', `Mutation approval ${key} does not match`);
    }
    const approval = await this.vault.decryptObject(record.envelope, scope);
    for (const [key, value] of Object.entries(scope)) {
      invariant(approval[key] === value, 'APPROVAL_CHANGED', `Mutation approval payload ${key} does not match`);
    }
    invariant(approval.projectBindingRevision === plan.projectBindingRevision, 'APPROVAL_CHANGED', 'Approved project binding does not match');
    invariant(approval.targetFingerprint === plan.targetFingerprint, 'APPROVAL_CHANGED', 'Approved target does not match');
    invariant(approval.credentialId === plan.credentialId, 'APPROVAL_CHANGED', 'Approved mutation credential does not match');
    invariant(approval.expiresAt === plan.expiresAt, 'APPROVAL_CHANGED', 'Approval expiry does not match the plan');
    invariant(Date.parse(approval.expiresAt) > this.now(), 'PLAN_EXPIRED', 'Mutation approval has expired');
    return approval;
  }

  async show(planId, project, target) {
    const plan = this.validatePlan(await this.load(planId, project.id, target.id), project, target);
    return this.publicPlan(plan, await this.loadApproval(plan));
  }

  async approve(planId, project, target) {
    requireTty({ input: process.stdin, output: process.stderr });
    invariant(process.stdout.isTTY, 'LOCAL_TTY_REQUIRED', 'Mutation approval refuses captured or redirected stdout');
    return withFileLock(this.lockFile(planId), async () => {
      const plan = this.validatePlan(await this.load(planId, project.id, target.id), project, target);
      const confirmationPhrase = await readVisibleLine(`Type "${plan.confirmationPhrase}" to approve this exact plan: `);
      this.validatePlan(plan, project, target);
      invariant(confirmationPhrase === plan.confirmationPhrase, 'MUTATION_CONFIRMATION_REQUIRED', 'Confirmation phrase does not match the exact mutation plan');
      const scope = approvalScope(plan);
      const approval = {
        formatVersion: 1,
        ...scope,
        projectBindingRevision: plan.projectBindingRevision,
        targetFingerprint: plan.targetFingerprint,
        credentialId: plan.credentialId,
        approvedAt: new Date(this.now()).toISOString(),
        expiresAt: plan.expiresAt,
      };
      const record = { formatVersion: 1, ...scope, envelope: await this.vault.encryptObject(approval, scope) };
      await atomicWriteJson(this.approvalFile(planId), record);
      return this.publicPlan(plan, approval);
    });
  }

  async consume(planId, project, target) {
    return withFileLock(this.lockFile(planId), async () => {
      const source = this.file(planId);
      const approvalSource = this.approvalFile(planId);
      const consuming = `${source}.${randomUUID()}.consuming`;
      const approvalConsuming = `${approvalSource}.${randomUUID()}.consuming`;
      const plan = this.validatePlan(await this.load(planId, project.id, target.id), project, target);
      const approval = await this.loadApproval(plan);
      invariant(approval, 'MUTATION_APPROVAL_REQUIRED', 'Run mutation approve in a local interactive terminal before execution');

      try {
        await rename(source, consuming);
        await rename(approvalSource, approvalConsuming);
      } catch (error) {
        if (error?.code === 'ENOENT') throw new AgentDbError('PLAN_ALREADY_USED', 'Mutation plan or approval is missing, expired, or already consumed');
        throw error;
      }

      try {
        return plan;
      } finally {
        await Promise.all([removeIfExists(consuming), removeIfExists(approvalConsuming)]);
      }
    });
  }

  async cancel(planId, project, target) {
    return withFileLock(this.lockFile(planId), async () => {
      const source = this.file(planId);
      const cancelling = `${source}.${randomUUID()}.cancelling`;
      this.validatePlan(await this.load(planId, project.id, target.id), project, target);
      try {
        await rename(source, cancelling);
      } catch (error) {
        if (error?.code === 'ENOENT') throw new AgentDbError('PLAN_ALREADY_USED', 'Mutation plan is missing, expired, or already consumed');
        throw error;
      }
      await Promise.all([removeIfExists(cancelling), removeIfExists(this.approvalFile(planId))]);
    });
  }
}
