import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs, assertAllowedFlags, booleanFlag, integerFlag, listFlag, optionalString, requiredString } from './core/args.js';
import { appendAudit, readAudit } from './core/audit.js';
import { AgentDbError, invariant } from './core/errors.js';
import { removeIfExists } from './core/fs.js';
import { operationInput } from './core/input.js';
import { commandContext, emitJson, failure, publicTarget, success } from './core/output.js';
import { createAdapter } from './adapters/index.js';
import { projectPaths, runtimePaths } from './config/paths.js';
import { ProjectStore } from './config/projects.js';
import { loadSchemaCache, saveSchemaCache } from './config/schema-cache.js';
import { PendingStore } from './security/pending.js';
import { assertNoEmbeddedSecret, requireMongoMutation, requireReadOperation, resolveTransactionMode } from './security/safety.js';
import { readHidden, readVisibleLine, requireTty } from './security/secret-input.js';
import { Vault } from './security/vault.js';

const VERSION = '0.2.0';
const DEFAULT_PORTS = { oracle: 1521, mongodb: 27017, sqlserver: 1433, postgresql: 5432, redis: 6379 };
const INPUT_FLAGS = ['target', 'file', 'text', 'stdin', 'max-rows', 'timeout-ms'];
const TERMINAL_UNSAFE = /[\u007f-\u009f\u061c\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]/gu;

function terminalJsonString(value) {
  return JSON.stringify(String(value)).replace(
    TERMINAL_UNSAFE,
    (character) => `\\u${character.codePointAt(0).toString(16).padStart(4, '0')}`,
  );
}

const USAGE = [
  'agent-db doctor',
  'agent-db project init --name <name>',
  'agent-db project show|list',
  'agent-db project bind --id <project-uuid>',
  'agent-db target add --id <id> --engine <oracle|mongodb|sqlserver|postgresql|redis> --environment <env> --host <host> --database <db-or-service>',
  'agent-db target list|show|test --target <id>',
  'agent-db credential set|status|reveal --target <id> --mode <read|mutation>',
  'agent-db schema refresh|show --target <id>',
  'agent-db read --target <id> (--file <path>|--text <value>|--stdin)',
  'agent-db mutation prepare --target <id> (--file <path>|--text <value>|--stdin) [--transaction <auto|always|never>]',
  'agent-db mutation show|approve|cancel --target <id> --plan <uuid>',
  'agent-db mutation execute --target <id> --plan <uuid>',
  'agent-db audit list [--target <id>] [--limit <n>]',
];

function commandName(positionals) {
  return positionals.slice(0, positionals[0] === 'read' || positionals[0] === 'doctor' ? 1 : 2).join(' ') || 'help';
}

function modeFlag(flags) {
  const mode = optionalString(flags, 'mode') || 'read';
  invariant(mode === 'read' || mode === 'mutation', 'INVALID_ARGUMENT', '--mode must be read or mutation');
  return mode;
}

function assertModeSupported(target, mode) {
  invariant(
    !(target.engine === 'redis' && mode === 'mutation'),
    'UNSUPPORTED_OPERATION',
    'Redis mutation mode is not supported in this version',
  );
}

async function projectAndTarget(store, flags) {
  const project = await store.resolveProject();
  const target = await store.target(project, requiredString(flags, 'target'));
  return { project, target };
}

async function targetCredential(vault, project, target, mode) {
  return vault.credential(target.credentials[mode], {
    projectId: project.id,
    targetId: target.id,
    targetFingerprint: target.targetFingerprint,
    engine: target.engine,
    mode,
  });
}

async function driverStatus(name) {
  try {
    await import(name);
    return { available: true };
  } catch (error) {
    return { available: false, error: error.code || error.message };
  }
}

async function appendAuditSafely(paths, event) {
  try {
    await appendAudit(paths, event);
    return [];
  } catch (error) {
    return [{ code: 'AUDIT_WRITE_FAILED', causeCode: error?.code || 'UNKNOWN' }];
  }
}

async function doctor(paths, store) {
  const [oracle, mongodb, sqlserver, postgresql, cursor, redis, keyring] = await Promise.all([
    driverStatus('oracledb'),
    driverStatus('mongodb'),
    driverStatus('mssql'),
    driverStatus('pg'),
    driverStatus('pg-cursor'),
    driverStatus('@redis/client'),
    driverStatus('@napi-rs/keyring'),
  ]);
  let project;
  try {
    const resolved = await store.resolveProject();
    project = { bound: true, id: resolved.id, name: resolved.name, root: resolved.root };
  } catch (error) {
    project = { bound: false, code: error.code || 'PROJECT_CONTEXT_REQUIRED' };
  }
  return {
    version: VERSION,
    node: process.version,
    platform: process.platform,
    runtimeRoot: paths.root,
    project,
    drivers: { oracle, mongodb, sqlserver, postgresql, postgresqlCursor: cursor, redis },
    keyring,
  };
}

async function handleProject(action, flags, store) {
  if (action === 'init') {
    assertAllowedFlags(flags, ['name']);
    return store.initProject(requiredString(flags, 'name'));
  }
  if (action === 'list') {
    assertAllowedFlags(flags, []);
    return store.listProjects();
  }
  if (action === 'show') {
    assertAllowedFlags(flags, []);
    const project = await store.resolveProject();
    return { project, manifest: await store.manifest(project.id) };
  }
  if (action === 'bind') {
    assertAllowedFlags(flags, ['id']);
    return store.bindProject(requiredString(flags, 'id'));
  }
  throw new AgentDbError('INVALID_COMMAND', `Unknown project command: ${action || ''}`);
}

async function handleTarget(action, flags, store, vault) {
  if (action === 'add') {
    assertAllowedFlags(flags, [
      'id', 'engine', 'environment', 'host', 'port', 'database', 'service', 'namespace',
      'key-prefix', 'tls', 'encrypt', 'trust-server-certificate', 'auth-source', 'expected-server-identity',
    ]);
    const project = await store.resolveProject();
    const engine = requiredString(flags, 'engine');
    invariant(DEFAULT_PORTS[engine], 'INVALID_ARGUMENT', `Unsupported engine: ${engine}`);
    return store.addTarget(project, {
      id: requiredString(flags, 'id'),
      engine,
      environment: requiredString(flags, 'environment'),
      host: requiredString(flags, 'host'),
      port: integerFlag(flags, 'port', DEFAULT_PORTS[engine], { min: 1, max: 65535 }),
      database: requiredString(flags, 'database'),
      service: optionalString(flags, 'service'),
      allowedNamespaces: listFlag(flags, 'namespace'),
      keyPrefix: optionalString(flags, 'key-prefix'),
      tls: booleanFlag(flags, 'tls', engine !== 'sqlserver'),
      encrypt: booleanFlag(flags, 'encrypt', engine === 'sqlserver'),
      trustServerCertificate: booleanFlag(flags, 'trust-server-certificate', false),
      authSource: optionalString(flags, 'auth-source'),
      expectedServerIdentity: optionalString(flags, 'expected-server-identity'),
    });
  }

  if (action === 'list') {
    assertAllowedFlags(flags, []);
    const project = await store.resolveProject();
    return (await store.listTargets(project)).map(publicTarget);
  }

  if (action === 'show') {
    assertAllowedFlags(flags, ['target']);
    const { project, target } = await projectAndTarget(store, flags);
    return { project: { id: project.id, name: project.name }, target: publicTarget(target), allowedNamespaces: target.allowedNamespaces, credentialStatus: {
      read: Boolean(target.credentials.read), mutation: Boolean(target.credentials.mutation),
    } };
  }

  if (action === 'test') {
    assertAllowedFlags(flags, ['target', 'mode', 'timeout-ms']);
    const { project, target } = await projectAndTarget(store, flags);
    const mode = modeFlag(flags);
    assertModeSupported(target, mode);
    const credential = await targetCredential(vault, project, target, mode);
    const adapter = await createAdapter(target, credential);
    return { ...await adapter.test({ timeoutMs: integerFlag(flags, 'timeout-ms', 15000, { min: 1000, max: 300000 }) }), mode };
  }

  throw new AgentDbError('INVALID_COMMAND', `Unknown target command: ${action || ''}`);
}

async function handleCredential(action, flags, store, vault, paths) {
  const allowed = action === 'set' ? ['target', 'mode', 'username'] : ['target', 'mode'];
  assertAllowedFlags(flags, allowed);
  const { project, target } = await projectAndTarget(store, flags);
  const mode = modeFlag(flags);
  assertModeSupported(target, mode);

  if (action === 'status') {
    return { target: publicTarget(target), mode, configured: Boolean(target.credentials[mode]) };
  }

  if (action === 'set') {
    requireTty();
    const username = optionalString(flags, 'username') || await readVisibleLine(`Username for ${target.id}/${mode}: `);
    invariant(username, 'INVALID_ARGUMENT', 'Username is required');
    const secret = await readHidden(`Secret for ${target.id}/${mode}: `);
    const repeated = await readHidden('Repeat secret: ');
    invariant(secret && secret === repeated, 'CREDENTIAL_MISMATCH', 'Credential secrets did not match');

    const candidate = { username, secret, mode };
    const adapter = await createAdapter(target, candidate);
    const tested = await adapter.test({ timeoutMs: 15000 });
    const previous = target.credentials[mode];
    const stored = await vault.storeCredential({
      projectId: project.id,
      targetId: target.id,
      targetFingerprint: target.targetFingerprint,
      engine: target.engine,
      mode,
      username,
      secret,
    });
    try {
      await store.setCredentialReference(project, target.id, mode, stored.credentialId);
    } catch (error) {
      await vault.deleteCredential(stored.credentialId);
      throw error;
    }
    await vault.deleteCredential(previous);
    await appendAudit(paths, { action: 'credential.set', projectId: project.id, targetId: target.id, credentialMode: mode, outcome: 'success' });
    return { target: publicTarget(target), mode, credentialId: stored.credentialId, identity: tested.identity };
  }

  if (action === 'reveal') {
    requireTty({ input: process.stdin, output: process.stderr });
    invariant(process.stdout.isTTY, 'LOCAL_TTY_REQUIRED', 'Credential reveal refuses captured or redirected stdout');
    const phrase = `REVEAL ${target.id} ${mode}`;
    const confirmation = await readVisibleLine(`Type "${phrase}" to reveal locally: `);
    invariant(confirmation === phrase, 'USER_CONFIRMATION_REQUIRED', 'Reveal confirmation did not match');
    const credential = await targetCredential(vault, project, target, mode);
    process.stdout.write(`Encoding: terminal-safe JSON string\nUsername: ${terminalJsonString(credential.username)}\nSecret: ${terminalJsonString(credential.secret)}\n`);
    await appendAudit(paths, { action: 'credential.reveal', projectId: project.id, targetId: target.id, credentialMode: mode, outcome: 'success' });
    return { rawOutput: true };
  }

  throw new AgentDbError('INVALID_COMMAND', `Unknown credential command: ${action || ''}`);
}

async function refreshSchema(flags, store, vault, paths) {
  assertAllowedFlags(flags, ['target', 'timeout-ms']);
  const { project, target } = await projectAndTarget(store, flags);
  const credential = await targetCredential(vault, project, target, 'read');
  const adapter = await createAdapter(target, credential);
  const result = await adapter.inspect({ timeoutMs: integerFlag(flags, 'timeout-ms', 30000, { min: 1000, max: 300000 }) });
  const cache = await saveSchemaCache(paths, vault, project, target, result);
  await appendAudit(paths, { action: 'schema.refresh', projectId: project.id, targetId: target.id, outcome: 'success' });
  return { ...result, cache: { capturedAt: cache.capturedAt, targetFingerprint: cache.targetFingerprint } };
}

async function handleSchema(action, flags, store, vault, paths) {
  if (action === 'refresh') return refreshSchema(flags, store, vault, paths);
  if (action === 'show') {
    assertAllowedFlags(flags, ['target']);
    const { project, target } = await projectAndTarget(store, flags);
    return loadSchemaCache(paths, vault, project, target);
  }
  throw new AgentDbError('INVALID_COMMAND', `Unknown schema command: ${action || ''}`);
}

async function handleRead(flags, store, vault, paths) {
  assertAllowedFlags(flags, INPUT_FLAGS);
  const { project, target } = await projectAndTarget(store, flags);
  const rawInput = await operationInput(flags);
  const options = {
    maxRows: integerFlag(flags, 'max-rows', 100, { min: 1, max: 10000 }),
    timeoutMs: integerFlag(flags, 'timeout-ms', 15000, { min: 1000, max: 300000 }),
  };
  requireReadOperation(target.engine, rawInput, target, options);
  const credential = await targetCredential(vault, project, target, 'read');
  const adapter = await createAdapter(target, credential);
  const result = await adapter.executeRead(rawInput, options);
  await appendAudit(paths, {
    action: 'read.execute', projectId: project.id, targetId: target.id, outcome: 'success',
    elapsedMs: result.elapsedMs, rowCount: result.result?.rowCount,
  });
  return { context: commandContext(project, target), value: result };
}

async function handleMutation(action, flags, store, vault, pending, paths) {
  if (action === 'prepare') {
    assertAllowedFlags(flags, ['target', 'file', 'text', 'stdin', 'timeout-ms', 'transaction']);
    const { project, target } = await projectAndTarget(store, flags);
    invariant(target.engine !== 'redis', 'UNSUPPORTED_OPERATION', 'Redis mutation is not supported in this version');
    const rawInput = await operationInput(flags);
    assertNoEmbeddedSecret(target.engine, rawInput);
    invariant(target.expectedServerIdentity, 'TARGET_IDENTITY_REQUIRED', 'Mutation targets require --expected-server-identity');
    const credential = await targetCredential(vault, project, target, 'mutation');
    const adapter = await createAdapter(target, credential);
    const tested = await adapter.test({ timeoutMs: integerFlag(flags, 'timeout-ms', 15000, { min: 1000, max: 300000 }) });
    const operationType = target.engine === 'mongodb'
      ? `mongodb.${requireMongoMutation(rawInput, target).operation}`
      : `${target.engine}.sql`;
    const transactionMode = resolveTransactionMode(target.engine, rawInput, optionalString(flags, 'transaction') || 'auto');
    const plan = await pending.prepare({
      project, target, rawInput, operationType, transactionMode, verifiedIdentity: tested.identity,
    });
    await appendAudit(paths, { action: 'mutation.prepare', projectId: project.id, targetId: target.id, operationHash: plan.operationHash, planId: plan.planId, outcome: 'success' });
    return { context: commandContext(project, target), value: plan };
  }

  if (action === 'show') {
    assertAllowedFlags(flags, ['target', 'plan']);
    const { project, target } = await projectAndTarget(store, flags);
    return { context: commandContext(project, target), value: await pending.show(requiredString(flags, 'plan'), project, target) };
  }

  if (action === 'approve') {
    assertAllowedFlags(flags, ['target', 'plan']);
    requireTty({ input: process.stdin, output: process.stderr });
    invariant(process.stdout.isTTY, 'LOCAL_TTY_REQUIRED', 'Mutation approval refuses captured or redirected stdout');
    const { project, target } = await projectAndTarget(store, flags);
    const planId = requiredString(flags, 'plan');
    const plan = await pending.show(planId, project, target);
    process.stderr.write([
      '\nExact mutation preview (JSON string encoding):',
      terminalJsonString(plan.operationPreview.exact),
      `Project: ${terminalJsonString(plan.projectName)} (${plan.projectId})`,
      `Environment: ${terminalJsonString(plan.environment)}`,
      `Target: ${plan.targetId} (${plan.engine})`,
      `Verified server: ${terminalJsonString(plan.verifiedIdentity.serverIdentity)}`,
      `Verified database: ${terminalJsonString(plan.verifiedIdentity.database)}`,
      `Transaction: ${terminalJsonString(plan.transactionMode)}`,
      `Expires: ${terminalJsonString(plan.expiresAt)}`,
      '',
    ].join('\n'));
    const approved = await pending.approve(planId, project, target);
    await appendAudit(paths, { action: 'mutation.approve', projectId: project.id, targetId: target.id, planId, operationHash: plan.operationHash, outcome: 'success' });
    return { context: commandContext(project, target), value: approved };
  }

  if (action === 'cancel') {
    assertAllowedFlags(flags, ['target', 'plan']);
    const { project, target } = await projectAndTarget(store, flags);
    const planId = requiredString(flags, 'plan');
    await pending.cancel(planId, project, target);
    await appendAudit(paths, { action: 'mutation.cancel', projectId: project.id, targetId: target.id, planId, outcome: 'success' });
    return { context: commandContext(project, target), value: { planId, cancelled: true } };
  }

  if (action === 'execute') {
    assertAllowedFlags(flags, ['target', 'plan', 'timeout-ms']);
    const { project, target } = await projectAndTarget(store, flags);
    const planId = requiredString(flags, 'plan');
    return store.withProjectManifestLock(project, async (lockedProject) => {
      const lockedTarget = await store.target(lockedProject, target.id);
      invariant(lockedTarget.engine !== 'redis', 'UNSUPPORTED_OPERATION', 'Redis mutation is not supported in this version');
      const credential = await targetCredential(vault, lockedProject, lockedTarget, 'mutation');
      const adapter = await createAdapter(lockedTarget, credential);
      const plan = await pending.consume(planId, lockedProject, lockedTarget);
      await removeIfExists(path.join(projectPaths(paths, lockedProject.id).schema, `${lockedTarget.id}.json.enc`));
      try {
        const result = await adapter.executeMutation(plan.rawInput, {
          timeoutMs: integerFlag(flags, 'timeout-ms', 30000, { min: 1000, max: 300000 }),
          expectedIdentity: plan.verifiedIdentity,
          transactionMode: plan.transactionMode,
          approvalExpiresAt: plan.expiresAt,
        });
        const warnings = await appendAuditSafely(paths, {
          action: 'mutation.execute', projectId: lockedProject.id, targetId: lockedTarget.id, planId,
          operationHash: plan.operationHash, outcome: 'success', elapsedMs: result.elapsedMs,
        });
        return { context: commandContext(lockedProject, lockedTarget), value: { plan: pending.publicPlan(plan), execution: result }, warnings };
      } catch (error) {
        const warnings = await appendAuditSafely(paths, {
          action: 'mutation.execute', projectId: lockedProject.id, targetId: lockedTarget.id, planId,
          operationHash: plan.operationHash, outcome: 'error', errorCode: error.code || 'MUTATION_OUTCOME_UNKNOWN',
        });
        if (warnings.length > 0 && error instanceof AgentDbError) {
          error.details = { ...(error.details || {}), auditWarning: warnings[0] };
        }
        throw error;
      }
    });
  }

  throw new AgentDbError('INVALID_COMMAND', `Unknown mutation command: ${action || ''}`);
}

async function handleAudit(action, flags, store, paths) {
  invariant(action === 'list', 'INVALID_COMMAND', `Unknown audit command: ${action || ''}`);
  assertAllowedFlags(flags, ['target', 'limit']);
  const project = await store.resolveProject();
  const targetId = optionalString(flags, 'target');
  if (targetId) await store.target(project, targetId);
  return readAudit(paths, {
    projectId: project.id,
    targetId,
    limit: integerFlag(flags, 'limit', 50, { min: 1, max: 1000 }),
  });
}

async function packageVersion() {
  const packagePath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'package.json');
  return JSON.parse(await readFile(packagePath, 'utf8')).version;
}

export async function runCli(argv) {
  const parsed = parseArgs(argv);
  const command = commandName(parsed.positionals);
  const paths = runtimePaths();
  const store = new ProjectStore(paths);
  const vault = new Vault(paths);
  const pending = new PendingStore(paths, vault);

  try {
    if (parsed.flags.version || parsed.positionals[0] === 'version') {
      assertAllowedFlags(parsed.flags, ['version']);
      emitJson(success('version', { version: await packageVersion() }));
      return;
    }
    if (parsed.flags.help || parsed.positionals.length === 0) {
      assertAllowedFlags(parsed.flags, ['help']);
      emitJson(success('help', { version: await packageVersion(), usage: USAGE }));
      return;
    }

    let result;
    switch (parsed.positionals[0]) {
      case 'doctor':
        assertAllowedFlags(parsed.flags, []);
        result = await doctor(paths, store);
        break;
      case 'project': result = await handleProject(parsed.positionals[1], parsed.flags, store); break;
      case 'target': result = await handleTarget(parsed.positionals[1], parsed.flags, store, vault); break;
      case 'credential': result = await handleCredential(parsed.positionals[1], parsed.flags, store, vault, paths); break;
      case 'schema': result = await handleSchema(parsed.positionals[1], parsed.flags, store, vault, paths); break;
      case 'read': result = await handleRead(parsed.flags, store, vault, paths); break;
      case 'mutation': result = await handleMutation(parsed.positionals[1], parsed.flags, store, vault, pending, paths); break;
      case 'audit': result = await handleAudit(parsed.positionals[1], parsed.flags, store, paths); break;
      default: throw new AgentDbError('INVALID_COMMAND', `Unknown command: ${parsed.positionals[0]}`);
    }

    if (result?.rawOutput) return;
    if (result?.context && Object.hasOwn(result, 'value')) {
      emitJson(success(command, result.value, result.context, result.warnings || []));
    } else {
      emitJson(success(command, result));
    }
  } catch (error) {
    emitJson(failure(command, error));
    process.exitCode = error instanceof AgentDbError ? error.exitCode : 1;
  }
}
