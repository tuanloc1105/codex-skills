import process from 'node:process';
import { createAdapter } from './adapters/index.js';
import {
  assertAllowedFlags,
  integerFlag,
  optionalString,
  parseArgs,
  requiredString,
} from './core/args.js';
import { DataDebugError, invariant } from './core/errors.js';
import { operationInput } from './core/input.js';
import { emitJson, failure, success } from './core/output.js';
import {
  CONNECTION_FLAGS,
  connectionFromFlags,
  publicConnectionTarget,
} from './connection.js';
import { PlanStore } from './security/plans.js';
import {
  requireMongoMutation,
  requireReadOperation,
  requireRedisMutation,
  requireSqlMutation,
  resolveTransactionMode,
} from './security/safety.js';

const VERSION = '0.3.0';
const MINIMUM_NODE_MAJOR = 22;
const INPUT_FLAGS = ['file', 'text', 'stdin'];
const RUNTIME_FLAGS = ['timeout-ms'];
const USAGE = [
  'data-debug doctor',
  'data-debug test <connection options>',
  'data-debug inspect <connection options>',
  'data-debug read <connection options> (--file <path>|--text <value>|--stdin)',
  'data-debug mutation preview <connection options> (--file <path>|--text <value>|--stdin) [--transaction <auto|always|never>]',
  'data-debug mutation execute <connection options> --plan <uuid> --approved <hash>',
];

function commandName(positionals) {
  if (positionals[0] === 'mutation') return positionals.slice(0, 2).join(' ') || 'mutation';
  return positionals[0] || 'help';
}

function helpData() {
  return {
    version: VERSION,
    usage: USAGE,
    connectionOptions: {
      environment: '--env-file <path> [--connection-env <name>] (defaults to DATA_DEBUG_URL)',
      direct: '--engine <engine> --host <host> --database <name> [--port <port>] --username <name> [--password-env <name>] (username optional for Redis)',
      engines: ['postgresql', 'mongodb', 'sqlserver', 'oracle', 'redis'],
      engineSpecific: [
        '--service <name> (Oracle)',
        '--auth-source <database> (MongoDB)',
        '--namespace <collection> (MongoDB, repeatable)',
        '--key-prefix <prefix> (Redis, optional)',
        '--tls <true|false>',
        '--encrypt <true|false> (SQL Server)',
        '--trust-server-certificate <true|false>',
        '--allow-insecure-credential-transport <true|false> (explicit plaintext/unverified override)',
      ],
    },
    operationOptions: {
      global: ['--help', '--version'],
      input: ['--file <path>', '--text <value>', '--stdin'],
      live: '--timeout-ms <1..300000> (default 15000)',
      read: '--max-rows <1..10000> (default 100)',
      mutationPreview: '--transaction <auto|always|never> (always only for PostgreSQL)',
      mutationExecute: '--plan <uuid> --approved <approval-hash>',
    },
    notes: [
      'Read commands are the default and reject mutation input.',
      'A mutation must be previewed, explicitly approved in chat, then executed with its approval hash.',
      'Connection secrets are read from environment variables and are never written to mutation plans.',
      'Credentialed non-loopback connections require verified encryption unless the explicit insecure override is accepted.',
    ],
  };
}

async function driverStatus(name) {
  try {
    await import(name);
    return { available: true };
  } catch (error) {
    return { available: false, code: error?.code || 'IMPORT_FAILED' };
  }
}

async function doctor() {
  const [oracle, mongodb, sqlserver, postgresql, cursor, redis] = await Promise.all([
    driverStatus('oracledb'),
    driverStatus('mongodb'),
    driverStatus('mssql'),
    driverStatus('pg'),
    driverStatus('pg-cursor'),
    driverStatus('@redis/client'),
  ]);
  return {
    version: VERSION,
    node: process.version,
    minimumNode: '22.0.0',
    supportedNode: Number(process.versions.node.split('.')[0]) >= MINIMUM_NODE_MAJOR,
    platform: process.platform,
    drivers: { oracle, mongodb, sqlserver, postgresql, postgresqlCursor: cursor, redis },
  };
}

function assertSupportedRuntime() {
  invariant(
    Number(process.versions.node.split('.')[0]) >= MINIMUM_NODE_MAJOR,
    'UNSUPPORTED_RUNTIME',
    'data-debug requires Node.js 22 or newer',
  );
}

function timeoutMs(flags) {
  return integerFlag(flags, 'timeout-ms', 15000, { min: 1, max: 300000 });
}

function maxRows(flags) {
  return integerFlag(flags, 'max-rows', 100, { min: 1, max: 10000 });
}

function transactionMode(flags, engine, input) {
  const requested = optionalString(flags, 'transaction') || 'auto';
  return resolveTransactionMode(engine, input, requested);
}

function mutationType(engine, input, target) {
  if (engine === 'mongodb') {
    const operation = requireMongoMutation(input, target);
    return `mongodb.${operation.operation}`;
  }
  if (engine === 'redis') {
    const operation = requireRedisMutation(input, target);
    return `redis.${operation.command.toLowerCase().replace(/\s+/g, '-')}`;
  }
  requireSqlMutation(input, engine);
  const statement = input.trim().match(/^(?:(?:--[^\n]*(?:\n|$)|\/\*[\s\S]*?\*\/)\s*)*([A-Za-z]+)/)?.[1]?.toLowerCase() || 'dml';
  return `${engine}.${statement}`;
}

async function connected(flags, mode, callback, adapterFactory) {
  const connection = connectionFromFlags(flags, { mode });
  const adapter = await adapterFactory(connection.target, connection.credential);
  return callback(connection, adapter);
}

async function handleTest(flags, adapterFactory) {
  assertAllowedFlags(flags, [...CONNECTION_FLAGS, ...RUNTIME_FLAGS]);
  return connected(flags, 'read', async ({ context }, adapter) => ({
    data: await adapter.test({ timeoutMs: timeoutMs(flags) }),
    context,
  }), adapterFactory);
}

async function handleInspect(flags, adapterFactory) {
  assertAllowedFlags(flags, [...CONNECTION_FLAGS, ...RUNTIME_FLAGS]);
  return connected(flags, 'read', async ({ context }, adapter) => ({
    data: await adapter.inspect({ timeoutMs: timeoutMs(flags) }),
    context,
  }), adapterFactory);
}

async function handleRead(flags, adapterFactory) {
  assertAllowedFlags(flags, [...CONNECTION_FLAGS, ...INPUT_FLAGS, ...RUNTIME_FLAGS, 'max-rows']);
  const input = await operationInput(flags);
  const connection = connectionFromFlags(flags, { mode: 'read' });
  requireReadOperation(connection.target.engine, input, connection.target, { maxRows: maxRows(flags) });
  const adapter = await adapterFactory(connection.target, connection.credential);
  return {
    data: await adapter.executeRead(input, { maxRows: maxRows(flags), timeoutMs: timeoutMs(flags) }),
    context: connection.context,
  };
}

async function handleMutationPreview(flags, planStore, adapterFactory) {
  assertAllowedFlags(flags, [...CONNECTION_FLAGS, ...INPUT_FLAGS, ...RUNTIME_FLAGS, 'transaction']);
  const input = await operationInput(flags);
  const connection = connectionFromFlags(flags, { mode: 'mutation' });
  const operationType = mutationType(connection.target.engine, input, connection.target);
  const mode = transactionMode(flags, connection.target.engine, input);
  const adapter = await adapterFactory(connection.target, connection.credential);
  const { identity } = await adapter.test({ timeoutMs: timeoutMs(flags) });
  const plan = await planStore.prepare({
    publicTarget: publicConnectionTarget(connection.target),
    rawInput: input,
    operationType,
    transactionMode: mode,
    expectedIdentity: identity,
  });
  return {
    data: {
      plan,
      approvalRequired: true,
      next: `Ask the user to approve this exact operation, then run mutation execute with --plan ${plan.planId} --approved ${plan.approvalHash}`,
    },
    context: connection.context,
  };
}

async function handleMutationExecute(flags, planStore, adapterFactory) {
  assertAllowedFlags(flags, [...CONNECTION_FLAGS, ...RUNTIME_FLAGS, 'plan', 'approved']);
  const planId = requiredString(flags, 'plan');
  const approvalHash = requiredString(flags, 'approved');
  const connection = connectionFromFlags(flags, { mode: 'mutation' });
  const plan = await planStore.consume(planId, approvalHash, connection.target);
  const operationType = mutationType(connection.target.engine, plan.rawInput, connection.target);
  invariant(operationType === plan.operationType, 'PLAN_CHANGED', 'Mutation operation type changed after preview');
  const adapter = await adapterFactory(connection.target, connection.credential);
  return {
    data: {
      plan: planStore.publicPlan(plan),
      execution: await adapter.executeMutation(plan.rawInput, {
        timeoutMs: timeoutMs(flags),
        expectedIdentity: plan.expectedIdentity,
        transactionMode: plan.transactionMode,
        approvalExpiresAt: plan.expiresAt,
      }),
    },
    context: connection.context,
  };
}

async function dispatch(positionals, flags, planStore, adapterFactory) {
  const [command, action] = positionals;
  invariant(positionals.length <= (command === 'mutation' ? 2 : 1), 'INVALID_COMMAND', 'Too many command arguments');

  if (command === 'doctor') {
    assertAllowedFlags(flags, []);
    return { data: await doctor() };
  }
  assertSupportedRuntime();
  if (command === 'test') return handleTest(flags, adapterFactory);
  if (command === 'inspect') return handleInspect(flags, adapterFactory);
  if (command === 'read') return handleRead(flags, adapterFactory);
  if (command === 'mutation' && action === 'preview') return handleMutationPreview(flags, planStore, adapterFactory);
  if (command === 'mutation' && action === 'execute') return handleMutationExecute(flags, planStore, adapterFactory);
  throw new DataDebugError('INVALID_COMMAND', `Unknown command: ${positionals.join(' ') || 'help'}`);
}

export async function runCli(argv, {
  stdout = process.stdout,
  stderr = process.stderr,
  planStore = new PlanStore(),
  adapterFactory = createAdapter,
} = {}) {
  const { positionals, flags } = parseArgs(argv);
  const command = commandName(positionals);
  if (flags.version === true && positionals.length === 0) {
    emitJson(success('version', { version: VERSION }), stdout);
    return 0;
  }
  if (flags.help === true || positionals[0] === 'help' || positionals.length === 0) {
    emitJson(success('help', helpData()), stdout);
    return 0;
  }

  try {
    const result = await dispatch(positionals, flags, planStore, adapterFactory);
    emitJson(success(command, result.data, result.context), stdout);
    return 0;
  } catch (error) {
    emitJson(failure(command, error), stderr);
    return error instanceof DataDebugError ? error.exitCode : 1;
  }
}
