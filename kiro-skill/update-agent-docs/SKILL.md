---
name: kiro-update-agent-docs
description: Create, refresh, or repair repository steering documentation centered on `.kiro/steering/*.md`. Use when the user asks Kiro to update steering docs, create agent-facing project docs, document a codebase for future Kiro sessions, migrate useful guidance from AGENTS.md/CLAUDE.md/Cursor/Copilot/Devin/Windsurf/Cline/Gemini configs, generate a docs/agent routing map, run multi-agent project discovery, or prepare a commit/push prompt for steering-doc changes. Kiro port of the Codex `update-agent-docs` skill.
---

# Update Agent Docs (Kiro / Kiro Crew)

Codex centers its agent-facing docs on a single `AGENTS.md` at the repo root. Kiro has
no equivalent convention: per-project guidance lives in `.kiro/steering/**/*.md` (auto-loaded
for sessions scoped to that project via `[PROJECT]`), and per-agent behavior lives in
`~/.kiro/agents/*.json` / a global prompt resource. This port keeps the same discovery,
writing-style, and verification workflow as the Codex skill, but retargets the *edit*
step at `.kiro/steering/`, while still reading (never blindly copying) any `AGENTS.md`,
`CLAUDE.md`, or other AI-tool config already in the repo as migration input.

## Purpose

Refresh the project's steering documentation so future Kiro sessions can find the right modules, packages, files, workflows, and tests without rediscovering the project from scratch.

Keep a top-level steering file as the token-efficient routing index. Put longer detail under `docs/agent/` and make the routing index point sessions to those files on demand.

## Required Workflow

1. **Resolve the writable steering target.**
   - Run the bundled resolver next to this `SKILL.md`: `python3 <skill-dir>/scripts/resolve_agent_docs_target.py <repo-root>`.
   - The resolver's primary target is `.kiro/steering/00-project-guide.md` (created if missing) inside `<repo-root>/.kiro/steering/`. Kiro auto-loads every `.md` file under `.kiro/steering/` for a session whose `[PROJECT]` is inside that repo, so which exact filename holds the routing index matters less than that it lives under `.kiro/steering/` and is not shadowed by a more specific file.
   - If the repo already has a routing-shaped steering file (e.g. any file under `.kiro/steering/` whose content matches the `## Start Here` / `## Task Routing` shape below), treat that file as the resolved target instead of creating a second one.
   - If `AGENTS.md` or `CLAUDE.md` exists at the repo root, treat it as durable migration input (see step 2) but do not edit it as the primary target — Kiro sessions do not read it automatically. Mention its existence to the user once; do not silently leave two competing routing docs.
   - If no `.kiro/steering/` directory exists, create it and the initial routing file.
   - `result.requires_confirmation` from the resolver means the resolved target is outside the repository (rare for the steering path, but preserved for parity with the Codex resolver and for any custom `--target` override); get explicit user confirmation before editing in that case.

2. **Read existing instructions before changing them.**
   - Read every file already under `.kiro/steering/`, plus any root `AGENTS.md`/`CLAUDE.md` and other AI-tool configs (see `discovery-checklist.md`).
   - Preserve durable user preferences, repo-specific rules, and tool-routing rules.
   - Treat any recorded library, dependency, framework, runtime, or toolchain version as stale-prone guidance to replace with source-of-truth file routing.
   - Treat existing docs as input, not as complete coverage.
   - If the target already has substantial content, use a refresh stance: identify missing, stale, bloated, and duplicated guidance before rewriting.
   - Do not replace user-authored guidance wholesale unless it is demonstrably stale or the user asked to start fresh.

3. **Use repository-aware retrieval.**
   - Use the `code` tool (`search_symbols`, `get_document_symbols`, `generate_codebase_overview`, `search_codebase_map`) for source-code structure instead of ad hoc scanning.
   - Use `grep`/`glob` scoped to the project directory (never the whole home directory) when direct output will stay small.

4. **Launch multiple agents in parallel when the discovery fans out.**
   - When the repository is large enough that architecture/workflow/frontend/backend/infra discovery is genuinely independent work, delegate with `spawn_run` — pass every discovery task in one `tasks` array batch (see [subagent-prompts.md](references/subagent-prompts.md) for the exact assignments), then **end the turn** and wait for `[Subagent completion event]` messages before synthesizing.
   - Set `include_lessons=false` and `include_memory=false` for these purely-read discovery agents (they only search and report, per this agent's own subagent-scoping guidance); keep `include_project=true` since they must search inside the project tree.
   - For a small or already-well-documented repo, do this discovery directly in-session instead — a lone discovery subagent adds a round-trip with no parallelism gain.
   - If subagent tooling is unavailable or session policy forbids delegation, continue with careful single-session discovery and say so.

5. **Explore beyond current docs.**
   - Use [discovery-checklist.md](references/discovery-checklist.md) to cover manifests, source roots, entrypoints, scripts, tests, config, CI, deploy, generated assets, migrations, docs, and package boundaries.
   - Compare findings against the existing steering content; add missing categories even if the previous docs did not mention them.
   - Read other AI-agent configuration files when present (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`, `.github/copilot-instructions.md`, etc.) and migrate only durable, repo-relevant guidance that is not already covered by an existing `.kiro/steering/` file or by this agent's global learned corrections (`learn_list`).
   - Ask the user only for practices the repo cannot reveal: non-obvious team conventions, required local services, branch/PR etiquette, test quirks, or changed workflows.

6. **Write token-efficient docs.**
   - Use [doc-structure.md](references/doc-structure.md).
   - Before keeping a line in the top-level steering file, test it: would removing this cause a future Kiro session to make a likely mistake? If not, cut it or move it to `docs/agent/`.
   - Keep the steering routing file concise but specific: mention exact folders/files to read for each common task.
   - Put detailed maps, workflow notes, and inventories in `docs/agent/`.
   - Prefer "When working on X, read Y first" guidance over prose summaries.
   - Do not write specific library, dependency, framework, runtime, or toolchain versions in `.kiro/steering/` or `docs/agent/`, including versions copied from existing docs.
   - Instead, tell sessions to check the project-managed source of truth for current versions, such as manifests, lockfiles, toolchain files, Dockerfiles, or CI config (`package.json`, lockfiles, `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`, `.nvmrc`, `.python-version`, `.tool-versions`, `mise.toml`, and similar files when present).
   - Keep personal preferences, private paths, secrets, and user-specific local setup out of shared docs unless the repository already intentionally documents them. A durable cross-repo preference belongs in `learn_add`, not in a repo's steering file.

7. **Verify.**
   - Re-read changed docs for broken links, stale paths, duplicated sections, and unclear routing.
   - Run the narrowest useful check, usually link/path existence checks plus a Markdown lint if the project already has one configured.
   - If scripts or generated docs were changed, run the relevant validation or smoke check.

8. **Ask about commit and push.**
   - After verification, ask whether the user wants to commit and push to `origin` — via `ask_question` on a dashboard session (ending the turn) or a trailing `[OPTIONS: Commit and push | Just leave the changes]` otherwise.
   - If the user agrees, follow [commit-push-policy.md](references/commit-push-policy.md).
   - Do not add `Co-Worker`, `Co-Authored-By`, or similar attribution trailers to the commit message, per this agent's own git conventions.

## Output Expectations

- The resolved `.kiro/steering/` routing file is updated or created.
- `docs/agent/` contains detailed supporting docs when detail would make the routing file too large.
- The final response summarizes changed files, verification performed, and asks about commit/push when changes are complete.

## Resource Map

- `scripts/resolve_agent_docs_target.py`: determine whether to edit the existing `.kiro/steering/` routing file, create a new one, or (with explicit confirmation) an out-of-repo target.
- [references/discovery-checklist.md](references/discovery-checklist.md): complete project discovery checklist.
- [references/doc-structure.md](references/doc-structure.md): recommended steering-file and `docs/agent/` structure.
- [references/subagent-prompts.md](references/subagent-prompts.md): parallel `spawn_run` assignments and synthesis rules.
- [references/commit-push-policy.md](references/commit-push-policy.md): exact commit/push behavior.
