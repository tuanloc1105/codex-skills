import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import { stageCleanSkill } from '../../scripts/stage-clean-skill.mjs';

const stagerPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../scripts/stage-clean-skill.mjs');

function git(root, args) {
  const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
}

function write(root, relative, content, mode = null) {
  const target = path.join(root, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content);
  if (mode !== null) fs.chmodSync(target, mode);
  return target;
}

function repositoryFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'technical-diagrams-clean-stage-'));
  write(root, 'technical-diagrams/package.json', JSON.stringify({
    name: 'technical-diagrams-fixture',
    scripts: { test: 'node --test' },
    devDependencies: { ajv: '1.0.0' },
  }));
  write(root, 'technical-diagrams/package-lock.json', '{}\n');
  write(root, 'technical-diagrams/skill-release.json', '{}\n');
  write(root, 'technical-diagrams/scripts/check-update.mjs', 'export {};\n');
  write(root, 'technical-diagrams/scripts/update-contract.mjs', 'export {};\n');
  write(root, 'technical-diagrams/renderers/shared/generated-validators.mjs', 'export {};\n');
  write(root, 'technical-diagrams/test/repository-only.test.mjs', 'throw new Error();\n');
  git(root, ['init']);
  return root;
}

test('clean staging preserves index modes and strips repository-only package metadata', () => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  try {
    write(root, 'technical-diagrams/bin/executable.mjs', '#!/usr/bin/env node\n', 0o755);
    write(root, 'technical-diagrams/runtime/test/required.dat', 'runtime fixture\n');
    git(root, ['add', 'technical-diagrams']);

    stageCleanSkill({ repoRoot: root, destination });

    assert.equal(fs.statSync(path.join(destination, 'bin', 'executable.mjs')).mode & 0o777, 0o755);
    assert.equal(fs.existsSync(path.join(destination, 'test')), false);
    assert.equal(
      fs.readFileSync(path.join(destination, 'runtime', 'test', 'required.dat'), 'utf8'),
      'runtime fixture\n',
      'only the repository-root test tree is excluded',
    );
    assert.equal(fs.existsSync(path.join(destination, 'package-lock.json')), false);
    const packageJson = JSON.parse(fs.readFileSync(path.join(destination, 'package.json'), 'utf8'));
    assert.equal(Object.hasOwn(packageJson, 'scripts'), false);
    assert.equal(Object.hasOwn(packageJson, 'devDependencies'), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('clean staging rejects a symlink in a tracked file ancestor before copying bytes', (t) => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  try {
    const runtime = path.join(root, 'technical-diagrams', 'runtime');
    write(root, 'technical-diagrams/runtime/payload.txt', 'tracked fixture\n');
    git(root, ['add', 'technical-diagrams']);
    fs.rmSync(runtime, { recursive: true });
    const external = path.join(root, 'outside-runtime');
    write(root, 'outside-runtime/payload.txt', 'external secret\n');
    try {
      fs.symlinkSync(external, runtime, process.platform === 'win32' ? 'junction' : 'dir');
    } catch (error) {
      if (['EPERM', 'EACCES', 'ENOTSUP'].includes(error?.code)) {
        t.skip(`symlinks unavailable: ${error.code}`);
        return;
      }
      throw error;
    }

    assert.throws(
      () => stageCleanSkill({ repoRoot: root, destination }),
      /refusing to package path through symlink: technical-diagrams\/runtime/,
    );
    assert.equal(fs.existsSync(destination), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('clean staging rejects tracked symlinks before reading through them', (t) => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  try {
    const external = write(root, 'outside.txt', 'private fixture\n');
    const linked = path.join(root, 'technical-diagrams', 'linked.txt');
    try {
      fs.symlinkSync(external, linked);
    } catch (error) {
      if (['EPERM', 'EACCES', 'ENOTSUP'].includes(error?.code)) {
        t.skip(`symlinks unavailable: ${error.code}`);
        return;
      }
      throw error;
    }
    git(root, ['add', 'technical-diagrams']);

    assert.throws(
      () => stageCleanSkill({ repoRoot: root, destination }),
      /refusing to package tracked symlink: technical-diagrams\/linked\.txt/,
    );
    assert.equal(fs.existsSync(destination), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('clean staging snapshots unstaged tracked bytes before a source ancestor can be swapped', (t) => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  const runtime = path.join(root, 'technical-diagrams', 'runtime');
  const external = path.join(root, 'outside-runtime');
  const originalMkdirSync = fs.mkdirSync;
  let swapped = false;
  try {
    const payload = write(root, 'technical-diagrams/runtime/payload.txt', 'indexed fixture\n');
    write(root, 'outside-runtime/payload.txt', 'external secret\n');
    git(root, ['add', 'technical-diagrams']);
    fs.writeFileSync(payload, 'unstaged working-tree fixture\n');

    const probe = path.join(root, 'symlink-probe');
    try {
      fs.symlinkSync(external, probe, process.platform === 'win32' ? 'junction' : 'dir');
      fs.rmSync(probe, { force: true });
    } catch (error) {
      if (['EPERM', 'EACCES', 'ENOTSUP'].includes(error?.code)) {
        t.skip(`symlinks unavailable: ${error.code}`);
        return;
      }
      throw error;
    }

    fs.mkdirSync = function swapSourceAfterSnapshot(target, ...args) {
      const result = originalMkdirSync.call(fs, target, ...args);
      if (!swapped && path.resolve(target) === path.resolve(destination)) {
        fs.rmSync(runtime, { recursive: true });
        fs.symlinkSync(external, runtime, process.platform === 'win32' ? 'junction' : 'dir');
        swapped = true;
      }
      return result;
    };

    stageCleanSkill({ repoRoot: root, destination });

    assert.equal(swapped, true, 'the deterministic ancestor-swap attack must run');
    assert.equal(
      fs.readFileSync(path.join(destination, 'runtime', 'payload.txt'), 'utf8'),
      'unstaged working-tree fixture\n',
      'staging keeps the tracked working-tree snapshot and never follows the replacement ancestor',
    );
  } finally {
    fs.mkdirSync = originalMkdirSync;
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('clean staging rejects a source ancestor swapped during preflight traversal', (t) => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  const runtime = path.join(root, 'technical-diagrams', 'runtime');
  const external = path.join(root, 'outside-runtime');
  const originalLstatSync = fs.lstatSync;
  let swapped = false;
  try {
    write(root, 'technical-diagrams/runtime/payload.txt', 'tracked fixture\n');
    write(root, 'outside-runtime/payload.txt', 'external secret\n');
    git(root, ['add', 'technical-diagrams']);
    const canonicalRuntime = path.join(fs.realpathSync(root), 'technical-diagrams', 'runtime');

    const probe = path.join(root, 'symlink-probe');
    try {
      fs.symlinkSync(external, probe, process.platform === 'win32' ? 'junction' : 'dir');
      fs.rmSync(probe, { force: true });
    } catch (error) {
      if (['EPERM', 'EACCES', 'ENOTSUP'].includes(error?.code)) {
        t.skip(`symlinks unavailable: ${error.code}`);
        return;
      }
      throw error;
    }

    fs.lstatSync = function swapSourceBetweenAncestorAndLeaf(target, ...args) {
      const metadata = originalLstatSync.call(fs, target, ...args);
      if (!swapped && path.resolve(target) === canonicalRuntime) {
        // Guard before mutation: recursive removal can re-enter the patched
        // lstatSync implementation on Linux.
        swapped = true;
        fs.rmSync(runtime, { recursive: true });
        fs.symlinkSync(external, runtime, process.platform === 'win32' ? 'junction' : 'dir');
      }
      return metadata;
    };

    assert.throws(
      () => stageCleanSkill({ repoRoot: root, destination }),
      /(?:tracked package path changed before it could be read: technical-diagrams\/|tracked package input is missing or unreadable: technical-diagrams\/runtime\/payload\.txt)/,
    );
    assert.equal(swapped, true, 'the deterministic mid-preflight ancestor swap must run');
    assert.equal(fs.existsSync(destination), false);
  } finally {
    fs.lstatSync = originalLstatSync;
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('clean staging reports the Git spawn error when Git cannot start', () => {
  const root = repositoryFixture();
  const destination = path.join(root, 'staged-skill');
  try {
    git(root, ['add', 'technical-diagrams']);
    const result = spawnSync(process.execPath, [
      stagerPath,
      '--root', root,
      '--dest', destination,
    ], {
      encoding: 'utf8',
      env: { ...process.env, PATH: '' },
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /unable to enumerate tracked Technical Diagrams files: .*ENOENT/);
    assert.doesNotMatch(result.stderr, /tracked Technical Diagrams paths must be valid UTF-8/);
    assert.equal(fs.existsSync(destination), false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
