---
name: update-agent-docs
description: Create, refresh, or repair repository agent documentation centered on AGENTS.md. Use when the user asks Codex to update AGENTS.md, create agent docs, document a codebase for future agent sessions, resolve AGENTS.md symlinks or @CLAUDE.md-style includes, migrate useful guidance from Claude/Cursor/Copilot/Devin/Windsurf/Cline/Gemini/Codex configs, generate docs/agent routing maps, run multi-agent project discovery, or prepare a commit/push prompt for agent-doc changes.
---

# Update Agent Docs

## Purpose

Refresh the repository's agent-facing documentation so future sessions can find the right modules, packages, files, workflows, and tests without rediscovering the project from scratch.

Keep `AGENTS.md` as the token-efficient routing index. Put longer detail under `docs/agent/` and make `AGENTS.md` point agents to those files on demand.

## Required Workflow

1. **Resolve the writable docs target.**
   - Run the bundled resolver next to this `SKILL.md`: `<skill-dir>/scripts/resolve_agent_docs_target.py <repo-root>`.
   - Set `agent_docs_target = result.target_path`; every later instruction to edit `AGENTS.md` means edit this resolved target when it differs from `result.agents_path`.
   - If `AGENTS.md` is a symlink, edit the resolved target.
   - If `AGENTS.md` or its symlink target is a single include directive such as `@CLAUDE.md`, edit the included file.
   - If `result.requires_confirmation` is true, get explicit user confirmation before editing because the resolved target is outside the repository.
   - If the script reports a mixed or ambiguous include, inspect it and ask the user only if the source of truth cannot be determined safely.
   - If no `AGENTS.md` exists, create `<repo-root>/AGENTS.md`.

2. **Read existing instructions before changing them.**
   - Read the resolved target and any existing `docs/agent/` files.
   - Preserve durable user preferences, repo-specific rules, and tool-routing rules.
   - Treat any recorded library, dependency, framework, runtime, or toolchain version as stale-prone guidance to replace with source-of-truth file routing.
   - Treat existing docs as input, not as complete coverage.
   - If the target already has substantial content, use a refresh stance: identify missing, stale, bloated, and duplicated guidance before rewriting.
   - Do not replace user-authored guidance wholesale unless it is demonstrably stale or the user asked to start fresh.

3. **Use repository-aware retrieval.**
   - Activate the repo with Serena when available and read Serena initial instructions if not already done.
   - Use Serena symbolic tools for source-code structure.
   - Use `rg`/`rg --files` through the repo's command wrapper when direct command output will stay small.

4. **Launch multiple agents in parallel.**
   - If subagent tooling is available and permitted by the current session policy, spawn independent agents before writing final docs. In Codex, use `multi_agent_v1.spawn_agent` when it is callable; otherwise search for the available multi-agent or subagent tool. Use [subagent-prompts.md](references/subagent-prompts.md).
   - Assign distinct slices: architecture/module map, workflows/tests, frontend/UI, backend/API/data, infra/config/CI, and existing-doc gap review.
   - If subagent tooling is unavailable or the current tool policy forbids delegation without an explicit user request, report that the parallel-agent step cannot be performed and continue with careful single-agent discovery.

5. **Explore beyond current docs.**
   - Use [discovery-checklist.md](references/discovery-checklist.md) to cover manifests, source roots, entrypoints, scripts, tests, config, CI, deploy, generated assets, migrations, docs, and package boundaries.
   - Compare findings against the existing `agent_docs_target`; add missing categories even if the previous docs did not mention them.
   - Read other AI-agent configuration files when present and migrate only durable, repo-relevant guidance.
   - Ask the user only for practices the repo cannot reveal: non-obvious team conventions, required local services, branch/PR etiquette, test quirks, or changed workflows.

6. **Write token-efficient docs.**
   - Use [doc-structure.md](references/doc-structure.md).
   - Before keeping a line in `agent_docs_target`, test it: would removing this cause a future agent to make a likely mistake? If not, cut or move it to `docs/agent/`.
   - Keep `agent_docs_target` concise but specific: mention exact folders/files to read for each common task.
   - Put detailed maps, workflow notes, and inventories in `docs/agent/`.
   - Prefer "When working on X, read Y first" guidance over prose summaries.
   - Do not write specific library, dependency, framework, runtime, or toolchain versions in `AGENTS.md` or `docs/agent/`, including versions copied from existing docs.
   - Instead, tell agents to check the project-managed source of truth for current versions, such as manifests, lockfiles, toolchain files, Dockerfiles, or CI config (`package.json`, lockfiles, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`, `.nvmrc`, `.python-version`, `.tool-versions`, `mise.toml`, and similar files when present).
   - Keep personal preferences, private paths, secrets, and user-specific local setup out of shared docs unless the repository already intentionally documents them.

7. **Verify.**
   - Re-read changed docs for broken links, stale paths, duplicated sections, and unclear routing.
   - Run the narrowest useful check, usually link/path existence checks plus `git diff --check`.
   - If scripts or generated docs were changed, run the relevant validation or smoke check.

8. **Ask about commit and push.**
   - After verification, ask whether the user wants to commit and push to `origin`.
   - If the user agrees, follow [commit-push-policy.md](references/commit-push-policy.md).
   - Do not add `Co-Worker`, `Co-Authored-By`, or similar attribution trailers to the commit message.

## Output Expectations

- `AGENTS.md` or its resolved source-of-truth target is updated or created.
- `docs/agent/` contains detailed supporting docs when detail would make `AGENTS.md` too large.
- The final response summarizes changed files, verification performed, and asks about commit/push when changes are complete.

## Resource Map

- `scripts/resolve_agent_docs_target.py`: determine whether to edit `AGENTS.md`, its symlink target, or its single include target.
- [references/discovery-checklist.md](references/discovery-checklist.md): complete project discovery checklist.
- [references/doc-structure.md](references/doc-structure.md): recommended `AGENTS.md` and `docs/agent/` structure.
- [references/subagent-prompts.md](references/subagent-prompts.md): parallel subagent assignments and synthesis rules.
- [references/commit-push-policy.md](references/commit-push-policy.md): exact commit/push behavior.
