import { createHash, randomUUID } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { DataDebugError, invariant } from '../core/errors.js';
import { atomicWriteJson, readJson, validateUuid, withFileLock, writeJsonExclusive } from '../core/fs.js';

const DEFAULT_TTL_MS = 10 * 60 * 1000;

function defaultStateRoot() {
  const owner = typeof process.getuid === 'function' ? String(process.getuid()) : 'user';
  return process.env.DATA_DEBUG_STATE_DIR || path.join(tmpdir(), `data-debug-${owner}`);
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, child]) => [key, canonicalize(child)]),
  );
}

function sha256(value) {
  return createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(canonicalize(value))).digest('hex');
}

function approvalSurface(plan) {
  return {
    planId: plan.planId,
    targetFingerprint: plan.target.targetFingerprint,
    operationHash: plan.operationHash,
    operationType: plan.operationType,
    transactionMode: plan.transactionMode,
    expectedIdentity: plan.expectedIdentity,
    expiresAt: plan.expiresAt,
  };
}

export class PlanStore {
  constructor({ stateRoot = defaultStateRoot(), now = () => Date.now(), ttlMs = DEFAULT_TTL_MS } = {}) {
    this.directory = path.join(stateRoot, 'plans');
    this.now = now;
    this.ttlMs = ttlMs;
  }

  file(planId) {
    validateUuid(planId, 'plan id');
    return path.join(this.directory, `${planId}.json`);
  }

  lockFile(planId) {
    return `${this.file(planId)}.lock`;
  }

  consumedFile(planId) {
    return `${this.file(planId)}.consumed`;
  }

  async prepare({ publicTarget, rawInput, operationType, transactionMode, expectedIdentity }) {
    const createdAtMs = this.now();
    const plan = {
      version: 1,
      planId: randomUUID(),
      status: 'pending',
      createdAt: new Date(createdAtMs).toISOString(),
      expiresAt: new Date(createdAtMs + this.ttlMs).toISOString(),
      target: publicTarget,
      operationType,
      transactionMode,
      expectedIdentity,
      rawInput,
      operationHash: sha256(rawInput),
    };
    plan.approvalHash = sha256(approvalSurface(plan));
    await atomicWriteJson(this.file(plan.planId), plan);
    return this.publicPlan(plan);
  }

  async load(planId) {
    let plan;
    try {
      plan = await readJson(this.file(planId));
    } catch (error) {
      if (error?.code === 'ENOENT') throw new DataDebugError('PLAN_NOT_FOUND', `Mutation plan was not found: ${planId}`);
      throw error;
    }
    invariant(plan?.version === 1 && plan.planId === planId, 'PLAN_INVALID', 'Mutation plan is invalid');
    invariant(plan.status === 'pending' && plan.consumedAt === undefined, 'PLAN_CHANGED', 'Mutation plan state changed');
    invariant(plan.operationHash === sha256(plan.rawInput), 'PLAN_CHANGED', 'Mutation payload changed after preview');
    invariant(plan.approvalHash === sha256(approvalSurface(plan)), 'PLAN_CHANGED', 'Mutation plan approval surface changed');
    return plan;
  }

  publicPlan(plan) {
    return {
      planId: plan.planId,
      status: plan.status,
      createdAt: plan.createdAt,
      expiresAt: plan.expiresAt,
      target: plan.target,
      operationType: plan.operationType,
      transactionMode: plan.transactionMode,
      expectedIdentity: plan.expectedIdentity,
      operation: plan.rawInput,
      operationHash: plan.operationHash,
      approvalHash: plan.approvalHash,
      ...(plan.consumedAt ? { consumedAt: plan.consumedAt } : {}),
    };
  }

  async consume(planId, approvalHash, target) {
    return withFileLock(this.lockFile(planId), async () => {
      const plan = await this.load(planId);
      let existingConsumption;
      try {
        existingConsumption = await readJson(this.consumedFile(planId));
      } catch (error) {
        if (error?.code !== 'ENOENT') throw error;
      }
      invariant(!existingConsumption, 'PLAN_ALREADY_USED', 'Mutation plan has already been consumed');
      invariant(Date.parse(plan.expiresAt) > this.now(), 'PLAN_EXPIRED', 'Mutation plan has expired');
      invariant(
        typeof approvalHash === 'string' && approvalHash === plan.approvalHash,
        'USER_APPROVAL_REQUIRED',
        'Mutation execution requires the approval hash shown to and approved by the user in the current chat',
      );
      invariant(
        target.targetFingerprint === plan.target.targetFingerprint,
        'TARGET_CHANGED',
        'Connection target changed after mutation preview',
      );
      const consumedAt = new Date(this.now()).toISOString();
      try {
        await writeJsonExclusive(this.consumedFile(planId), {
          version: 1,
          planId,
          status: 'consumed',
          consumedAt,
          approvalHash: plan.approvalHash,
        });
      } catch (error) {
        if (error?.code === 'EEXIST') {
          throw new DataDebugError('PLAN_ALREADY_USED', 'Mutation plan has already been consumed');
        }
        throw error;
      }
      return { ...plan, status: 'consumed', consumedAt };
    });
  }
}
