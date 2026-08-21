# Flowchart Style Guide

## Structure

- Use one action per process node.
- Phrase decision nodes as concise questions and label outgoing branches, such as `Yes`/`No`, `Success`/`Failure`, or domain-specific outcomes.
- Show retries and loops explicitly; do not duplicate the repeated sequence.
- Use terminal nodes for meaningful entry and exit states.
- Use `subgraph` only for real ownership, phase, service, or system boundaries.
- Keep the happy path visually direct and attach error or exceptional paths as branches.

## Naming

- Use short, semantic node IDs such as `validateOrder` rather than positional IDs such as `node7`.
- Keep existing IDs when editing unless an ID has become misleading.
- Use the terminology already established by the user or codebase.
- Keep labels compact. Move explanations and assumptions outside the graph.

## Layout

- Default to `flowchart TD` for decision-heavy or long processes.
- Use `flowchart LR` for short pipelines and architecture-like handoffs.
- Prefer connected edges over spacing tricks or invisible links.
- Split a graph near 25 nodes when a reader would otherwise need to trace many crossing edges.

## Styling

Prefer Mermaid's default theme and semantic shapes over extensive custom CSS. Add classes or theme configuration only when the user asks for branded styling or when a small visual distinction materially improves comprehension. Ensure meaning remains understandable without color.
