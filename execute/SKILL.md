---
name: execute
description: Persistent execution and evidence-tracking mode for an approved Markdown execution record produced by $plan or by an execution-ready $discuss tracker. Use whenever the user supplies or references such a file and asks Codex to read, adopt, resume, continue, execute, amend, or record follow-up work against it, including in a fresh session and when its implementation is already complete. Keep the exact file active as the source of execution truth across later turns, record material corrections, added work, out-of-scope handoffs, evidence, and commit records in place, and remain in execute mode until the user explicitly exits it. During implementation, commit each verified unit of work, schedule dependency-ready phases, run integration and final verification, use $simplify across the session commit range, update agent docs when required, and optionally offer a current-change $security-review.
---

# Execute

## Workflow Modes Hook

When the `workflow-modes` plugin is installed and its hooks are trusted, resolve `workflow_modes_control.py` from the installed plugin bundle, normally `<user-home>/plugins/workflow-modes/scripts/`, and run lifecycle calls with the exact absolute path and `--marker workflow-modes-v1`.

- On fresh-session adoption, after validating and persisting `Execute mode: Active`, run `activate execute --record <execution-record>` before implementation.
- On handoff from `$plan` or `$discuss`, require the source skill's successful `transition execute --record <execution-record>` result, then run `activate execute --record <execution-record>` to confirm or rebind the same active record.
- When the user explicitly exits execute and the exit metadata is durable, run `deactivate`. Implementation completion alone must never call `deactivate`.

Confirm every control call returns model-visible `WORKFLOW_*` context. If the plugin or control script is unavailable, read-only adoption and evidence updates may continue, but do not begin or resume implementation; report that lifecycle enforcement must be installed and trusted. Never bypass a denied hook decision.

Use this skill to adopt either an approved `$plan` handoff or an execution-ready `$discuss` tracker as a persistent execution and evidence record. In the rules below, “plan” means the exact adopted execution record regardless of which skill produced it.

## Persistent Mode Contract

Enter execute mode immediately when the user explicitly invokes `$execute` or asks to read, adopt, resume, continue, execute, or amend an accepted execution record. Accepted records are `$plan` handoffs and `$discuss` trackers that passed `Direct Execute Handoff`. Activate the mode in a fresh session and regardless of whether the implementation status is approved, in progress, blocked, paused, implemented, or previously exited. Supplying the record again or asking to read it is an explicit re-entry.

- Bind the mode to the exact adopted execution-record path. Keep that file as the sole execution source of truth unless the user explicitly switches to another record.
- Keep execute mode active across later turns, completion reports, and `Status: Implemented`. Completing the baseline plan does not end the mode.
- Exit only when the user clearly says to exit or turn off execute, such as `exit execute`, `turn off execute`, `thoat execute`, or equivalent explicit wording.
- Treat requests to handle work separately, keep it outside the approved scope, or avoid changing the baseline as scope instructions, not as a mode exit. Record the boundary and material handoff or evidence in the adopted plan while the mode remains active.
- Do not treat reading or adopting a plan as authorization to implement code, mutate external systems, commit, push, or deploy. Wait for a clear current-session request authorizing the relevant action. In a git repository, a clear request to implement the adopted record authorizes local incremental commits for that implementation unless the user or plan explicitly forbids commits; it does not authorize pushing or deploying.

On every adoption or re-entry, read the complete plan before substantive work and ensure it contains or backfill these metadata lines near the top:

```markdown
Execute mode: Active
Last updated: <timestamp and timezone>
Resume instruction: Invoke $execute, read this file completely, keep this exact file as the execution source of truth, and continue updating it until the user explicitly exits execute.
```

Preserve the implementation `Status` independently from the execute mode. An implemented plan may remain `Status: Implemented` while `Execute mode: Active`; reopen the implementation status only when new executable work starts.

## Completion Contract

Execute the entire approved plan, not only the current phase or execution wave.

Treat every material correction, added deliverable, decision, evidence item, or out-of-scope handoff the user provides while execute mode is active as an amendment or evidence record. Update the adopted plan even when its approved baseline is already complete. Only an explicit execute exit stops this recording contract.

Do not send the final response while any in-scope plan item remains pending `[ ]` or in progress `[~]`, unless a genuine blocker requires user input or an external state change. Progress reports, completed phases, failed checks, subagent results, context pressure, tool failures, and unavailable delegation are intermediate states, not completion conditions. Continue recovering and executing within the current task.

Before claiming that implementation is complete, blocked, or intentionally paused, ensure exactly one of these conditions is true:

1. Every in-scope plan item is completed `[x]`, final verification has been attempted, and the plan status is `Implemented`.
2. All safe independent work is complete, at least one item has a documented genuine blocker `[!]`, and the plan status is `Blocked`.
3. The user explicitly exited execute with unfinished work, the incomplete checklist remains accurate, the plan status is `Paused`, and the execute mode is `Exited`.

A final response for a completed implementation is a checkpoint, not a mode exit. State that execute remains active and name the adopted execution-record path unless the user explicitly exited it.

For a read-, inspection-, summary-, or adoption-only turn without implementation authorization, preserve the existing implementation status and checklist, persist the mode metadata plus any material evidence, and send a checkpoint response stating that no implementation was performed. This response does not need to satisfy an implementation completion condition and does not exit execute.

## Mode Exit

When the user explicitly exits execute:

1. Stop accepting new amendments under this mode after the exit instruction.
2. Persist all material current-turn deltas, evidence, checklist state, and verification results first.
3. Set `Execute mode: Exited` and update `Last updated`.
4. Add an `Exit` entry under `## Amendments and Evidence` with the instruction and timestamp.
5. Keep `Status: Implemented` or `Status: Blocked` when accurate; use `Status: Paused` when executable items remain unfinished without a genuine blocker.
6. Report the exact execution-record path and remaining work. Do not treat exit as authorization to discard or complete pending work.

## Genuine Blocker Definition

A genuine blocker exists only when meaningful progress requires one of:

- A user decision whose alternatives materially change the approved outcome
- A credential, permission, approval, or secret that cannot be obtained within the current task
- An unavailable external system or state required for the next dependent work
- An action prohibited by higher-priority instructions
- An irreconcilable conflict with pre-existing user changes where proceeding could overwrite or corrupt them

The following are not blockers by themselves:

- A failed test, build, lint, verification, or integration check
- A crashed, timed-out, unavailable, or rejected subagent
- Lack of parallel-agent capacity
- A failed implementation attempt
- Missing optional tooling or skills
- Repository drift that can be reconciled without materially changing the approved goal
- Ambiguity that repository evidence or a safe, non-material assumption can resolve
- An optional documentation, simplification, or review step that can be performed locally or reported as unavailable

## Required Input

Require a path to the Markdown execution record unless an exact adopted plan or discussion-tracker path is already active in the current task. A successful direct handoff from `$discuss` supplies its active tracker path automatically.

- If the user supplied a plan or tracker path, resolve it before doing implementation work.
- If the current task already has one adopted execution-record path, reuse it for later turns without asking again.
- If the user did not supply a path and no exact active path exists, ask where the execution record is and stop until they answer.
- If the path does not exist or is not readable, report that clearly and ask for the correct path.

## Plan and Tracker Intake

Read the full execution record before any substantive response or implementation work, adopt the exact path, and apply the `Persistent Mode Contract` metadata update. Never copy a direct discussion handoff into a separate plan file; preserve the tracker history and keep updating that same path.

Verify these basics:

- The file is either a Markdown plan, ideally with `# How to do it: ...`, or a `# Discussion Tracker` with `Execution readiness: Ready` and `Mode status: Exited`.
- The record has a concrete `## Goal`, `## Step-by-Step Plan`, and `## Verification`.
- No unresolved entry under `## Open Questions` is marked as blocking execution.
- The record status is approved or the user explicitly asked to execute it.
- For a phased plan, read `## Execution Structure` and capture each phase's ID, dependencies, wave, subagent eligibility, owned scope, produced output, and verification or integration requirements.

Reject an active or not-ready discussion tracker as an execution input. Do not silently finish its discussion, choose unresolved options, or manufacture a plan inside execute mode. In the same task, keep `$discuss` active and complete its `Direct Execute Handoff`; in a fresh task, tell the user to resume `$discuss` on that exact tracker before trying `$execute` again.

For an accepted discussion tracker, preserve `Mode status: Exited`, set `Execute mode: Active`, apply the standard execute resume instruction, and use the tracker as the sole execution source of truth. Missing scheduling metadata remains subject to the sequential backward-compatibility rule below.

Treat an explicit user request to execute the supplied record as execution approval even when its status is missing or still says `Draft`, `Ready`, or `Awaiting execution`. A request only to read, inspect, summarize, or adopt the record activates execute mode and its bookkeeping but does not authorize implementation.

Ask for confirmation only when the record explicitly says not to implement, an unresolved choice materially changes the desired outcome, repository drift invalidates the approved goal or requires materially different scope, or two authoritative requirements cannot both be satisfied. Do not invent a materially different plan.

Treat `Depends on` as authoritative and any declared wave as a scheduling hint that must agree with it. Revalidate phase independence against the current repository and runtime before dispatch. An eligibility note never overrides overlapping files, shared mutable state, unstable contracts, or newly discovered dependencies.

For backward compatibility, execute plans without dependency, wave, ownership, or subagent metadata sequentially. Missing scheduling metadata is not a blocker. Do not infer parallel permission from numbered steps alone.

When working in a git repository, capture the initial status and current diff boundaries before parallel dispatch so pre-existing user changes can be distinguished and preserved.

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

The main agent is the coordinator and remains the sole writer of the original execution record. It owns dependency scheduling, shared or cross-phase files, integration, conflict resolution, final verification, the `$simplify` pass, the agent-doc decision, and the final response.

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

Update the original execution record in place as work progresses. Do not create a separate execution-progress section unless the user asks for one.

In `## Step-by-Step Plan`, convert steps to a checklist if needed and update each item directly:

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

When checks are run, update `## Verification` directly with checkboxes or short result notes. Include skipped checks and residual risk in the existing `## Verification` or `## Handoff Notes` sections.

### Amendment and Evidence Gate

Before substantive work or a user-facing response, persist every material user correction, added request, changed decision, discovered fact, verification result, external handoff, or out-of-scope item received while execute mode is active.

Use or create `## Amendments and Evidence` in the original execution record. Remove the initial `None at approval` placeholder when adding the first real entry. Give entries stable IDs such as `A001` and record:

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

1. Pass the request through the `Amendment and Evidence Gate`, then add it to `## Step-by-Step Plan` before starting it. Reference its amendment ID and use a concise note such as `Added by user on <YYYY-MM-DD>` so the scope change is distinguishable from the approved baseline.
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
6. Record every successful commit under `## Handoff Notes`. Create a concise `### Commits` subsection when needed and include the full commit SHA, subject, branch, and associated phase or checklist item in chronological order.
7. If a commit attempt fails, keep the unit in progress while recovering and add a concise failure note only when it helps a future session. Use `[!]` only when the failure meets the genuine blocker definition.
8. After all implementation units included in the current session are committed, define the simplify scope as every current-session commit after the captured starting `HEAD` through the current `HEAD`, plus any remaining in-scope staged, unstaged, or untracked changes. Do not substitute only the final commit or current working-tree diff, even when the session executed a single phase.
9. Commit simplify-driven fixes as one or more separate coherent commits after their checks pass. Record them like other session commits. Never rewrite, squash, or amend the earlier implementation commits unless the user explicitly requests history rewriting.

The final commit SHA cannot be embedded in the commit that produced it because changing the plan would change that SHA. Record the SHA immediately after the commit, do not amend solely to make the SHA self-referential, and disclose the resulting plan-only working-tree change. Create a separate plan-metadata commit only when the user explicitly requests it; do not try to record that metadata commit's own SHA inside itself.

## Implementation Workflow

1. Resolve, adopt, and read the complete execution-record path; activate or re-enter execute mode and persist its metadata.
2. Inspect enough repository context to execute safely.
3. Build the dependency and ownership map, validate declared waves, identify the current ready set, and divide each selected phase into commit-sized logical work units.
4. Select a safe execution wave; serialize phases that are unannotated, coupled, or not worth delegating.
5. Mark the selected phase items in progress and dispatch each eligible delegated phase with the required ownership and return contract.
6. Execute any coordinator-owned phase that can run concurrently without conflicting with active subagents.
7. Collect subagent reports, inspect actual changed files or resources against the baseline and assigned ownership, and review each implementation.
8. As each commit-sized unit becomes coherent, run its focused checks, review and commit it immediately, then continue with the next unit. A selected phase may therefore produce multiple commits before its phase-local checks are complete.
9. Run or confirm phase-local checks, mark each accepted phase completed, and run the wave's integration gate before unlocking dependent phases; recover or mark a genuine blocker as appropriate.
10. Repeat the ready-set workflow until all phases are accepted or a genuine blocker requires user input or an external state change.
11. Run the plan's final `## Verification` checks on the integrated result.
12. Use `$simplify` to review the complete current-session commit range from the captured starting `HEAD` through the current `HEAD`, together with any remaining in-scope working-tree changes.
13. Fix confirmed or plausible `$simplify` findings that are in scope.
14. Re-run the narrowest meaningful checks after any simplify-driven fixes, then commit those fixes separately in coherent units.
15. If the current execution session's commit range or remaining working-tree diff contains substantial agent-facing changes that are not already covered in agent docs, use `$update-agent-docs` with the session-change-only scope in this skill.
16. Re-run the narrowest meaningful checks after any agent-doc updates.
17. Update the plan status, checklist, amendments and evidence, verification notes, execution decisions, `Last updated`, and residual risks.
18. If the user adds follow-up work, changes an earlier decision, provides a material handoff or evidence item, or requests a commit, pass it through the amendment gate and resume the applicable workflow before treating the task as complete.
19. Apply the final completion gate and continue working if any requirement fails.

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

## Required Simplify Pass

After the plan's implementation units are committed, invoke `$simplify` on the complete current-session changes before the final response.

- Scope `$simplify` to the diff from the captured starting `HEAD` (exclusive) through the current `HEAD` (inclusive), plus remaining in-scope staged, unstaged, and untracked changes. Include all implementation commits created in the session, not only the most recent commit or working-tree diff.
- Run one coordinator-owned simplify pass only after all parallel phase results have been collected and integrated; do not run independent simplify passes inside subagents.
- Allow `$simplify` to apply focused fixes for confirmed or plausible issues in scope.
- Commit simplify-driven fixes separately after focused checks pass; do not rewrite earlier implementation commits unless the user explicitly requests it.
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
- If there is no git repository or no current-session change to inspect, skip this step and state the limitation in the final response.
- If `$update-agent-docs` requires additional authorization, including permission to edit outside the repository, skip the optional update and record the reason unless that external documentation update is itself an explicit plan goal. Do not leave an otherwise completed implementation in progress solely because an automatic agent-doc update could not run.

## Security Review Offer

Do not run `$security-review` automatically.

The security-review offer is post-completion and must not leave the execution plan marked in progress.

At the end, ask the user whether they want a security review of the current execution session's changes.

If the user says yes, use `$security-review` with this scope constraint:

- Review only the current execution session's commit range plus remaining in-scope working-tree changes.
- Do not review the full repository.
- Read surrounding context, callers, or configs only as needed to validate a finding from the diff.
- Report findings first, following the `$security-review` output format.

## Final Completion Gate

Before sending a response that claims implementation completion, a genuine blocker, or an explicit-exit pause:

- Re-read the plan checklist and confirm no in-scope `[ ]` or `[~]` item remains.
- Confirm every `[!]` item satisfies the Genuine Blocker Definition.
- Confirm unrelated ready phases were not skipped because another phase failed.
- Confirm final verification was run or its unavailability and residual risk were documented.
- Confirm the required simplify review was completed through the skill or locally.
- Confirm optional agent-doc limitations did not prevent plan completion.
- Confirm every material user correction, follow-up deliverable, decision, evidence item, and out-of-scope handoff received while execute mode was active was recorded under `## Amendments and Evidence`.
- Confirm every executable amendment was reflected in the checklist and completed, paused by explicit exit, or genuinely blocked.
- If commits were created, confirm their SHA, subject, and branch were recorded in `## Handoff Notes`, and disclose any post-commit plan-only working-tree change.
- Confirm `Execute mode: Active` remains set unless the user explicitly exited; implementation completion alone must not change it.
- Persist the final checklist, status, amendments and evidence, verification results, execution decisions, `Last updated`, and residual risks to the execution record.

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
- Whether the execution record was updated
- Which user-requested corrections, follow-up items, evidence, or out-of-scope handoffs were appended to the record
- Whether execute mode remains active or was explicitly exited, plus the exact adopted execution-record path
- Commit SHA, subject, and branch for commits created during execution, plus whether recording them left a plan-only working-tree change

Then ask whether the user wants `$security-review` on the current execution session's changes when implementation reached `Implemented`, unless they already answered that question in the current turn.

For a read-, inspection-, summary-, adoption-, or evidence-only checkpoint, report the exact adopted execution-record path, what metadata or evidence was updated, that no implementation was performed unless separately authorized, and that execute remains active until explicit exit. Do not offer a security review solely because the record was read or adopted.
