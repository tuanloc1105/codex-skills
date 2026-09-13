---
name: update-agent-docs
description: Create, refresh, or repair repository agent documentation centered on AGENTS.md and GEMINI.md. Use when the user asks to update AGENTS.md/GEMINI.md, create agent docs, document a codebase for future agent sessions, resolve symlinks or includes, migrate useful guidance from other AI configs, generate docs/agent routing maps, run multi-agent project discovery, or prepare a commit/push prompt for agent-doc changes.
---

# Update Agent Docs (Antigravity Edition)

## Purpose

Refresh the repository's agent-facing documentation so future sessions can find the right modules, packages, files, workflows, and tests without rediscovering the project from scratch.

Keep `AGENTS.md` (or `GEMINI.md` / `.agents/rules/`) as the token-efficient routing index. Put longer detail under `docs/agent/` and make `AGENTS.md` point agents to those files on demand.

## Required Workflow

1. **Resolve the writable docs target.**
   - Run the bundled resolver: `<skill-dir>/scripts/resolve_agent_docs_target.py <repo-root>`.
   - Set `agent_docs_target = result.target_path`; every later instruction to edit `AGENTS.md` means edit this resolved target when it differs from `result.agents_path`.
   - If `AGENTS.md` is a symlink, edit the resolved target.
   - If `AGENTS.md` or its symlink target is a single include directive such as `@CLAUDE.md`, edit the included file.
   - If `result.requires_confirmation` is true, get explicit user confirmation using `ask_question` before editing because the resolved target is outside the repository.
   - If no `AGENTS.md` or `GEMINI.md` exists, create `<repo-root>/AGENTS.md`.

2. **Read existing instructions before changing them.**
   - Read the resolved target and any existing `docs/agent/` files using `view_file`.
   - Preserve durable user preferences, repo-specific rules, and tool-routing rules.
   - Treat any recorded library, dependency, framework, runtime, or toolchain version as stale-prone guidance to replace with source-of-truth file routing.
   - If the target already has substantial content, use a refresh stance: identify missing, stale, bloated, and duplicated guidance before rewriting.
   - Do not replace user-authored guidance wholesale unless it is demonstrably stale or the user asked to start fresh.

3. **Use repository-aware retrieval.**
   - Use Antigravity search tools: `find_by_name`, `grep_search`, `list_dir`.

4. **Launch multiple agents in parallel.**
   - When project discovery requires broad inspection, launch independent subagents using Antigravity's `invoke_subagent`:
     - Dispatch subagents with `TypeName: 'research'` and distinct roles: `Role: 'Architecture Mapper'`, `Role: 'Workflow & Test Mapper'`, `Role: 'Frontend & UI Mapper'`, `Role: 'Backend & Data Mapper'`, `Role: 'Infra & CI Mapper'`, `Role: 'Doc Gap Reviewer'`.
     - Prompts should follow [subagent-prompts.md](references/subagent-prompts.md).
   - If subagent delegation is unavailable, perform sequential discovery locally.

5. **Explore beyond current docs.**
   - Use [discovery-checklist.md](references/discovery-checklist.md) to cover manifests, source roots, entrypoints, scripts, tests, config, CI, deploy, generated assets, migrations, docs, and package boundaries.
   - Compare findings against the existing `agent_docs_target`; add missing categories even if previous docs did not mention them.
   - Ask the user (via `ask_question`) only for practices the repo cannot reveal: non-obvious team conventions, required local services, branch/PR etiquette, test quirks, or changed workflows.

6. **Write token-efficient docs.**
   - Use [doc-structure.md](references/doc-structure.md).
   - Before keeping a line in `agent_docs_target`, test it: would removing this cause a future agent to make a likely mistake? If not, cut or move it to `docs/agent/`.
   - Keep `agent_docs_target` concise but specific: mention exact folders/files to read for each common task.
   - Put detailed maps, workflow notes, and inventories in `docs/agent/`.
   - Prefer "When working on X, read Y first" guidance over prose summaries.
   - Do not write specific library or tool versions in docs; point agents to manifest/lockfile sources of truth.
   - Apply edits with `replace_file_content` or `write_to_file`.

7. **Verify.**
   - Re-read changed docs for broken links, stale paths, duplicated sections, and unclear routing.
   - Run `git diff --check` via `run_command`.

8. **Ask about commit and push.**
   - After verification, ask whether the user wants to commit and push to `origin` using `ask_question` (or chat fallback).
   - If the user agrees, follow [commit-push-policy.md](references/commit-push-policy.md).
   - Do not add `Co-Worker`, `Co-Authored-By`, or similar attribution trailers to the commit message.

## Output Expectations

- `AGENTS.md` (or `GEMINI.md`) is updated or created.
- `docs/agent/` contains detailed supporting docs when detail would make `AGENTS.md` too large.
- The final response summarizes changed files, verification performed, and asks about commit/push when changes are complete.
