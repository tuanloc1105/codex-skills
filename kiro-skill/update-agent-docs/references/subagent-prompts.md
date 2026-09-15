# Parallel Subagent Prompts

Spawn subagents in parallel with `spawn_run` (passing every task in one `tasks` array batch) when the discovery genuinely fans out and session policy permits delegation. Give each agent a distinct read-only discovery assignment unless you intentionally split doc edits into disjoint files. After calling `spawn_run`, end the turn and wait for the `[Subagent completion event]` messages — do not duplicate the discovery yourself while they run.

Tell all subagents, in the task text:

```text
You are not alone in the codebase. Do not revert or overwrite changes made by others. Return concise findings with exact repo-relative paths and suggested .kiro/steering/ routing. Do not edit files unless explicitly assigned a write scope.
```

Set `include_lessons=false` and `include_memory=false` for these agents (pure read-and-report, fully specified by the task text below); keep `include_project=true` (default) so they can search inside the project tree.

## Recommended Discovery Agents

### Architecture And Module Map

```text
Explore the repository architecture for Kiro steering documentation. Identify major apps/packages/modules, their purpose, key entrypoints, first files to read for each area, generated/vendor folders to avoid, and any monorepo/package boundaries. Return concise bullets with exact repo-relative paths.
```

### Workflows And Tests

```text
Explore development workflows for Kiro steering documentation. Identify install/dev/build/lint/typecheck/test commands, focused test patterns, CI workflow mapping, codegen, migrations, and verification commands. Use manifests and existing docs as evidence. Return concise bullets with exact repo-relative paths.
```

### Frontend Or Product Surface

```text
If this repo has a frontend or product UI, map routes, layouts, components, design system, state/data fetching, styling, assets, and test utilities. If not, say no frontend surface found. Return task-routing bullets with exact repo-relative paths.
```

### Backend, API, And Data

```text
If this repo has backend/API/data code, map route/controllers, services, domain models, data access, schemas, migrations, auth/authorization, jobs, and external integrations. If not, say no backend/API/data surface found. Return task-routing bullets with exact repo-relative paths.
```

### Infra, Config, And Operations

```text
Map infrastructure and operations surfaces: env config, Docker, deployment, IaC, CI/CD, release scripts, observability, runtime configuration, and runbooks. Return what future Kiro sessions should read before touching each area, with exact repo-relative paths.
```

### Existing Docs Gap Review

```text
Read the existing .kiro/steering/*.md files (if any) and compare them against the live repo structure and other AI-tooling instructions such as AGENTS.md, CLAUDE.md, .cursor/rules, copilot-instructions.md, Devin/Windsurf/Cline rules, and GEMINI.md when present. Identify stale paths, missing modules/workflows, missing docs/agent opportunities, duplicated guidance, bloated generic advice, unclear source of truth, and durable guidance worth migrating into .kiro/steering/. Return high-signal fixes with exact repo-relative paths.
```

## Synthesis Rules

- Trust specific path findings from subagents, but verify important paths before writing.
- Merge duplicate findings into one routing map.
- Treat contradictions as a signal to inspect the repo directly.
- Do not paste subagent prose wholesale into docs; rewrite into concise durable guidance.
- Keep uncertainty visible in `docs/agent/doc-gaps.md` only when it helps future sessions.
