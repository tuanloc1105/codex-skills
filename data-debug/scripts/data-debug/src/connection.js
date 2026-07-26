import { createHash } from 'node:crypto';
import { isIP } from 'node:net';
import process from 'node:process';
import {
  booleanFlag,
  integerFlag,
  listFlag,
  optionalString,
  requiredString,
} from './core/args.js';
import { DataDebugError, invariant } from './core/errors.js';

export const SUPPORTED_ENGINES = new Set(['oracle', 'mongodb', 'sqlserver', 'postgresql', 'redis']);
export const DEFAULT_PORTS = {
  oracle: 1521,
  mongodb: 27017,
  sqlserver: 1433,
  postgresql: 5432,
  redis: 6379,
};

export const CONNECTION_FLAGS = [
  'env-file', 'connection-env', 'engine', 'host', 'port', 'database', 'service',
  'username', 'password-env', 'tls', 'encrypt', 'trust-server-certificate',
  'auth-source', 'namespace', 'key-prefix', 'allow-insecure-credential-transport',
];
const DIRECT_CONNECTION_FLAGS = [
  'engine', 'host', 'port', 'database', 'service', 'username', 'password-env',
  'tls', 'encrypt', 'trust-server-certificate', 'auth-source',
];

function decodeUrlPart(value, label) {
  try {
    return decodeURIComponent(value);
  } catch {
    throw new DataDebugError('INVALID_ARGUMENT', `Connection URL has an invalid ${label}`);
  }
}

function booleanQuery(url, name, defaultValue) {
  const value = url.searchParams.get(name);
  if (value === null) return defaultValue;
  if (value === 'true' || value === '1') return true;
  if (value === 'false' || value === '0') return false;
  throw new DataDebugError('INVALID_ARGUMENT', `Connection URL parameter ${name} expects true or false`);
}

function engineFromProtocol(protocol) {
  const normalized = protocol.replace(/:$/, '').toLowerCase();
  if (normalized === 'mongodb+srv') {
    throw new DataDebugError('UNSUPPORTED_OPERATION', 'MongoDB SRV URLs are not supported by this version');
  }
  if (normalized === 'postgres' || normalized === 'postgresql') return 'postgresql';
  if (normalized === 'mssql' || normalized === 'sqlserver') return 'sqlserver';
  if (normalized === 'rediss') return 'redis';
  if (SUPPORTED_ENGINES.has(normalized)) return normalized;
  throw new DataDebugError('UNSUPPORTED_ENGINE', `Unsupported connection URL scheme: ${normalized || 'unknown'}`);
}

function databaseFromUrl(url, engine) {
  const pathname = decodeUrlPart(url.pathname.replace(/^\//, ''), 'database path');
  if (engine === 'redis') return pathname || '0';
  invariant(pathname, 'INVALID_ARGUMENT', 'Connection URL must include a database or Oracle service');
  return pathname;
}

function parseConnectionUrl(raw) {
  let url;
  try {
    url = new URL(raw);
  } catch {
    throw new DataDebugError('INVALID_ARGUMENT', 'Connection environment variable is not a valid URL');
  }

  const engine = engineFromProtocol(url.protocol);
  invariant(url.hostname, 'INVALID_ARGUMENT', 'Connection URL must include a host');
  const database = databaseFromUrl(url, engine);
  const port = url.port ? Number(url.port) : DEFAULT_PORTS[engine];
  invariant(Number.isSafeInteger(port) && port > 0 && port <= 65535, 'INVALID_ARGUMENT', 'Connection URL port is invalid');

  const tlsDefault = url.protocol.toLowerCase() === 'rediss:';
  const connection = {
    host: url.hostname,
    port,
    database,
    tls: booleanQuery(url, 'tls', tlsDefault),
    encrypt: booleanQuery(url, 'encrypt', engine === 'sqlserver'),
    trustServerCertificate: booleanQuery(url, 'trustServerCertificate', false),
    ...(engine === 'oracle' ? { service: database } : {}),
    ...(url.searchParams.get('authSource') ? { authSource: url.searchParams.get('authSource') } : {}),
  };

  return {
    engine,
    connection,
    credential: {
      username: decodeUrlPart(url.username || '', 'username'),
      secret: decodeUrlPart(url.password || '', 'password'),
    },
  };
}

function environmentValue(name, label, { optional = false } = {}) {
  const value = process.env[name];
  if (optional && (value === undefined || value === '')) return '';
  invariant(typeof value === 'string' && value.length > 0, 'CONNECTION_NOT_CONFIGURED', `${label} environment variable is not set`);
  return value;
}

function directConnection(flags) {
  const engine = requiredString(flags, 'engine').toLowerCase();
  invariant(SUPPORTED_ENGINES.has(engine), 'UNSUPPORTED_ENGINE', `Unsupported database engine: ${engine}`);
  const database = optionalString(flags, 'database') || (engine === 'redis' ? '0' : undefined);
  invariant(database, 'INVALID_ARGUMENT', 'Missing required option --database');
  const service = optionalString(flags, 'service');
  const username = optionalString(flags, 'username') || '';
  const passwordEnvironment = optionalString(flags, 'password-env');
  const secret = passwordEnvironment
    ? environmentValue(passwordEnvironment, `Password (${passwordEnvironment})`)
    : '';
  if (engine !== 'redis') {
    invariant(username, 'INVALID_ARGUMENT', `--username is required for ${engine}`);
  }

  return {
    engine,
    connection: {
      host: requiredString(flags, 'host'),
      port: integerFlag(flags, 'port', DEFAULT_PORTS[engine], { min: 1, max: 65535 }),
      database,
      ...(service ? { service } : {}),
      tls: booleanFlag(flags, 'tls', false),
      encrypt: booleanFlag(flags, 'encrypt', engine === 'sqlserver'),
      trustServerCertificate: booleanFlag(flags, 'trust-server-certificate', false),
      ...(optionalString(flags, 'auth-source') ? { authSource: optionalString(flags, 'auth-source') } : {}),
    },
    credential: { username, secret },
  };
}

function isLoopbackHost(value) {
  let host = String(value || '').trim().toLowerCase();
  if (host.startsWith('[') && host.endsWith(']')) host = host.slice(1, -1);
  if (host === 'localhost') return true;
  if (isIP(host) === 4) return host.split('.')[0] === '127';
  if (isIP(host) === 6) return host === '::1' || host.startsWith('::ffff:127.');
  return false;
}

function hasVerifiedEncryption(parsed) {
  const encrypted = parsed.engine === 'sqlserver'
    ? parsed.connection.encrypt
    : parsed.connection.tls;
  return Boolean(encrypted) && !parsed.connection.trustServerCertificate;
}

function assertCredentialTransport(parsed, allowInsecureCredentialTransport) {
  if (!parsed.credential.secret || isLoopbackHost(parsed.connection.host) || hasVerifiedEncryption(parsed)) return;
  invariant(
    allowInsecureCredentialTransport,
    'INSECURE_CREDENTIAL_TRANSPORT',
    'Credentialed non-loopback connections require encrypted transport with certificate verification; use --allow-insecure-credential-transport only after accepting the exposure risk',
  );
}

function targetFingerprint(target, username) {
  const surface = {
    engine: target.engine,
    connection: target.connection,
    allowedNamespaces: target.allowedNamespaces,
    keyPrefix: target.keyPrefix,
    allowInsecureCredentialTransport: target.allowInsecureCredentialTransport,
    username,
  };
  return createHash('sha256').update(JSON.stringify(surface)).digest('hex');
}

export function publicConnectionTarget(target) {
  return {
    engine: target.engine,
    host: target.connection.host,
    port: target.connection.port,
    database: target.connection.database,
    ...(target.connection.service ? { service: target.connection.service } : {}),
    tls: Boolean(target.connection.tls),
    ...(target.connection.encrypt === undefined ? {} : { encrypt: Boolean(target.connection.encrypt) }),
    trustServerCertificate: Boolean(target.connection.trustServerCertificate),
    ...(target.connection.authSource ? { authSource: target.connection.authSource } : {}),
    ...(target.allowedNamespaces.length > 0 ? { allowedNamespaces: target.allowedNamespaces } : {}),
    ...(target.keyPrefix ? { keyPrefix: target.keyPrefix } : {}),
    allowInsecureCredentialTransport: Boolean(target.allowInsecureCredentialTransport),
    targetFingerprint: target.targetFingerprint,
  };
}

export function loadConnectionEnvironment(flags) {
  const envFile = optionalString(flags, 'env-file');
  if (!envFile) return;
  invariant(typeof process.loadEnvFile === 'function', 'UNSUPPORTED_RUNTIME', 'This Node.js runtime cannot load env files');
  try {
    process.loadEnvFile(envFile);
  } catch (error) {
    throw new DataDebugError('CONNECTION_NOT_CONFIGURED', `Unable to load environment file: ${error?.code || 'invalid file'}`);
  }
}

export function connectionFromFlags(flags, { mode = 'read' } = {}) {
  loadConnectionEnvironment(flags);
  const explicitEnvironment = optionalString(flags, 'connection-env');
  const directFlags = DIRECT_CONNECTION_FLAGS.filter((name) => Object.hasOwn(flags, name));
  invariant(
    !explicitEnvironment || directFlags.length === 0,
    'INVALID_ARGUMENT',
    `--connection-env cannot be combined with direct connection option(s): ${directFlags.map((name) => `--${name}`).join(', ')}`,
  );
  const environmentName = explicitEnvironment || (directFlags.length === 0 && process.env.DATA_DEBUG_URL ? 'DATA_DEBUG_URL' : undefined);
  const parsed = environmentName
    ? parseConnectionUrl(environmentValue(environmentName, `Connection (${environmentName})`))
    : directConnection(flags);
  const allowInsecureCredentialTransport = booleanFlag(flags, 'allow-insecure-credential-transport', false);
  assertCredentialTransport(parsed, allowInsecureCredentialTransport);

  const allowedNamespaces = listFlag(flags, 'namespace');
  const keyPrefix = optionalString(flags, 'key-prefix') || null;
  invariant(parsed.engine === 'mongodb' || allowedNamespaces.length === 0, 'INVALID_ARGUMENT', '--namespace is only supported for MongoDB');
  invariant(parsed.engine === 'redis' || !keyPrefix, 'INVALID_ARGUMENT', '--key-prefix is only supported for Redis');

  const target = {
    id: 'direct',
    engine: parsed.engine,
    environment: 'direct',
    connection: parsed.connection,
    allowedNamespaces,
    keyPrefix,
    allowInsecureCredentialTransport,
    expectedServerIdentity: null,
  };
  target.targetFingerprint = targetFingerprint(target, parsed.credential.username);
  return {
    target,
    credential: { ...parsed.credential, mode },
    context: { target: publicConnectionTarget(target) },
  };
}
