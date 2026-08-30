import fs from 'node:fs';

export class MermaidImportError extends Error {
  constructor(code, message, line = null, supportedFixes = []) {
    super(message);
    this.name = 'MermaidImportError';
    this.diagnostic = { code, severity: 'error', message, subject: line ? { line } : {}, supportedFixes };
  }
}

const clean = (value) => value.trim().replace(/^['"]|['"]$/g, '');
const id = (value, fallback = 'item') => {
  const normalized = value.normalize('NFKD').replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');
  return /^[a-zA-Z]/.test(normalized) ? normalized : `${fallback}-${normalized || '1'}`;
};
const titleMeta = (title) => ({ title, quality_profile: 'showcase' });

function linesOf(source) {
  return source.replace(/\r\n?/g, '\n').split('\n')
    .map((text, index) => ({ text: text.trim(), line: index + 1 }))
    .filter(({ text }) => text && !text.startsWith('%%'));
}

function nodeToken(token) {
  const match = token.trim().match(/^([\w-]+)(?:\s*(?:\[([^\]]+)\]|\(([^)]+)\)|\{([^}]+)\}))?$/u);
  if (!match) return null;
  return { sourceId: match[1], id: id(match[1], 'node'), label: clean(match[2] || match[3] || match[4] || match[1]) };
}

function importFlowchart(rows, target) {
  const nodes = new Map();
  const edges = [];
  let direction = 'LR';
  let inSubgraph = false;
  for (const row of rows) {
    if (/^(flowchart|graph)\b/i.test(row.text)) {
      direction = row.text.split(/\s+/)[1] || 'LR';
      continue;
    }
    if (/^subgraph\b/i.test(row.text)) { inSubgraph = true; continue; }
    if (/^end$/i.test(row.text)) { inSubgraph = false; continue; }
    const match = row.text.match(/^(.+?)\s*(-->|---|-.->|==>)\s*(?:\|([^|]+)\|\s*)?(.+)$/u);
    if (!match) {
      const standalone = nodeToken(row.text);
      if (standalone) { nodes.set(standalone.sourceId, standalone); continue; }
      throw new MermaidImportError('mermaid/unsupported-syntax', `Unsupported flowchart statement: ${row.text}`, row.line,
        ['use one node or one A --> B relationship per line', 'remove Mermaid styling directives']);
    }
    const from = nodeToken(match[1]);
    const to = nodeToken(match[4]);
    if (!from || !to) throw new MermaidImportError('mermaid/malformed-edge', 'Flowchart edge endpoints could not be parsed.', row.line,
      ['use stable alphanumeric node IDs with optional [labels]']);
    const remember = (node) => {
      const current = nodes.get(node.sourceId);
      if (!current || node.label !== node.sourceId) nodes.set(node.sourceId, node);
    };
    remember(from); remember(to);
    edges.push({ from: from.id, to: to.id, ...(match[3] ? { label: clean(match[3]) } : {}), ...(inSubgraph ? { role: 'branch' } : {}) });
  }
  if (!nodes.size) throw new MermaidImportError('mermaid/empty', 'The Mermaid flowchart contains no nodes.', null, ['add at least one node and relationship']);
  const ordered = [...nodes.values()];
  if (target === 'architecture') {
    return { schema_version: 1, diagram_type: 'architecture', meta: { ...titleMeta('Imported architecture'), viewBox: [1000, Math.max(420, ordered.length * 90)] },
      components: ordered.map((node, index) => ({ id: node.id, type: 'backend', label: node.label, pos: [100 + (index % 3) * 280, 100 + Math.floor(index / 3) * 130], size: [190, 74] })),
      connections: edges.map((edge) => ({ ...edge, route: 'auto' })), cards: [] };
  }
  return { schema_version: 2, diagram_type: 'workflow', meta: titleMeta('Imported workflow'),
    lanes: [{ id: 'main', label: 'Workflow' }],
    nodes: ordered.map((node, index) => ({ id: node.id, lane: 'main', col: index % 6, type: 'backend', label: node.label, ...(index >= 6 ? { yOffset: Math.floor(index / 6) * 100 } : {}) })),
    edges: edges.map((edge) => ({ ...edge, role: edge.role || 'main', route: 'auto' })),
    mainPath: ordered.slice(0, Math.max(2, ordered.length)).map((node) => node.id), cards: [] };
}

function importSequence(rows) {
  const participants = new Map(); const messages = [];
  for (const row of rows.slice(1)) {
    const participant = row.text.match(/^(participant|actor)\s+([\w-]+)(?:\s+as\s+(.+))?$/i);
    if (participant) { participants.set(participant[2], { id: id(participant[2], 'participant'), label: clean(participant[3] || participant[2]) }); continue; }
    const message = row.text.match(/^([a-zA-Z_][\w-]*?)\s*(-->>?|->>?)\s*([\w-]+)\s*:\s*(.+)$/u);
    if (message) {
      for (const key of [message[1], message[3]]) if (!participants.has(key)) participants.set(key, { id: id(key, 'participant'), label: key });
      messages.push({ id: `message-${messages.length + 1}`, from: id(message[1]), to: id(message[3]), y: 180 + messages.length * 44, label: clean(message[4]), variant: message[2].includes('--') ? 'return' : 'default' });
      continue;
    }
    if (/^(alt|else|end|loop|opt|par|and|rect|note|activate|deactivate)\b/i.test(row.text)) {
      throw new MermaidImportError('mermaid/lossy-construct', `The sequence construct is not safely translatable: ${row.text}`, row.line,
        ['flatten the construct into explicit messages', 'author the typed sequence JSON directly']);
    }
    throw new MermaidImportError('mermaid/unsupported-syntax', `Unsupported sequence statement: ${row.text}`, row.line, ['use participant and message statements']);
  }
  return { schema_version: 1, diagram_type: 'sequence', meta: titleMeta('Imported sequence'), participants: [...participants.values()].map((participant) => ({ ...participant, type: 'backend' })), messages, cards: [] };
}

function importState(rows) {
  const states = new Map(); const transitions = [];
  for (const row of rows.slice(1)) {
    const alias = row.text.match(/^state\s+"([^"]+)"\s+as\s+([\w-]+)$/u);
    if (alias) { states.set(alias[2], { id: id(alias[2], 'state'), label: alias[1] }); continue; }
    const transition = row.text.match(/^([\w*_-]+)\s*-->\s*([\w*_-]+)(?:\s*:\s*(.+))?$/u);
    if (!transition) throw new MermaidImportError('mermaid/unsupported-syntax', `Unsupported state statement: ${row.text}`, row.line, ['use state aliases and A --> B transitions']);
    for (const key of [transition[1], transition[2]]) if (key !== '[*]' && !states.has(key)) states.set(key, { id: id(key, 'state'), label: key });
    if (transition[1] !== '[*]' && transition[2] !== '[*]') transitions.push({ from: id(transition[1]), to: id(transition[2]), ...(transition[3] ? { label: clean(transition[3]) } : {}) });
  }
  const ordered = [...states.values()];
  return { schema_version: 1, diagram_type: 'lifecycle', meta: titleMeta('Imported lifecycle'), lanes: [{ id: 'main', label: 'Lifecycle' }],
    states: ordered.map((state, index) => ({ ...state, type: index === 0 ? 'start' : index === ordered.length - 1 ? 'success' : 'active', lane: 'main', col: Math.min(index, 4) })),
    transitions, cards: [] };
}

export function importMermaid(source, { target } = {}) {
  const rows = linesOf(source);
  if (!rows.length) throw new MermaidImportError('mermaid/empty', 'Mermaid input is empty.', null, ['provide a supported Mermaid diagram']);
  const header = rows[0].text;
  if (/^(flowchart|graph)\b/i.test(header)) return importFlowchart(rows, target === 'architecture' ? 'architecture' : 'workflow');
  if (/^sequenceDiagram$/i.test(header)) return importSequence(rows);
  if (/^stateDiagram(?:-v2)?$/i.test(header)) return importState(rows);
  throw new MermaidImportError('mermaid/unsupported-family', `Unsupported Mermaid family: ${header.split(/\s+/)[0]}`,
    rows[0].line, ['use flowchart/graph, sequenceDiagram, or stateDiagram-v2', 'author typed JSON for another diagram family']);
}

export function importMermaidFile(input, options = {}) { return importMermaid(fs.readFileSync(input, 'utf8'), options); }
