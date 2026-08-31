# Execute Completion Reference

Read this reference completely after implementation is integrated and before claiming completion, simplifying, updating agent docs, offering security review, or sending the final implementation response.

First add `references/completion.md` through a record write transaction, read this file completely, and complete `rules-sync`.

## Required Simplify Pass

After the plan's implementation units are committed, invoke `the required simplification review` on the complete current-session changes before the final response.

- Scope `the required simplification review` to the diff from the captured starting `HEAD` (exclusive) through the current `HEAD` (inclusive), plus remaining in-scope staged, unstaged, and untracked changes. Include all implementation commits created in the session, not only the most recent commit or working-tree diff.
- Run one coordinator-owned simplify pass only after all parallel phase results have been collected and integrated; do not run independent simplify passes inside subagents.
- Allow `the required simplification review` to apply focused fixes for confirmed or plausible issues in scope.
- Commit simplify-driven fixes separately after focused checks pass; do not rewrite earlier implementation commits unless the user explicitly requests it.
- Do not let simplification broaden the plan or refactor unrelated code.
- If `the required simplification review` is unavailable, rejected, or lacks capacity for its preferred reviewer layout, perform all required review passes locally or with the available safe capacity and state the limitation. Do not block plan completion waiting for a specific subagent count.

## Agent Docs Update

After the plan is implemented, verified, and simplified, decide whether the current execution session's changes introduced substantial information future agents need.

Run `the repository agent-documentation workflow` automatically only when both are true:

- The current execution session's commit range or remaining working-tree diff includes durable agent-facing changes, such as new or changed project structure, package boundaries, entrypoints, scripts, commands, workflows, tests, generated assets, configuration, deployment steps, migrations, or repo conventions.
- The existing agent docs do not already cover the new or changed information accurately.

When invoking `the repository agent-documentation workflow` from this skill, explicitly constrain it to the current execution session's changes:

- Review only the current execution session's commit range and remaining git working-tree diff, plus the agent docs needed to check coverage or make the update.
- Do not run a repository-wide documentation refresh.
- Do not document unrelated existing code, conventions, scripts, or workflows just because they are discovered while checking the docs.
- Keep any agent-doc changes limited to guidance made necessary by the current diff.
- If there is no git repository or no current-session change to inspect, skip this step and state the limitation in the final response.
- If `the repository agent-documentation workflow` requires additional authorization, including permission to edit outside the repository, skip the optional update and record the reason unless that external documentation update is itself an explicit plan goal. Do not leave an otherwise completed implementation in progress solely because an automatic agent-doc update could not run.

## Security Review Offer

Do not run `a focused security review` automatically.

The security-review offer is post-completion and must not leave the execution plan marked in progress.

At the end, ask the user whether they want a security review of the current execution session's changes.

If the user says yes, use `a focused security review` with this scope constraint:

- Review only the current execution session's commit range plus remaining in-scope working-tree changes.
- Do not review the full repository.
- Read surrounding context, callers, or configs only as needed to validate a finding from the diff.
- Report findings first, following the `a focused security review` output format.

## Final Completion Gate

Before sending a response that claims implementation completion, a genuine blocker, or an explicit-exit pause:

- For Git repositories, confirm implementation was performed in the current dedicated worktree under `<repository-root>/.worktrees/`, that `/.worktrees/` is verified as ignored, and that `evidence.md` records the latest path and branch after any worktree replacement. Confirm implementation did not occur in the user's existing checkout. For non-Git directories, confirm the worktree and ignore steps were skipped.
- Re-read every phase file and confirm no in-scope `[ ]`, `[~]`, `Pending`, or `In progress` state remains.
- Confirm every `[!]` item satisfies the Genuine Blocker Definition.
- Confirm unrelated ready phases were not skipped because another phase failed.
- Confirm final verification was run or its unavailability and residual risk were documented.
- Confirm the required simplify review was completed through the skill or locally.
- Confirm optional agent-doc limitations did not prevent plan completion.
- Confirm every material correction, follow-up, decision, evidence item, and out-of-scope handoff was recorded in `evidence.md`.
- Confirm every executable amendment was reflected in the checklist and completed, paused by explicit exit, or genuinely blocked.
- If commits were created, confirm their SHA, subject, and branch were recorded in `evidence.md`, and disclose any post-commit bundle-only working-tree change.
- Confirm `Execute mode: Active` remains set unless the user explicitly exited; implementation completion alone must not change it.
- Persist final phase checklists, index status, evidence, `verification.md` results, execution decisions, and residual risks through one valid record write transaction.

If any requirement above is false, continue working instead of responding finally.

## Final Response

After implementation reaches `Implemented`, `Blocked`, or an explicit-exit `Paused` state, summarize:

- What was implemented
- Which plan steps are completed or blocked
- Which phases ran in parallel, which eligible phases were serialized and why, and any subagent recovery that was needed
- Checks run and results
- Integration-gate results for parallel waves
- `the required simplification review` result and any fixes it caused
- Whether `the repository agent-documentation workflow` was run, skipped, or unavailable, and any docs it changed
- Whether the execution record was updated
- Which user-requested corrections, follow-up items, evidence, or out-of-scope handoffs were appended to the record
- Whether execute mode remains active or was explicitly exited, plus the exact adopted execution-record path
- Commit SHA, subject, and branch for commits created during execution, plus whether recording them left a plan-only working-tree change

Then ask whether the user wants `a focused security review` on the current execution session's changes when implementation reached `Implemented`, unless they already answered that question in the current turn.

For a read-, inspection-, summary-, adoption-, or evidence-only checkpoint, report the exact adopted execution-record path, what metadata or evidence was updated, that no implementation was performed unless separately authorized, and that execute remains active until explicit exit. Do not offer a security review solely because the record was read or adopted.
