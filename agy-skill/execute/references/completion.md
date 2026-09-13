# Execute Completion Reference (Antigravity Edition)

Read this reference completely after implementation is integrated and before claiming completion, simplifying, updating agent docs, offering security review, handling a user-requested PR/MR merge or post-merge worktree cleanup, or sending the final implementation response.

First add `references/completion.md` through a record write transaction, read this file completely, and verify the saved Required references.

## Required Simplify Pass

After the plan's implementation units are committed for Git targets, or their changed-path and before/after evidence is current for non-Git targets, invoke the `simplify` skill on the complete current-session changes before the final response.

- For Git targets, scope `simplify` to the diff from the captured starting `HEAD` (exclusive) through current `HEAD` (inclusive), plus remaining in-scope working-tree changes.
- For non-Git targets, scope `simplify` to the recorded current-session changed paths against before-state evidence.
- Run one coordinator-owned simplify pass only after all parallel phase results have been collected and integrated; do not run independent simplify passes inside subagents.
- Allow `simplify` to apply focused fixes for confirmed or plausible issues in scope.
- For Git targets, commit simplify-driven fixes separately after focused checks pass.
- Do not let simplification broaden the plan or refactor unrelated code.
- If `simplify` is unavailable, perform all required review passes locally and state the limitation.

## Agent Docs Update

After the plan is implemented, verified, and simplified, decide whether the current execution session's changes introduced substantial information future agents need.

Run `update-agent-docs` automatically only when both are true:

- The current execution session's changes include durable agent-facing changes, such as new or changed project structure, package boundaries, entrypoints, scripts, commands, workflows, tests, generated assets, configuration, deployment steps, migrations, or repo conventions (`AGENTS.md`, `GEMINI.md`, rules).
- The existing agent docs do not already cover the new or changed information accurately.

When invoking `update-agent-docs` from this skill, explicitly constrain it to current execution session changes:

- Review only current-session commits and remaining working-tree diff.
- Do not run a repository-wide documentation refresh.
- Keep agent-doc changes limited to guidance made necessary by the current diff.

## Security Review Offer

Do not run `security-review` automatically.

The security-review offer is post-completion and must not leave the execution plan marked in progress.

At the end of the implementation response, ask the user whether they want a security review of the current execution session's changes using `ask_question` (or chat fallback).

If the user says yes:
- Review only the current execution session's commit range plus remaining in-scope working-tree changes.
- Do not review the full repository.
- Read surrounding context only as needed to validate findings from the diff.

## Final Completion Gate

Before sending a response that claims implementation completion:

- Confirm implementation occurred in dedicated worktrees / isolated Antigravity workspaces.
- Confirm every phase file has no remaining `[ ]`, `[~]`, `Pending`, or `In progress` items.
- Confirm every `[!]` item satisfies the Genuine Blocker Definition.
- Confirm final verification checks were run.
- Confirm the required simplify pass was completed.
- Confirm `Execute mode: Active` remains set unless the user explicitly exited.
- Persist final phase checklists, index status, evidence, and verification notes through a record write transaction.

## Final Response

After implementation reaches `Implemented`, `Blocked`, or an explicit-exit `Paused` state, summarize:

- What was implemented
- Which plan steps are completed or blocked
- Which phases ran in parallel via subagents, which were serialized, and any recovery performed
- Checks run and results
- `simplify` result and any fixes applied
- Whether `update-agent-docs` was run, skipped, or unavailable
- Whether execute mode remains active (it remains active unless explicitly exited) and the exact adopted record path
- Commit SHA, subject, and branch for commits created during execution

Then ask whether the user wants `security-review` on the current execution session's changes when implementation reached `Implemented`, using `ask_question`.
