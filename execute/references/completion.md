# Execute Completion Reference

Read this reference completely after implementation is integrated and before claiming completion, simplifying, updating agent docs, resolving a PR/MR target branch, offering security review, handling a user-requested PR/MR merge or post-merge worktree cleanup, or sending the final implementation response.

First add `references/completion.md` through a record write transaction, read this file completely, and verify the saved Required references.

## Required Simplify Pass

After the plan's implementation units are committed for Git targets, or their changed-path and before/after evidence is current for non-Git targets, invoke `$simplify` on the complete current-session changes before the final response.

- For Git targets, scope `$simplify` to the diff from the captured starting `HEAD` (exclusive) through the current `HEAD` (inclusive), plus remaining in-scope staged, unstaged, and untracked changes. Include all implementation commits created in the session, not only the most recent commit or working-tree diff.
- For non-Git targets, scope `$simplify` to every path in the recorded current-session changed-path inventory and compare it with the saved before-state evidence. Do not require commits, staging, branches, or `HEAD`; their absence is not a blocker.
- Run one coordinator-owned simplify pass only after all parallel phase results have been collected and integrated; do not run independent simplify passes inside subagents.
- Allow `$simplify` to apply focused fixes for confirmed or plausible issues in scope.
- For Git targets, commit simplify-driven fixes separately after focused checks pass; do not rewrite earlier implementation commits unless the user explicitly requests it. For non-Git targets, update the changed-path and verification evidence after those fixes.
- Do not let simplification broaden the plan or refactor unrelated code.
- If `$simplify` is unavailable, rejected, or lacks capacity for its preferred reviewer layout, perform all required review passes locally or with the available safe capacity and state the limitation. Do not block plan completion waiting for a specific subagent count.

## Agent Docs Update

After the plan is implemented, verified, and simplified, decide whether the current execution session's changes introduced substantial information future agents need.

Run `$update-agent-docs` automatically only when both are true:

- The current execution session's commit range or remaining working-tree diff includes durable agent-facing changes, such as new or changed project structure, package boundaries, entrypoints, scripts, commands, workflows, tests, generated assets, configuration, deployment steps, migrations, or repo conventions.
- The existing agent docs do not already cover the new or changed information accurately.

When invoking `$update-agent-docs` from this skill, explicitly constrain it to the current execution session's changes:

- Review only the current execution session's commit range and remaining git working-tree diff, plus the agent docs needed to check coverage or make the update.
- Do not run a repository-wide documentation refresh.
- Do not document unrelated existing code, conventions, scripts, or workflows just because they are discovered while checking the docs.
- Keep any agent-doc changes limited to guidance made necessary by the current diff.
- If there is no current-session change to inspect, skip this step and state the limitation in the final response. A non-Git target with recorded current-session path changes remains eligible for a scoped agent-doc update using that evidence.
- If `$update-agent-docs` requires additional authorization, including permission to edit outside the repository, skip the optional update and record the reason unless that external documentation update is itself an explicit plan goal. Do not leave an otherwise completed implementation in progress solely because an automatic agent-doc update could not run.

## PR/MR Target Branch

After implementation, verification, simplification, and any scoped agent-doc updates are complete, persist `Status: Implemented` and resolve the PR/MR target branch before the final implementation response. This is a post-completion preference and does not keep implementation in progress.

- For each Git repository receiving a PR/MR, inspect the complete adopted bundle for an explicit destination repository and target/base branch, including decisions and handoff evidence. Reuse that information without asking again. A worktree starting branch or implementation source branch alone is not a PR/MR target decision; do not infer the destination from it or from the remote default branch.
- Only when the bundle lacks a target branch, use `request_user_input` to ask which branch the completed changes should target in a Pull Request or Merge Request. Identify the repository in the question. Offer verified branch candidates when available and allow a custom branch or deferral; do not invent branch names. For multiple repositories, ask only about those with missing targets and respect the tool's question limit.
- Use `request_user_input` for this branch preference, not as a permission or approval request. If the tool is unavailable, ask the same concise question in conversation and record that limitation. If the tool returns without an answer, times out, or reports dismissal, leave the target unresolved, persist the unanswered question and resume checkpoint, and stop substantive work for that turn. Do not guess, apply the recommended option, resend the question, push, create a PR/MR, or proceed to another question in that turn. Keep implementation `Implemented` and execute active; resume the handoff after the user answers or explicitly changes the request. Timeout duration belongs to the runtime; do not invent a timeout parameter.
- Persist an answered destination repository and target branch in `evidence.md`, with the question, user decision, and PR/MR handoff status; update the Active Snapshot and Resume Checkpoint through the normal record transaction. Record deferral as well and honor it on subsequent completion checkpoints unless the user reopens PR/MR work. Recover this decision from the bundle after resume or compaction instead of asking again.
- Skip this question for non-Git targets, an already created associated PR/MR whose target is recorded, an explicit decision to defer or omit PR/MR creation, or read-only, blocked, paused, and exit-only checkpoints.
- A branch preference alone does not authorize pushing or creating a PR/MR. Continue under existing user or plan authorization when it covers those actions; otherwise report the recorded target as the handoff. When creation is authorized, validate the destination and branch, perform it under a scoped action, and record the resulting PR/MR URL and target in the bundle.
- When creating or updating the PR/MR description, use the bundle as source context for a concise recap of the completed changes. Lead with the concrete outcome, list the main changes delivered, and include only relevant verification results or material limitations. Describe the final result for a reviewer who has not seen the conversation; omit pending, abandoned, or unrelated work. Do not include workflow metadata such as plan ID, bundle ID, tracker ID, bundle path, bundle status, execution mode, checkpoint, or internal evidence/action IDs. Keep this metadata in the execution record instead. Follow the repository's PR/MR template when present without adding internal workflow fields.

## Security Review Offer

Do not run `$security-review` automatically.

The security-review offer is post-completion and must not leave the execution plan marked in progress.

At the end, ask the user whether they want a security review of the current execution session's changes.

If the user says yes, use `$security-review` with this scope constraint:

- Review only the current execution session's commit range plus remaining in-scope working-tree changes.
- Do not review the full repository.
- Read surrounding context, callers, or configs only as needed to validate a finding from the diff.
- Report findings first, following the `$security-review` output format.

## Post-Merge Worktree Cleanup

Before handling a user-requested PR/MR merge or dedicated-worktree cleanup, read and follow [post-merge-cleanup.md](post-merge-cleanup.md). Without such a request, preserve the dedicated worktree.

## Final Completion Gate

Before sending a response that claims implementation completion, a genuine blocker, or an explicit-exit pause:

- For each target Git repository, confirm implementation was performed in its recorded dedicated worktree and that new or replacement worktrees are inside `<recorded-anchor>/.worktrees/`, unless the user explicitly overrode that layout, as required by `Dedicated Worktree`. Safely reused pre-existing dedicated worktrees may retain their recorded locations. Confirm `evidence.md` preserves the anchor provenance and latest source-repository/worktree/branch mapping, and that ignore verification was performed only when the destination was inside a checkout. Confirm implementation did not occur in the user's existing checkout. Skip worktree and ignore steps only for actual non-Git targets; a non-Git umbrella cwd is not sufficient.
- When the user requested a PR/MR merge, confirm its remote merged state and the post-merge cleanup result or concrete preservation blocker are recorded. A successfully removed worktree satisfies the worktree gate through its recorded implementation and cleanup evidence; do not recreate it solely for completion checks. Without a merge request or separate explicit cleanup request, confirm the worktree was retained.
- Re-read every phase file and confirm no in-scope `[ ]`, `[~]`, `Pending`, or `In progress` state remains.
- Confirm every `[!]` item satisfies the Genuine Blocker Definition.
- Confirm unrelated ready phases were not skipped because another phase failed.
- Confirm final verification was run or its unavailability and residual risk were documented.
- Confirm the required simplify review was completed through the skill or locally.
- Confirm optional agent-doc limitations did not prevent plan completion.
- For an implemented Git target, confirm the PR/MR target was reused from the bundle or the missing-target question was handled under `PR/MR Target Branch`, with any answer, deferral, or unresolved state recorded.
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
- `$simplify` result and any fixes it caused
- Whether `$update-agent-docs` was run, skipped, or unavailable, and any docs it changed
- The recorded PR/MR destination and target branch, creation result when authorized, or deferred/unresolved handoff
- For a user-requested PR/MR merge, the verified merge result and whether the dedicated worktree was removed or retained, with the reason
- Whether the execution record was updated
- Which user-requested corrections, follow-up items, evidence, or out-of-scope handoffs were appended to the record
- Whether execute mode remains active or was explicitly exited, plus the exact adopted execution-record path
- Commit SHA, subject, and branch for commits created during execution, plus whether recording them left a plan-only working-tree change

Then ask whether the user wants `$security-review` on the current execution session's changes when implementation reached `Implemented`, unless they already answered that question in the current turn.

For a read-, inspection-, summary-, adoption-, or evidence-only checkpoint, report the exact adopted execution-record path, what metadata or evidence was updated, that no implementation was performed unless separately authorized, and that execute remains active until explicit exit. Do not offer a security review solely because the record was read or adopted.
