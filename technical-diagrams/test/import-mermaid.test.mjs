import assert from 'node:assert/strict';
import test from 'node:test';
import { importMermaid, MermaidImportError } from '../scripts/import-mermaid.mjs';
import { architecture, lifecycle, sequence, workflow } from '../renderers/shared/generated-validators.mjs';

test('flowchart preserves Unicode labels, branches, and direction', () => {
  const result = importMermaid('flowchart LR\nA[Nhận yêu cầu] -->|hợp lệ| B{Kiểm tra}\nB --> C[Hoàn tất]');
  assert.equal(result.diagram_type, 'workflow');
  assert.ok(result.nodes[0]);
  assert.deepEqual(result.nodes.map((node) => node.label), ['Nhận yêu cầu', 'Kiểm tra', 'Hoàn tất']);
  assert.equal(result.edges[0].label, 'hợp lệ');
});

test('flowchart can target architecture without preserving Mermaid styling', () => {
  const result = importMermaid('graph TD\nweb[Web] --> api[API]', { target: 'architecture' });
  assert.equal(result.diagram_type, 'architecture');
  assert.deepEqual(result.connections.map(({ from, to }) => [from, to]), [['web', 'api']]);
});

test('sequence preserves participants, return messages, and long labels', () => {
  const result = importMermaid('sequenceDiagram\nparticipant U as Người dùng\nU->>API: gửi yêu cầu rất dài\nAPI-->>U: kết quả');
  assert.equal(result.diagram_type, 'sequence');
  assert.equal(result.messages[1].variant, 'return');
});

test('state diagram preserves retry transitions', () => {
  const result = importMermaid('stateDiagram-v2\nIdle --> Running: start\nRunning --> Idle: retry\nRunning --> Done: finish');
  assert.equal(result.diagram_type, 'lifecycle');
  assert.equal(result.transitions.find(({ label }) => label === 'retry').to, 'Idle');
});

test('unsupported family and lossy constructs return stable diagnostics', () => {
  assert.throws(() => importMermaid('classDiagram\nA <|-- B'), (error) => error instanceof MermaidImportError && error.diagnostic.code === 'mermaid/unsupported-family');
  assert.throws(() => importMermaid('sequenceDiagram\nalt success'), (error) => error.diagnostic.code === 'mermaid/lossy-construct');
});

test('every translated family validates against its generated schema', () => {
  const cases = [
    [workflow, importMermaid('flowchart LR\nA --> B')],
    [architecture, importMermaid('flowchart LR\nA --> B', { target: 'architecture' })],
    [sequence, importMermaid('sequenceDiagram\nA->>B: hello')],
    [lifecycle, importMermaid('stateDiagram-v2\nA --> B: go')],
  ];
  for (const [validate, value] of cases) assert.equal(validate(value), true, JSON.stringify(validate.errors));
});
