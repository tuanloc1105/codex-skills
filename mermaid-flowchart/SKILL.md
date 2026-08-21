---
name: mermaid-flowchart
description: Create, edit, validate, and render Mermaid flowcharts from session context, natural-language processes, code paths, or existing Mermaid source. Use when the user asks to visualize a workflow or turn the current discussion into a flowchart; do not use for free-form illustrations or non-flowchart Mermaid diagram types.
---

# Mermaid Flowchart

Turn the relevant facts in the current task into a readable Mermaid flowchart and, when the environment permits, validated `.mmd` and rendered `.svg` artifacts.

## Build the diagram

1. Resolve the target from the current request first, then the relevant session context, then named files or code. Do not make the user repeat information already available. Read [references/context-extraction.md](references/context-extraction.md) when the request depends on prior discussion, evolving decisions, or code-derived behavior.
2. Separate confirmed behavior from inference. Ask a question only when a missing choice would materially change the diagram; otherwise use the narrowest reasonable assumption and disclose it.
3. Model the flow before writing Mermaid: identify start/end points, actions, decisions, labeled branches, loops, boundaries, and exceptional paths.
4. Generate a `flowchart TD` diagram by default. Use `LR` for short pipelines or when horizontal ordering is materially clearer. Follow [references/flowchart-style-guide.md](references/flowchart-style-guide.md).
5. Keep node IDs stable when editing an existing diagram. Preserve correct content and layout choices outside the requested change.
6. Before rendering unfamiliar labels, links, directives, or configuration, read [references/mermaid-safe-syntax.md](references/mermaid-safe-syntax.md).

## Write and verify artifacts

- When the user wants an artifact, write the Mermaid source to a meaningful `.mmd` path in the current workspace. Do not overwrite an existing file unless the request clearly targets it.
- Validate with `scripts/validate_mermaid.sh <input.mmd>`.
- Render SVG with `scripts/render_mermaid.sh <input.mmd> <output.svg>`. PNG and PDF are supported when requested by using the corresponding output extension.
- The scripts require an already-installed Mermaid CLI and local browser runtime; they never download dependencies. The renderer honors `MERMAID_PUPPETEER_CONFIG_FILE`, otherwise it discovers a Puppeteer-cached browser and creates a temporary config. In Codex, browser launch may require approval to rerun the same render command outside the process sandbox. If either runtime remains unavailable, still provide the Mermaid source and state that render validation was not run.
- On a Mermaid syntax failure, inspect the actual diagnostic, make a focused correction, and retry at most twice. Do not change the represented behavior merely to make rendering pass.

## Present the result

Return the diagram preview when the client supports Mermaid or local image display, link the `.mmd` and rendered artifact when created, and list only assumptions or unresolved branches that affect interpretation. Keep the explanation brief unless the user asks for a walkthrough.

For diagrams above roughly 25 nodes, prefer a high-level overview plus one or more focused diagrams instead of one dense graph.
