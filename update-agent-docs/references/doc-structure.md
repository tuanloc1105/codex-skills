# Documentation Structure

Use `AGENTS.md` as the concise routing index. Use `docs/agent/` for detailed maps and longer notes.

## AGENTS.md Recommended Sections

1. `# Agent Guide`
2. `## Start Here`
   - State the source of truth for agent docs.
   - Tell agents which docs to read first for common tasks.
   - Include command/tool routing rules that future sessions must obey.
3. `## Project Map`
   - List major packages, modules, apps, and folders with one-line purpose and first files to read.
   - Link to `docs/agent/module-index.md` for detail when needed.
4. `## Common Workflows`
   - Dev, build, test, lint, typecheck, migrations, codegen, release, and focused checks.
   - Link to `docs/agent/workflows.md` for full command details.
5. `## Task Routing`
   - "When changing X, read Y first" bullets for frontend, backend, data, auth, config, CI, docs, tests, and infra.
6. `## Conventions And Guardrails`
   - Repo-specific coding conventions, generated-file rules, testing expectations, and safety constraints.
7. `## Read On Demand`
   - Link to detailed `docs/agent/` files and explain when to open each one.

## docs/agent/ Recommended Files

- `docs/agent/project-map.md`: repository structure, package boundaries, and first-read files.
- `docs/agent/module-index.md`: detailed module/package/file routing.
- `docs/agent/workflows.md`: commands, checks, local setup, CI mapping, and focused test guidance.
- `docs/agent/testing.md`: test strategy, fixtures, mocks, and how to run narrow checks.
- `docs/agent/operations.md`: deploy, migrations, environment, codegen, release, and runbooks.
- `docs/agent/doc-gaps.md`: optional temporary notes for uncertain findings or follow-up documentation gaps.

Create only the files that are useful for the repo. Do not create empty placeholder docs.

## Writing Style

- Every line in `AGENTS.md` should pass this test: would removing it cause a future agent to make a likely mistake? If no, cut it or move it to `docs/agent/`.
- Prefer exact paths over broad descriptions.
- Prefer routing instructions over narrative: "For API auth changes, read `src/auth/...` then `src/api/...`."
- Keep long inventories out of `AGENTS.md`; link to `docs/agent/`.
- Mark generated, vendored, build, cache, and artifact directories as "do not edit" when relevant.
- Include verification commands only after checking they exist in manifests or docs.
- Do not write specific library, dependency, framework, runtime, or toolchain versions. Instead, route agents to the manifest, lockfile, toolchain file, Dockerfile, or CI config that owns the current version.
- When refreshing existing docs, replace any already-recorded dependency/framework version with source-of-truth file routing.
- Keep docs stable and durable; avoid recording transient observations such as current branch noise.
- Exclude generic advice, standard language conventions, obvious manifest commands, long tutorials, and file-by-file inventories from `AGENTS.md`.
- Preserve useful existing instructions, but rewrite them into concise routing guidance when they are verbose.

## Refreshing Existing Docs

- If `AGENTS.md` already exists, compare it to live repo findings before editing. Look for missing modules, stale commands, stale paths, duplicated sections, and guidance copied from other tools that no longer fits Codex.
- For major rewrites, explain the intended change shape before editing; ask for confirmation before destructive replacement or moving the source of truth.
- Keep the source-of-truth relationship clear when `AGENTS.md` is a symlink or a single `@include` stub.
- Move detailed maps, workflow tables, and uncertain follow-up notes into `docs/agent/` instead of expanding `AGENTS.md`.

## Link And Path Checks

- Every path mentioned in `AGENTS.md` should exist or be explicitly marked as planned/missing.
- Every `docs/agent/` link should be relative and valid.
- Prefer repo-relative paths in prose.
