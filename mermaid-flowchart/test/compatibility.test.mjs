import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { importMermaid } from '../../technical-diagrams/scripts/import-mermaid.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const skill = fs.readFileSync(path.join(root, 'SKILL.md'), 'utf8');

test('legacy alias remains flowchart-only and permanent', () => {
  assert.match(skill, /permanent/i);
  assert.match(skill, /flowchart-only/i);
  assert.doesNotMatch(skill, /deprecat(?:e|ion)/i);
});

test('legacy alias routes to the sole technical-diagrams engine', () => {
  assert.match(skill, /technical-diagrams\/SKILL\.md/);
  assert.match(skill, /import-mermaid/);
  assert.equal(fs.existsSync(path.join(root, 'scripts/render_mermaid.sh')), false);
  assert.equal(fs.existsSync(path.join(root, 'scripts/validate_mermaid.sh')), false);
});

test('legacy process and component prompts select equivalent canonical families', () => {
  assert.equal(importMermaid('flowchart TD\nstart --> done').diagram_type, 'workflow');
  assert.equal(importMermaid('flowchart LR\nweb --> api', { target: 'architecture' }).diagram_type, 'architecture');
});
