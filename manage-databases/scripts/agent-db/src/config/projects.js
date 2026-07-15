import { createHash, randomUUID } from 'node:crypto';
import { execFile as execFileCallback } from 'node:child_process';
import { access, constants, realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { AgentDbError, invariant } from '../core/errors.js';
import { atomicWriteInExistingDirectory, atomicWriteJson, readJson, removeIfExists, validateDisplayText, validateIdentifier, validateUuid, withFileLock } from '../core/fs.js';
import { readVisibleLine, requireTty } from '../security/secret-input.js';
import { projectPaths } from './paths.js';

const execFile = promisify(execFileCallback);
const ENGINES = new Set(['oracle', 'mongodb', 'sqlserver', 'postgresql', 'redis']);

function hash(value) {
  return createHash('sha256').update(value).digest('hex');
}

function normalizeGitRemote(value) {
  const remote = value.trim();
  try {
    const parsed = new URL(remote);
    parsed.username = '';
    parsed.password = '';
    parsed.search = '';
    parsed.hash = '';
    parsed.hostname = parsed.hostname.toLowerCase();
    parsed.pathname = parsed.pathname.replace(/\/+$/, '');
    return parsed.toString();
  } catch {
    const scp = remote.match(/^(?:[^@/\s]+@)?([^:/\s]+):(.+)$/);
    if (scp) return `${scp[1].toLowerCase()}:${scp[2].replace(/\/+$/, '')}`;
    return remote.replace(/\/+$/, '');
  }
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

export function computeTargetFingerprint(target) {
  return hash(JSON.stringify(canonicalize({
    id: target.id,
    engine: target.engine,
    environment: target.environment,
    connection: target.connection,
    allowedNamespaces: target.allowedNamespaces || [],
    keyPrefix: target.keyPrefix || null,
    expectedServerIdentity: target.expectedServerIdentity || null,
  })));
}

function validateRedisKeyPrefix(value) {
  const keyPrefix = validateDisplayText(value, 'Redis key prefix');
  invariant(Buffer.byteLength(keyPrefix, 'utf8') <= 256, 'INVALID_ARGUMENT', 'Redis key prefix exceeds 256 UTF-8 bytes');
  invariant(!['*', '?', '[', ']', '\\'].some((character) => keyPrefix.includes(character)), 'INVALID_ARGUMENT', 'Redis key prefix cannot contain glob metacharacters');
  return keyPrefix;
}

function normalizePath(value) {
  const resolved = path.resolve(value).replace(/[\\/]+$/, '');
  return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

function isInside(candidate, root) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

async function filesystemFingerprint(root) {
  const information = await stat(root, { bigint: true });
  return hash(JSON.stringify({
    device: information.dev.toString(),
    inode: information.ino.toString(),
    birthtimeNs: information.birthtimeNs.toString(),
  }));
}

async function readBindingMarker(markerPath) {
  const marker = await readJson(markerPath, null);
  if (!marker) return null;
  invariant(marker.formatVersion === 1, 'PROJECT_MARKER_INVALID', 'Unsupported project binding marker format');
  validateUuid(marker.projectId, 'marker project id');
  validateUuid(marker.bindingMarker, 'binding marker id');
  validateUuid(marker.bindingRevision, 'marker binding revision');
  return marker;
}

function markerMatches(project, marker) {
  return marker
    && marker.projectId === project.id
    && marker.bindingMarker === project.bindingMarker
    && marker.bindingRevision === project.bindingRevision;
}

async function writeBindingMarker(markerPath, project) {
  await atomicWriteInExistingDirectory(markerPath, `${JSON.stringify({
    formatVersion: 1,
    projectId: project.id,
    bindingMarker: project.bindingMarker,
    bindingRevision: project.bindingRevision,
  }, null, 2)}\n`);
}

async function removeMatchingMarker(project) {
  if (!project.markerPath) return;
  const marker = await readBindingMarker(project.markerPath);
  if (markerMatches(project, marker)) await removeIfExists(project.markerPath);
}

function scrubbedSubprocessEnv(env) {
  const clean = Object.fromEntries(
    Object.entries(env).filter(([key]) => {
      const upper = key.toUpperCase();
      return !upper.startsWith('AGENT_DB_') && !upper.startsWith('GIT_');
    }),
  );
  return { ...clean, GIT_TERMINAL_PROMPT: '0', GCM_INTERACTIVE: 'Never' };
}

async function enclosingGitBoundary(cwd) {
  let current = await realpath(cwd);
  while (true) {
    try {
      await access(path.join(current, '.git'));
      return normalizePath(current);
    } catch (error) {
      if (error?.code !== 'ENOENT') return normalizePath(current);
      const parent = path.dirname(current);
      if (parent === current) return normalizePath(await realpath(cwd));
      current = parent;
    }
  }
}

export async function resolveTrustedGit(cwd, env = process.env) {
  const untrustedRoot = await enclosingGitBoundary(cwd);
  const names = process.platform === 'win32' ? ['git.exe'] : ['git'];
  for (const rawEntry of String(env.PATH || '').split(path.delimiter)) {
    const entry = rawEntry.trim().replace(/^"|"$/g, '');
    if (!entry || !path.isAbsolute(entry)) continue;
    for (const name of names) {
      const candidate = path.join(entry, name);
      try {
        await access(candidate, constants.X_OK);
        const actual = await realpath(candidate);
        if (isInside(normalizePath(actual), untrustedRoot)) continue;
        return actual;
      } catch {
        // Keep scanning trusted absolute PATH entries.
      }
    }
  }
  return null;
}

async function gitValue(cwd, args, env = process.env, trustedGit = undefined) {
  try {
    const git = trustedGit === undefined ? await resolveTrustedGit(cwd, env) : trustedGit;
    if (!git) return undefined;
    const { stdout } = await execFile(git, ['-C', cwd, ...args], {
      cwd: path.dirname(git),
      env: scrubbedSubprocessEnv(env),
      timeout: 5000,
      windowsHide: true,
    });
    return stdout.trim() || undefined;
  } catch {
    return undefined;
  }
}

export async function discoverProjectContext(cwd = process.cwd(), env = process.env) {
  const actualCwd = await realpath(cwd);
  const trustedGit = await resolveTrustedGit(actualCwd, env);
  const gitRoot = await gitValue(actualCwd, ['rev-parse', '--show-toplevel'], env, trustedGit);
  const root = await realpath(gitRoot || actualCwd);
  const remote = gitRoot ? await gitValue(root, ['config', '--local', '--get', 'remote.origin.url'], env, trustedGit) : undefined;
  const gitDirectory = gitRoot ? await gitValue(root, ['rev-parse', '--absolute-git-dir'], env, trustedGit) : undefined;
  const markerPath = gitDirectory
    ? path.join(await realpath(gitDirectory), 'agent-db-project.json')
    : path.join(root, '.agent-db-project.json');
  return {
    root,
    normalizedRoot: normalizePath(root),
    remoteFingerprint: remote ? hash(normalizeGitRemote(remote)) : null,
    filesystemFingerprint: await filesystemFingerprint(root),
    markerPath,
    marker: await readBindingMarker(markerPath),
    source: gitRoot ? 'git' : 'path',
  };
}

function emptyManifest(projectId) {
  return { version: 1, projectId, targets: [] };
}

export class ProjectStore {
  constructor(paths) {
    this.paths = paths;
  }

  async registry() {
    const registry = await readJson(this.paths.registry, { version: 1, projects: [] });
    invariant(registry.version === 1 && Array.isArray(registry.projects), 'CONFIG_INVALID', 'Unsupported project registry format');
    for (const project of registry.projects) validateUuid(project.id, 'project id');
    for (const project of registry.projects) {
      validateUuid(project.bindingRevision, 'project binding revision');
      validateUuid(project.bindingMarker, 'project binding marker');
      invariant(validateDisplayText(project.name, 'project name') === project.name, 'CONFIG_INVALID', 'Project name is not canonical');
      invariant(typeof project.filesystemFingerprint === 'string' && project.filesystemFingerprint, 'CONFIG_INVALID', 'Project filesystem fingerprint is missing');
      invariant(typeof project.markerPath === 'string' && path.isAbsolute(project.markerPath), 'CONFIG_INVALID', 'Project marker path must be absolute');
    }
    return registry;
  }

  async saveRegistry(registry) {
    await atomicWriteJson(this.paths.registry, registry);
  }

  async initProject(name, cwd = process.cwd()) {
    const projectName = validateDisplayText(name, 'project name');
    const context = await discoverProjectContext(cwd);
    return withFileLock(`${this.paths.registry}.lock`, async () => {
      const registry = await this.registry();
      const existing = registry.projects.find((project) => normalizePath(project.root) === context.normalizedRoot);
      invariant(!existing, 'PROJECT_ALREADY_BOUND', 'This project root is already registered', { projectId: existing?.id });
      invariant(!context.marker, 'PROJECT_MARKER_CONFLICT', 'This project root already contains an agent-db binding marker');

      const now = new Date().toISOString();
      const project = {
        id: randomUUID(),
        bindingRevision: randomUUID(),
        bindingMarker: randomUUID(),
        name: projectName,
        root: context.root,
        remoteFingerprint: context.remoteFingerprint,
        filesystemFingerprint: context.filesystemFingerprint,
        markerPath: context.markerPath,
        bindingSource: context.source,
        createdAt: now,
        updatedAt: now,
      };
      await writeBindingMarker(context.markerPath, project);
      await atomicWriteJson(projectPaths(this.paths, project.id).manifest, emptyManifest(project.id));
      registry.projects.push(project);
      await this.saveRegistry(registry);
      return project;
    });
  }

  async listProjects() {
    return (await this.registry()).projects;
  }

  async bindProject(projectId, cwd = process.cwd()) {
    requireTty({ input: process.stdin, output: process.stderr });
    invariant(process.stdout.isTTY, 'LOCAL_TTY_REQUIRED', 'Project binding refuses captured or redirected stdout');
    validateUuid(projectId, 'project id');
    const phrase = `BIND ${projectId} TO THIS PROJECT`;
    const confirmation = await readVisibleLine(`Type "${phrase}" to move this database binding here: `);
    invariant(confirmation === phrase, 'USER_CONFIRMATION_REQUIRED', 'Project binding confirmation did not match');
    const context = await discoverProjectContext(cwd);
    return withFileLock(`${this.paths.registry}.lock`, async () => {
      const registry = await this.registry();
      const project = registry.projects.find((entry) => entry.id === projectId);
      invariant(project, 'PROJECT_NOT_FOUND', `Unknown project: ${projectId}`);
      const conflict = registry.projects.find((entry) => entry.id !== projectId && normalizePath(entry.root) === context.normalizedRoot);
      invariant(!conflict, 'PROJECT_BINDING_CONFLICT', 'The current root is already bound to another project', { projectId: conflict?.id });
      invariant(
        !context.marker || markerMatches(project, context.marker),
        'PROJECT_MARKER_CONFLICT',
        'The destination already belongs to a different agent-db project binding',
      );
      const previous = { ...project };
      const manifestPath = projectPaths(this.paths, project.id).manifest;
      return withFileLock(`${manifestPath}.lock`, async () => {
        project.root = context.root;
        project.bindingRevision = randomUUID();
        project.bindingMarker = randomUUID();
        project.remoteFingerprint = context.remoteFingerprint;
        project.filesystemFingerprint = context.filesystemFingerprint;
        project.markerPath = context.markerPath;
        project.bindingSource = context.source;
        project.updatedAt = new Date().toISOString();
        await writeBindingMarker(context.markerPath, project);
        await this.saveRegistry(registry);
        if (normalizePath(previous.markerPath) !== normalizePath(project.markerPath)) {
          await removeMatchingMarker(previous);
        }
        return project;
      });
    });
  }

  async assertStoredBinding(project) {
    const marker = await readBindingMarker(project.markerPath);
    invariant(markerMatches(project, marker), 'PROJECT_BINDING_MISMATCH', 'Project binding marker is missing or does not match', {
      projectId: project.id,
      projectName: project.name,
    });
  }

  async resolveProject(cwd = process.cwd()) {
    const context = await discoverProjectContext(cwd);
    const registry = await this.registry();
    const rootMatch = registry.projects.find((project) => normalizePath(project.root) === context.normalizedRoot);

    if (rootMatch) {
      if (
        rootMatch.remoteFingerprint !== context.remoteFingerprint
        || rootMatch.filesystemFingerprint !== context.filesystemFingerprint
        || normalizePath(rootMatch.markerPath) !== normalizePath(context.markerPath)
        || !markerMatches(rootMatch, context.marker)
      ) {
        throw new AgentDbError('PROJECT_BINDING_MISMATCH', 'Project marker, filesystem, or Git remote fingerprint does not match the registered project', {
          projectId: rootMatch.id,
          projectName: rootMatch.name,
        });
      }
      return rootMatch;
    }

    if (context.source === 'path') {
      const candidates = registry.projects
        .filter((project) => isInside(context.normalizedRoot, normalizePath(project.root)))
        .sort((left, right) => right.root.length - left.root.length);
      if (candidates.length === 1) return candidates[0];
      if (candidates.length > 1 && candidates[0].root.length === candidates[1].root.length) {
        throw new AgentDbError('PROJECT_CONTEXT_REQUIRED', 'Multiple project bindings match the current directory');
      }
      if (candidates[0]) {
        const candidate = candidates[0];
        const currentFingerprint = await filesystemFingerprint(await realpath(candidate.root));
        invariant(
          candidate.filesystemFingerprint === currentFingerprint,
          'PROJECT_BINDING_MISMATCH',
          'Project root filesystem fingerprint changed after registration',
          { projectId: candidate.id, projectName: candidate.name },
        );
        await this.assertStoredBinding(candidate);
        return candidate;
      }
    }

    throw new AgentDbError('PROJECT_CONTEXT_REQUIRED', 'The current directory is not bound to an agent-db project');
  }

  async manifest(projectId) {
    validateUuid(projectId, 'project id');
    const filePath = projectPaths(this.paths, projectId).manifest;
    const manifest = await readJson(filePath, emptyManifest(projectId));
    invariant(manifest.version === 1 && manifest.projectId === projectId && Array.isArray(manifest.targets), 'CONFIG_INVALID', 'Invalid project manifest');
    for (const target of manifest.targets) {
      validateIdentifier(target.id, 'target id');
      validateDisplayText(target.environment, 'target environment');
      validateDisplayText(target.connection?.host, 'target host');
      validateDisplayText(target.connection?.database, 'target database');
      if (target.connection?.service) validateDisplayText(target.connection.service, 'Oracle service');
      if (target.connection?.authSource) validateDisplayText(target.connection.authSource, 'MongoDB auth source');
      if (target.expectedServerIdentity) validateDisplayText(target.expectedServerIdentity, 'expected server identity');
      for (const namespace of target.allowedNamespaces || []) validateDisplayText(namespace, 'namespace');
      if (target.keyPrefix) validateRedisKeyPrefix(target.keyPrefix);
      if (target.engine === 'redis') {
        invariant(/^(?:0|[1-9]\d*)$/.test(target.connection.database), 'CONFIG_INVALID', 'Redis target database must be a canonical non-negative integer');
        invariant(Number.isSafeInteger(Number(target.connection.database)), 'CONFIG_INVALID', 'Redis target database is outside the supported integer range');
        invariant(target.keyPrefix, 'CONFIG_INVALID', 'Redis target requires a key prefix');
        invariant((target.allowedNamespaces || []).length === 0, 'CONFIG_INVALID', 'Redis target cannot use MongoDB namespaces');
        invariant(target.connection.trustServerCertificate !== true, 'CONFIG_INVALID', 'Redis TLS certificate verification cannot be disabled');
      }
      invariant(
        target.targetFingerprint === computeTargetFingerprint(target),
        'TARGET_BINDING_TAMPERED',
        `Target binding fingerprint is invalid: ${target.id}`,
      );
    }
    return manifest;
  }

  async saveManifest(manifest) {
    await atomicWriteJson(projectPaths(this.paths, manifest.projectId).manifest, manifest);
  }

  async withProjectManifestLock(project, task) {
    return withFileLock(`${this.paths.registry}.lock`, async () => {
      const registry = await this.registry();
      const current = registry.projects.find((entry) => entry.id === project.id);
      invariant(current, 'PROJECT_NOT_FOUND', `Unknown project: ${project.id}`);
      invariant(current.bindingRevision === project.bindingRevision, 'PROJECT_BINDING_MISMATCH', 'Project binding changed before the operation lock was acquired');
      await this.assertStoredBinding(current);
      const manifestPath = projectPaths(this.paths, current.id).manifest;
      return withFileLock(`${manifestPath}.lock`, () => task(current));
    });
  }

  async addTarget(project, input) {
    const id = validateIdentifier(input.id, 'target id');
    invariant(ENGINES.has(input.engine), 'INVALID_ARGUMENT', `Unsupported engine: ${input.engine}`);
    const environment = validateDisplayText(input.environment, 'target environment');
    const host = validateDisplayText(input.host, 'target host');
    const database = validateDisplayText(input.database, 'target database or Oracle service');
    const service = input.service ? validateDisplayText(input.service, 'Oracle service') : undefined;
    const authSource = input.authSource ? validateDisplayText(input.authSource, 'MongoDB auth source') : undefined;
    const expectedServerIdentity = input.expectedServerIdentity
      ? validateDisplayText(input.expectedServerIdentity, 'expected server identity')
      : null;
    const allowedNamespaces = (input.allowedNamespaces || []).map((namespace) => validateDisplayText(namespace, 'namespace'));
    const keyPrefix = input.keyPrefix ? validateRedisKeyPrefix(input.keyPrefix) : null;
    invariant(Number.isSafeInteger(input.port) && input.port > 0 && input.port <= 65535, 'INVALID_ARGUMENT', 'Target port is invalid');
    invariant(
      !(['oracle', 'redis'].includes(input.engine) && input.trustServerCertificate),
      'UNSUPPORTED_OPERATION',
      `${input.engine === 'redis' ? 'Redis TLS' : 'Oracle TCPS'} certificate verification cannot be disabled by this CLI`,
    );
    if (input.engine === 'redis') {
      invariant(/^(?:0|[1-9]\d*)$/.test(database) && Number.isSafeInteger(Number(database)), 'INVALID_ARGUMENT', 'Redis database must be a canonical non-negative integer');
      invariant(keyPrefix, 'INVALID_ARGUMENT', 'Redis targets require --key-prefix');
      invariant(allowedNamespaces.length === 0, 'INVALID_ARGUMENT', 'Redis targets cannot use MongoDB namespaces');
      invariant(!service && !authSource, 'INVALID_ARGUMENT', 'Redis targets do not support Oracle service or MongoDB auth source options');
    } else {
      invariant(!keyPrefix, 'INVALID_ARGUMENT', '--key-prefix is only supported for Redis targets');
    }

    const connection = {
      host,
      port: input.port,
      database,
      ...(service ? { service } : {}),
      tls: input.tls,
      encrypt: input.encrypt,
      trustServerCertificate: input.trustServerCertificate,
      ...(authSource ? { authSource } : {}),
    };
    const manifestPath = projectPaths(this.paths, project.id).manifest;
    return withFileLock(`${manifestPath}.lock`, async () => {
      const manifest = await this.manifest(project.id);
      invariant(!manifest.targets.some((target) => target.id === id), 'TARGET_ALREADY_EXISTS', `Target already exists: ${id}`);
      const now = new Date().toISOString();
      const target = {
        id,
        engine: input.engine,
        environment,
        connection,
        allowedNamespaces,
        ...(keyPrefix ? { keyPrefix } : {}),
        expectedServerIdentity,
        credentials: { read: null, mutation: null },
        createdAt: now,
        updatedAt: now,
      };
      target.targetFingerprint = computeTargetFingerprint(target);
      manifest.targets.push(target);
      await this.saveManifest(manifest);
      return target;
    });
  }

  async listTargets(project) {
    return (await this.manifest(project.id)).targets;
  }

  async target(project, targetId) {
    const target = (await this.manifest(project.id)).targets.find((entry) => entry.id === targetId);
    invariant(target, 'TARGET_NOT_FOUND', `Unknown target for project ${project.name}: ${targetId}`);
    return target;
  }

  async setCredentialReference(project, targetId, mode, credentialId) {
    invariant(mode === 'read' || mode === 'mutation', 'INVALID_ARGUMENT', 'Credential mode must be read or mutation');
    validateUuid(credentialId, 'credential id');
    return withFileLock(`${this.paths.registry}.lock`, async () => {
      const registry = await this.registry();
      const current = registry.projects.find((entry) => entry.id === project.id);
      invariant(current, 'PROJECT_NOT_FOUND', `Unknown project: ${project.id}`);
      invariant(current.bindingRevision === project.bindingRevision, 'PROJECT_BINDING_MISMATCH', 'Project binding changed while the credential was being verified');
      await this.assertStoredBinding(current);
      const manifestPath = projectPaths(this.paths, project.id).manifest;
      return withFileLock(`${manifestPath}.lock`, async () => {
        const manifest = await this.manifest(project.id);
        const target = manifest.targets.find((entry) => entry.id === targetId);
        invariant(target, 'TARGET_NOT_FOUND', `Unknown target: ${targetId}`);
        target.credentials[mode] = credentialId;
        target.updatedAt = new Date().toISOString();
        await this.saveManifest(manifest);
        return target;
      });
    });
  }
}
