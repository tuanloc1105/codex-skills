import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { execFile as execFileCallback } from 'node:child_process';
import { copyFile, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { promisify } from 'node:util';
import { runtimePaths } from '../src/config/paths.js';
import { projectPaths } from '../src/config/paths.js';
import { discoverProjectContext, ProjectStore, resolveTrustedGit } from '../src/config/projects.js';

const execFile = promisify(execFileCallback);

test('project registry resolves nested paths and isolates targets by project', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const runtime = path.join(temp, 'runtime');
  const projectRoot = path.join(temp, 'workspace', 'app');
  const nested = path.join(projectRoot, 'src', 'feature');
  await mkdir(nested, { recursive: true });

  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: runtime }));
  const project = await store.initProject('Application', projectRoot);
  assert.equal((await store.resolveProject(nested)).id, project.id);

  const target = await store.addTarget(project, {
    id: 'staging', engine: 'postgresql', environment: 'staging', host: 'db.internal', port: 5432,
    database: 'application', tls: true, allowedNamespaces: ['public'],
  });
  assert.equal((await store.target(project, 'staging')).targetFingerprint, target.targetFingerprint);
  await assert.rejects(store.target(project, 'production'), { code: 'TARGET_NOT_FOUND' });
  await assert.rejects(store.initProject('Duplicate', projectRoot), { code: 'PROJECT_ALREADY_BOUND' });
});

test('target identifiers and engines are validated', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  const project = await store.initProject('Application', projectRoot);
  await assert.rejects(
    store.addTarget(project, {
      id: '../escape', engine: 'postgresql', environment: 'test', host: 'localhost', port: 5432, database: 'app',
    }),
    { code: 'INVALID_ARGUMENT' },
  );
  await assert.rejects(
    store.addTarget(project, {
      id: 'primary', engine: 'mysql', environment: 'test', host: 'localhost', port: 3306, database: 'app',
    }),
    { code: 'INVALID_ARGUMENT' },
  );
  await assert.rejects(
    store.addTarget(project, {
      id: 'unsafe-env', engine: 'postgresql', environment: 'prod\u001b[2J', host: 'localhost', port: 5432, database: 'app',
    }),
    { code: 'INVALID_ARGUMENT' },
  );
});

test('project display names reject terminal and bidi control characters', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-display-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  await assert.rejects(store.initProject('Payments\u001b[2J', projectRoot), { code: 'INVALID_ARGUMENT' });
  await assert.rejects(store.initProject('Payments\u2028FAKE', projectRoot), { code: 'INVALID_ARGUMENT' });
  await assert.rejects(store.initProject('Payments\u2029FAKE', projectRoot), { code: 'INVALID_ARGUMENT' });
  await assert.rejects(store.initProject('Payments\u202eprod', projectRoot), { code: 'INVALID_ARGUMENT' });
});

test('manifest target changes require a new fingerprint and invalidate old plans', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-tamper-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const paths = runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') });
  const store = new ProjectStore(paths);
  const project = await store.initProject('Application', projectRoot);
  await store.addTarget(project, {
    id: 'primary', engine: 'postgresql', environment: 'staging', host: 'staging.internal', port: 5432,
    database: 'app', tls: true,
  });
  const manifestPath = projectPaths(paths, project.id).manifest;
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  manifest.targets[0].connection.host = 'production.internal';
  await writeFile(manifestPath, JSON.stringify(manifest));
  await assert.rejects(store.target(project, 'primary'), { code: 'TARGET_BINDING_TAMPERED' });
});

test('concurrent target additions do not lose manifest updates', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-concurrent-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  const project = await store.initProject('Application', projectRoot);
  await Promise.all(['first', 'second'].map((id, index) => store.addTarget(project, {
    id, engine: 'postgresql', environment: 'test', host: `${id}.internal`, port: 5432 + index, database: 'app',
  })));
  assert.deepEqual((await store.listTargets(project)).map((target) => target.id).sort(), ['first', 'second']);
});

test('credential reference refuses a stale project binding revision', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-credential-race-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const paths = runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') });
  const store = new ProjectStore(paths);
  const project = await store.initProject('Application', projectRoot);
  await store.addTarget(project, {
    id: 'primary', engine: 'postgresql', environment: 'test', host: 'localhost', port: 5432, database: 'app',
  });

  const registry = JSON.parse(await readFile(paths.registry, 'utf8'));
  const current = registry.projects[0];
  current.bindingRevision = randomUUID();
  current.bindingMarker = randomUUID();
  await writeFile(paths.registry, JSON.stringify(registry));
  await writeFile(current.markerPath, JSON.stringify({
    formatVersion: 1,
    projectId: current.id,
    bindingMarker: current.bindingMarker,
    bindingRevision: current.bindingRevision,
  }));

  await assert.rejects(
    store.setCredentialReference(project, 'primary', 'read', randomUUID()),
    { code: 'PROJECT_BINDING_MISMATCH' },
  );
});

test('Oracle TCPS cannot disable certificate verification', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-oracle-tls-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  const project = await store.initProject('Application', projectRoot);
  await assert.rejects(store.addTarget(project, {
    id: 'oracle', engine: 'oracle', environment: 'test', host: 'oracle.internal', port: 1522,
    database: 'payments', tls: true, trustServerCertificate: true,
  }), { code: 'UNSUPPORTED_OPERATION' });
});

test('recreating a directory at the same path does not inherit the old project binding', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-reused-path-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  await store.initProject('Original', projectRoot);
  await rm(projectRoot, { recursive: true, force: true });
  await mkdir(projectRoot, { recursive: true });
  await assert.rejects(store.resolveProject(projectRoot), { code: 'PROJECT_BINDING_MISMATCH' });
});

test('removing the local project marker invalidates the binding without hashing normal source edits', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-marker-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  const project = await store.initProject('Original', projectRoot);
  await writeFile(path.join(projectRoot, 'normal-source-edit.txt'), 'source edits preserve project identity');
  assert.equal((await store.resolveProject(projectRoot)).id, project.id);
  await rm(project.markerPath, { force: true });
  await assert.rejects(store.resolveProject(projectRoot), { code: 'PROJECT_BINDING_MISMATCH' });
});

test('project rebind cannot be invoked from a captured non-TTY process', {
  skip: Boolean(process.stdin.isTTY || process.stderr.isTTY || process.stdout.isTTY),
}, async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-bind-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const firstRoot = path.join(temp, 'first');
  const secondRoot = path.join(temp, 'second');
  await Promise.all([mkdir(firstRoot, { recursive: true }), mkdir(secondRoot, { recursive: true })]);
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  const original = await store.initProject('Movable', firstRoot);
  await assert.rejects(store.bindProject(original.id, secondRoot), { code: 'LOCAL_TTY_REQUIRED' });
  assert.equal((await store.resolveProject(firstRoot)).id, original.id);
});

test('adding a Git remote after registration requires an explicit rebind', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-project-remote-transition-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  await execFile('git', ['init'], { cwd: projectRoot, windowsHide: true });
  const store = new ProjectStore(runtimePaths({ AGENT_DB_HOME: path.join(temp, 'runtime') }));
  await store.initProject('Original', projectRoot);
  await execFile('git', ['remote', 'add', 'origin', 'https://example.invalid/org/repo.git'], { cwd: projectRoot, windowsHide: true });
  await assert.rejects(store.resolveProject(projectRoot), { code: 'PROJECT_BINDING_MISMATCH' });
});

test('Windows Git discovery never executes a repo-local git.exe', { skip: process.platform !== 'win32' }, async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-git-hijack-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  await mkdir(projectRoot, { recursive: true });
  const fakeGit = path.join(projectRoot, 'git.exe');
  await copyFile(process.execPath, fakeGit);
  const resolved = await resolveTrustedGit(projectRoot, {
    ...process.env,
    PATH: `${projectRoot}${path.delimiter}${process.env.PATH}`,
    AGENT_DB_VAULT_PASSPHRASE: 'must-not-reach-subprocess',
  });
  assert.ok(resolved, 'A trusted Git installation should be found for this test');
  assert.notEqual(await realpath(resolved), await realpath(fakeGit));
});

test('Windows Git discovery rejects a repo-controlled sibling binary from a nested cwd', { skip: process.platform !== 'win32' }, async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-git-sibling-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const projectRoot = path.join(temp, 'workspace');
  const nested = path.join(projectRoot, 'app', 'src');
  const tools = path.join(projectRoot, 'tools');
  await Promise.all([mkdir(nested, { recursive: true }), mkdir(tools, { recursive: true })]);
  await execFile('git', ['init'], { cwd: projectRoot, windowsHide: true });
  const fakeGit = path.join(tools, 'git.exe');
  await copyFile(process.execPath, fakeGit);
  const resolved = await resolveTrustedGit(nested, {
    ...process.env,
    PATH: `${tools}${path.delimiter}${process.env.PATH}`,
  });
  assert.ok(resolved, 'A trusted Git installation should be found for this test');
  assert.notEqual(await realpath(resolved), await realpath(fakeGit));
});

test('Git environment variables cannot redirect project discovery to another repository', async (t) => {
  const temp = await mkdtemp(path.join(os.tmpdir(), 'agent-db-git-env-'));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const repository = path.join(temp, 'repository');
  const unrelated = path.join(temp, 'unrelated');
  await Promise.all([mkdir(repository, { recursive: true }), mkdir(unrelated, { recursive: true })]);
  await execFile('git', ['init'], { cwd: repository, windowsHide: true });

  const context = await discoverProjectContext(unrelated, {
    ...process.env,
    GIT_DIR: path.join(repository, '.git'),
    GIT_WORK_TREE: repository,
    GIT_CONFIG_COUNT: '1',
    GIT_CONFIG_KEY_0: 'remote.origin.url',
    GIT_CONFIG_VALUE_0: 'https://example.invalid/spoofed.git',
  });
  assert.equal(await realpath(context.root), await realpath(unrelated));
  assert.equal(context.source, 'path');
  assert.equal(context.remoteFingerprint, null);
});
