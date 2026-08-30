---
name: mermaid-flowchart
description: Create or edit a technical workflow/flowchart from session context, natural-language processes, code paths, or Mermaid flowchart source. This is the permanent flowchart-only compatibility alias for technical-diagrams; do not use it for sequence, state, data-flow, or other diagram families.
---

# Mermaid Flowchart Compatibility Alias

Preserve the established flowchart invocation while using `technical-diagrams`
as the only authoring, validation, rendering, delivery, and visual-QA engine.
This alias is permanent and should route quietly without migration warnings.

## Route the request

1. Resolve the target from the current request, then relevant session context,
   then named files or code. Read
   [references/context-extraction.md](references/context-extraction.md) when the
   request depends on earlier discussion or repository evidence.
2. Keep this alias flowchart-only. Route an ordered process, decision tree,
   runbook, or CI/CD flow to the `workflow` family. Route a component/service
   handoff map to `architecture` only when the nodes represent system parts
   rather than process steps.
3. Preserve stable IDs, exact domain terms, labeled branches, loops, ownership
   boundaries, and exception paths. Use
   [references/flowchart-style-guide.md](references/flowchart-style-guide.md)
   for legacy intent normalization.
4. Follow `technical-diagrams/SKILL.md` from its artifact-first authoring step.
   Do not invoke another renderer or validator from this alias.

## Mermaid input

When the request includes Mermaid `flowchart` or `graph` source, translate it
through the canonical importer:

```bash
node ../technical-diagrams/bin/technical-diagrams.mjs import-mermaid input.mmd candidate.json --json
```

Add `--target architecture` only for a component map. Then validate and deliver
the typed IR with the same `technical-diagrams` CLI. Mermaid style directives
are not canonical and must not create a second rendering path.

## Artifact compatibility

- Honor an explicit destination. Otherwise use the destination rules from
  `technical-diagrams`; during `$discuss`, keep artifacts under `./discussion/`.
- The final artifact is the checked standalone HTML produced by
  `technical-diagrams`. If the user explicitly requests normalized Mermaid
  source too, preserve it as an auxiliary `.mmd` input, not as the rendered
  source of truth.
- Return the artifact path, chosen family, validation/delivery receipt, and
  truthful visual-review status exactly as required by `technical-diagrams`.
