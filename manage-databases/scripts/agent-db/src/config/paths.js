import os from 'node:os';
import path from 'node:path';

export function runtimePaths(env = process.env) {
  const root = path.resolve(env.AGENT_DB_HOME || path.join(os.homedir(), '.agent-db'));
  return {
    root,
    registry: path.join(root, 'registry.json'),
    vaultFormat: path.join(root, 'vault-format.json'),
    projects: path.join(root, 'projects'),
    vault: path.join(root, 'vault'),
    pending: path.join(root, 'pending'),
    audit: path.join(root, 'audit'),
  };
}

export function projectPaths(paths, projectId) {
  const root = path.join(paths.projects, projectId);
  return {
    root,
    manifest: path.join(root, 'manifest.json'),
    schema: path.join(root, 'schema'),
  };
}
