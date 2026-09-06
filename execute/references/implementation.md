# Execute Implementation Reference

Read this reference completely before implementation, tracker amendments, commits, worktree setup, phase scheduling, recovery, or any mutating work unit.

First add `references/implementation.md` through a record write transaction, read this file completely, and complete `rules-sync` before mutation.

## Dedicated Worktree

Before beginning or resuming implementation in a git repository, work from a dedicated linked worktree for the adopted execution record. Never implement in the user's existing checkout.

- Resolve the repository root from the current working directory. If the current directory is not inside a Git repository, skip the dedicated-worktree and Git-ignore steps and continue with the non-Git workflow.
- Keep execute-created worktrees under `<repository-root>/.worktrees/`. Before creating or reusing one there, ensure the repository root ignores that directory. Prefer an existing matching ignore rule; otherwise append the root-anchored `/.worktrees/` rule to the root `.gitignore` without changing or reordering existing content. Verify the result with `git check-ignore` against a path beneath `.worktrees/`. If the rule cannot be added or the verification fails, do not create the worktree or begin implementation.
- Inspect the repository's current worktrees first. Reuse one only when it is already dedicated to the same execution record and contains no unrelated work; otherwise create a new linked worktree on the intended task branch or on a new task-focused branch from the approved base.
- Treat the recorded worktree path as resumable state, not a permanent dependency. The user may remove or clean `.worktrees/` between sessions. If the recorded worktree is missing or no longer registered, prune stale worktree metadata when safe, recreate a dedicated worktree under `.worktrees/` from the recorded branch or current execution commit, update `evidence.md` with the replacement path and branch, and continue. Do not declare a blocker merely because the previous worktree disappeared.
- Run all implementation edits, checks, staging, commits, integration, and simplify-driven fixes inside that worktree. The adopted execution record remains at its exact bound path and is the only permitted execute-mode write outside the dedicated worktree when that path lives elsewhere.
- Record the worktree path and branch in the handoff section of `evidence.md` before implementation so a later session can resume the same isolated workspace.
- If a dedicated worktree cannot be created or safely reused, do not fall back to the existing checkout. Report the concrete blocker and wait for the permission or user decision required to proceed.

## Parallel Phase Scheduling

Treat `Subagent: Eligible` as permission, not a mandate. Build a dependency-ready set from phases whose prerequisites are completed and accepted, then form the safest useful execution wave from that set.

Delegate an eligible phase only when all of these are true:

- The phase has a bounded task, stable inputs, a concrete output contract, and phase-local verification.
- Its write ownership does not overlap another active phase or pre-existing user work that cannot be preserved safely.
- It neither consumes another same-wave phase's output nor mutates a shared contract, migration, lockfile, generated artifact, external resource, persistent test data, stateful process, or similarly coupled resource without an explicit safe coordination strategy.
- A separate subagent and runtime capacity are available, and delegation is likely to improve speed or quality enough to justify coordination.

Use one subagent per eligible phase. The main agent may execute another dependency-ready, non-conflicting phase concurrently. Never hardcode a concurrency count; respect the active runtime's available capacity.

If delegation is unavailable, unsafe, or not worthwhile, execute the eligible phase sequentially and add a concise plan note when the reason matters for handoff. Lack of subagent capacity is not a blocker.

## Coordinator and Subagent Ownership

The main agent is the sole writer of the execution bundle. Subagents never edit `index.md`, `plan.md`, `verification.md`, `evidence.md`, or phase status metadata.

Assume subagents share the current workspace unless the runtime explicitly guarantees isolation. Enforce one writer per file or mutable touchpoint within a wave.

Before dispatch, mark the phase in progress and give the subagent a bounded task containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required repository instructions and read-before-write context
- The expected output or handoff contract and phase-local checks
- A requirement not to edit the execution record, broaden scope, or run commits, pushes, deployments, destructive commands, broad formatters, or other operations outside its ownership unless separately authorized
- A return contract covering summary, files or resources changed, checks and results, assumptions, risks, and blockers

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach. Review its reported output and actual changes before accepting the phase; never treat a successful agent status as sufficient verification.

## Execution Rules

Follow the plan as written, subject to higher-priority instructions and current repository rules.

- Read relevant project instructions, local conventions, callers, tests, and touched files before writing.
- For non-trivial code edits, follow the active repository coding workflow and use any required coding skill or semantic retrieval tools available in the session.
- Keep changes surgical and scoped to the plan.
- After implementation is authorized, commit the smallest complete, accepted, and independently verifiable unit of work as soon as its proportionate focused check passes. Apply this cadence across every domain; a single finished component, DTO, design token set, configuration unit, migration, documentation section, test fixture, script, workflow step, or similarly self-contained artifact may each be its own commit. Prefer a smaller valid checkpoint over combining separately complete units merely because they belong to the same task, checklist step, feature, layer, or phase. Include only the minimum dependent edits required to make the unit complete and keep the repository in an acceptable state. A saved file, partial scaffold, broken artifact, or change that is only valid after omitted required work is not a commit unit. Treat phases and checklist steps as scheduling containers, never as commit boundaries: either may produce many commits, and the same cadence applies when the current execution session covers only one phase or step. Preserve dependency order, commit before starting the next separable unit, and do not wait until the phase, step, or plan is complete. Do not commit when the user or plan forbids commits.
- Do not push, deploy, run destructive commands, or broaden scope unless the plan or user explicitly says to.
- If the plan references additional skills, tools, apps, or commands, use them when available.
- Recover from failed attempts using the recovery workflow before considering a step blocked.
- Allow unrelated dependency-ready phases to continue when one phase fails, but never start a dependent phase until its prerequisite is accepted and integrated.

## Updating The Plan

Update the original bundle transactionally. Update each phase checklist and status in its own phase file; keep the authoritative dependency table in `plan.md`, check results in `verification.md`, and amendments/commits in `evidence.md`.

In each active phase file, update checklist items directly:

- `- [ ]` or `1. [ ]` for pending
- `- [~]` or `1. [~]` for in progress
- `- [x]` or `1. [x]` for completed
- `- [!]` or `1. [!]` for blocked

Preserve the original step text where possible. Add concise inline notes only when they help a future session understand a decision, blocker, or verification result.

The coordinator may mark multiple items in progress only when their phases are explicitly safe to run in the same wave. Mark every dispatched phase in progress before spawning its subagent, and mark it completed only after reviewing scope, accepting its output, and confirming its phase-local checks. Keep dependent phases pending until their prerequisites pass the required integration gate.

Add short notes such as `parallel wave 1` or `serialized: overlaps <path or state>` when they explain an execution decision. Do not let subagents edit the plan concurrently. Use `[!]` only for a genuine blocker that requires user input or an external state change, not merely for a crashed, timed-out, or unavailable subagent.

Also update the plan status line when present:

- Before implementation: `Status: In progress`
- After implementation and verification: `Status: Implemented`
- If blocked: `Status: Blocked`
- After an explicit mode exit with unfinished non-blocked work: `Status: Paused`

When checks are run, update `verification.md` directly with checkboxes or short result notes. Put skipped checks and residual risk there or in `evidence.md` handoff notes.

### Amendment and Evidence Gate

Before substantive work or a user-facing response, persist every material user correction, added request, changed decision, discovered fact, verification result, external handoff, or out-of-scope item received while execute mode is active.

Use `evidence.md` for amendments and evidence. Remove `None at approval` when adding the first entry. Give entries stable IDs such as `A001` and record:

- Timestamp and timezone
- Kind: `Additive`, `Corrective`, `Superseding`, `Evidence`, `Out-of-scope handoff`, `Re-entry`, or `Exit`
- Source: user request, repository path and symbol, command or check, commit, artifact, ticket, URL, or other exact locator
- The change, decision, handoff, or evidence
- Affected goal, scope, phase, checklist item, verification, rollback, or external consumer
- Current status and any result that a future session must revalidate

Apply these rules:

1. Write the amendment or evidence entry before starting related implementation. If the plan write fails, report the persistence blocker and do not perform the unrecorded work.
2. For executable work, also add or revise the corresponding checklist item, dependency, ownership, integration, verification, and rollback details before implementation.
3. For a corrective or superseding request, preserve completed history, mark obsolete pending work as superseded by the amendment ID, and add corrective items for already completed behavior that must change. Update `Goal`, `Scope`, `Desired Logic and Behavior`, or acceptance criteria when they are no longer accurate.
4. For evidence-only updates or handoffs that require no execution, keep the implementation `Status` unchanged.
5. If the plan is `Implemented`, `Blocked`, or `Paused` and new executable work can proceed, change it to `In progress` before starting.
6. A request to keep work separate or outside the approved baseline still requires an `Out-of-scope handoff` record. If the agent performs that work while the mode remains active, add an amendment checklist item so its execution and verification remain auditable.
7. Do not save a raw transcript, hidden reasoning, secrets, or unrelated conversation. Persist only actionable context and evidence needed for handoff.

### User-Requested Follow-Up Work

When the user asks for implementation, fixes, tests, documentation, cleanup, or another deliverable not represented in the approved baseline while execute mode is active:

1. Pass the request through the `Amendment and Evidence Gate`, then add it to the affected phase file or the simple checklist in `plan.md` before starting it. Reference its amendment ID and date.
2. Add or adjust dependency, ownership, integration, and verification notes when the new work affects them. Do not rewrite completed history merely to make the addition look original.
3. If the plan was `Implemented`, `Blocked`, or `Paused`, change its status back to `In progress` before doing work that can proceed.
4. Mark the new item in progress, execute it under the same recovery and verification rules, then mark it completed or genuinely blocked.
5. Return the plan to `Implemented` only after the added work and its required verification are complete.

Do not silently perform user-requested follow-up work outside the plan record. If the user wants the work kept separate from the approved baseline, preserve that boundary while still recording the handoff, evidence, and any work performed. Only an explicit execute exit disables this requirement.

### Incremental Commits and Commit Records

In a git repository, once implementation and its local commits are authorized, use this cadence:

1. Capture the starting `HEAD`, branch, status, staged diff, unstaged diff, and untracked paths before implementation. Treat the starting `HEAD` as the exclusive lower bound of the current execution session's commit range.
2. Derive commit-sized work units inside each selected phase before coding. Prefer the smallest logical change that leaves the repository in a coherent, reviewable state and can pass focused checks, such as one behavior slice with its tests, one refactor prerequisite, or one isolated configuration change.
3. Never assume one phase equals one commit. A phase commonly produces multiple commits; use a single commit only when the entire phase is genuinely one indivisible logical change. Apply this rule unchanged when the session executes only one phase from a larger plan.
4. After a unit's focused checks pass and the coordinator accepts all changes in its scope, stage only files and hunks created for that unit, review the staged diff, and commit it immediately before beginning the next dependent unit. Never include unrelated pre-existing or concurrent user changes.
5. Use the active repository's commit conventions. Keep one logical change per commit and preserve dependency order. Do not create a partial commit merely because time elapsed; the unit must be coherent and verified.
6. Record every successful commit in the handoff section of `evidence.md`, including full SHA, subject, branch, and associated phase or checklist item.
7. If a commit attempt fails, keep the unit in progress while recovering and add a concise failure note only when it helps a future session. Use `[!]` only when the failure meets the genuine blocker definition.
8. After all implementation units included in the current session are committed, define the simplify scope as every current-session commit after the captured starting `HEAD` through the current `HEAD`, plus any remaining in-scope staged, unstaged, or untracked changes. Do not substitute only the final commit or current working-tree diff, even when the session executed a single phase.
9. Commit simplify-driven fixes as one or more separate coherent commits after their checks pass. Record them like other session commits. Never rewrite, squash, or amend the earlier implementation commits unless the user explicitly requests history rewriting.

The final commit SHA cannot be embedded in the commit that produced it because changing the plan would change that SHA. Record the SHA immediately after the commit, do not amend solely to make the SHA self-referential, and disclose the resulting plan-only working-tree change. Create a separate plan-metadata commit only when the user explicitly requests it; do not try to record that metadata commit's own SHA inside itself.

## Implementation Workflow

1. Resolve, adopt, and read the complete execution-record path; activate or re-enter execute mode and persist its metadata.
2. When the current directory is inside a Git repository, ensure `<repository-root>/.worktrees/` is ignored, create or safely reuse the dedicated worktree there, record its path and branch in the execution record, and perform the remaining implementation workflow there. Otherwise skip worktree setup and continue in the non-Git directory.
3. Inspect enough repository context to execute safely.
4. Build the dependency and ownership map, validate declared waves, identify the current ready set, and divide each selected phase into commit-sized logical work units.
5. Select a safe execution wave; serialize phases that are unannotated, coupled, or not worth delegating.
6. Mark the selected phase items in progress and dispatch each eligible delegated phase with the required ownership and return contract.
7. Execute any coordinator-owned phase that can run concurrently without conflicting with active subagents.
8. Collect subagent reports, inspect actual changed files or resources against the baseline and assigned ownership, and review each implementation.
9. As each commit-sized unit becomes coherent, run its focused checks, review and commit it immediately, then continue with the next unit. A selected phase may therefore produce multiple commits before its phase-local checks are complete.
10. Run or confirm phase-local checks, mark each accepted phase completed, and run the wave's integration gate before unlocking dependent phases; recover or mark a genuine blocker as appropriate.
11. Repeat the ready-set workflow until all phases are accepted or a genuine blocker requires user input or an external state change.
12. Run the final checks from `verification.md` on the integrated result.
13. Use `$simplify` to review the complete current-session commit range from the captured starting `HEAD` through the current `HEAD`, together with any remaining in-scope working-tree changes.
14. Fix confirmed or plausible `$simplify` findings that are in scope.
15. Re-run the narrowest meaningful checks after any simplify-driven fixes, then commit those fixes separately in coherent units.
16. If the current execution session's commit range or remaining working-tree diff contains substantial agent-facing changes that are not already covered in agent docs, use `$update-agent-docs` with the session-change-only scope in this skill.
17. Re-run the narrowest meaningful checks after any agent-doc updates.
18. Update the plan status, checklist, amendments and evidence, verification notes, execution decisions, `Last updated`, and residual risks.
19. If the user adds follow-up work, changes an earlier decision, provides a material handoff or evidence item, or requests a commit, pass it through the amendment gate and resume the applicable workflow before treating the task as complete.
20. Apply the final completion gate and continue working if any requirement fails.

## Recovery Before Blocking

Before declaring a blocker:

1. Inspect partial changes and the concrete failure.
2. Retry when the failure may be transient.
3. Attempt a safe in-scope alternative.
4. Replace failed delegation with coordinator-owned execution.
5. Serialize conflicting work.
6. Continue all unrelated dependency-ready phases.
7. Record skipped optional checks and residual risk when implementation can still be completed safely.

Ask the user only after these recovery paths are exhausted and the Genuine Blocker Definition is satisfied.

## Failure and Conflict Handling

A subagent failure is not automatically a plan blocker. Inspect any partial changes, preserve pre-existing user work, and choose the safest recovery: retry, reassign, finish locally, or serialize the phase. Continue unrelated ready phases when safe and keep dependent phases pending.

If ownership overlaps or an unexpected dependency appears, stop only the conflicting dispatch, preserve and inspect the current changes, update the plan note or dependency metadata, and resume in a safe sequence. Continue unrelated ready work when safe. Never use a blanket reset or discard unrelated user changes to recover from parallel work.

If a wave integration check fails, return the implicated phase items to in progress while correcting them. Mark the plan blocked only when meaningful progress truly requires user input or an external state change.
