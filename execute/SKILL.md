---
name: execute
description: Take ownership of a delegated execution task and complete its version 4 plan or execution-ready discussion bundle, including necessary delivery steps, with durable evidence and proportionate recovery. Workflow bookkeeping supports execution rather than granting permission for each action.
---

# Execute

## Entry and Authority

Use this workflow when the user invokes `$execute` or clearly requests executing/resuming an accepted execution record. Reading, reviewing, summarizing, or mentioning a record alone does not activate execute. If execute is already active, a read-only turn may update relevant evidence without authorizing implementation.

Require the bundle directory or its `index.md`, unless an exact record is already active. Canonicalize and retain that root as the sole execution record. Read `index.md` and every manifest file on adoption, restore the checkpoint, and revalidate material repository or external drift. Do not copy a direct discussion handoff into another plan.

Accept only version 4 bundles with a valid manifest, `context.md`, `decisions.md`, `plan.md`, `verification.md`, `evidence.md`, and every declared phase file. A discussion record must already have `Mode status: Exited` and `Execution readiness: Ready`. If it is not ready, report the missing handoff state; do not silently select unresolved options or manufacture approval.

An explicit request to execute delegates end-to-end responsibility for the supplied task, even if its recorded status is still Draft or Ready. Carry out the accepted outcome and its necessary implementation, verification, recovery, and delivery steps without asking the user to approve each tool, file, work unit, or effect class. A read/adopt request adds no implementation authority. Delegation persists across turns, compaction, and resume until the user changes or revokes it.

Resolve authority from the user's actual request and explicit constraints. Record that authority in the bundle; do not treat an agent-written action summary, missing marker, stale permission label, or hook advisory as an independent restriction. Correct stale metadata yourself when the user's intent is clear. Ask only for an unresolved decision that materially changes the outcome, missing authority beyond the delegated task, or an actual conflict with an explicit prohibition or higher-priority instruction.

For Git work, execution includes task branches, worktree setup, local incremental commits, and the delivery steps needed by the requested outcome. A request to create a PR/MR includes a normal push of the task branch to the intended remote when needed to create it; inspect the branch, remote, and task diff, then push and create the PR/MR without requesting separate push permission. Do not reinterpret PR creation as limited to an already-published branch unless the user imposed that limit. Execute a deployment when deployment is part of the accepted task. An implementation-only task does not acquire unrelated publication, deployment, or destructive history rewriting. Explicit user prohibitions and higher-priority policies still apply.

Before beginning or resuming implementation in any Git repository, create or safely reuse a dedicated linked worktree for this execution record. This is mandatory regardless of plan size, checkout cleanliness, or whether work runs sequentially. Never implement in the user's original checkout or silently fall back to it. Follow the dedicated-worktree procedure in the implementation reference, record its path and branch, and give every implementation tool and subagent that workspace explicitly. Read-only adoption does not require a worktree; non-Git directories skip Git-specific setup.

When local commits are authorized, the smallest-complete-verified-unit commit cadence is mandatory. Commit each such unit immediately after its focused checks pass and its changes are accepted, before starting the next separable unit. Do not accumulate an entire phase or plan before committing. Unit boundaries follow coherent behavior and dependencies, not an arbitrary file or line count. Follow the implementation reference; local commit authority follows the implementation request as defined above; delivery authority follows the requested outcome and its necessary steps as defined above.

On entry, persist `Execute mode: Active`, current timestamp, and the resume instruction to read this exact bundle. Use the `Durable` profile by default, upgrading Lightweight and preserving Audited. Keep implementation status independent of mode status. Record the source and scope of execution authority; `Execution authorization: Granted` is an acknowledgment of user authority, not a grant produced by the hook.

## Reference Routing

Read each applicable reference completely:

- [references/implementation.md](references/implementation.md): implementation, amendments, commits, workspace selection, phase scheduling, or recovery.
- [references/completion.md](references/completion.md): final implementation verification and reporting, including a blocked or paused result.

Read-only evidence turns need neither reference unless their subject requires it. Keep Required references minimal (`None` when neither applies), read the relevant file and record the reference set at the next meaningful checkpoint. A missing rules-sync acknowledgment is bookkeeping, not a reason to stop authorized work. Do not activate other skills merely because the record mentions their names; use them only when the task requires them and the user has not excluded them.

Keep `Supporting skills` in the Active Snapshot limited to skills needed for the next safe action, with each skill name or locator and its purpose; use `None` when none apply. This is resume context, not the mode reference allowlist: do not add these names to `Required references` or `rules-sync`. On adoption or after compaction, reassess their relevance and the user’s exclusions before loading them; a recorded mention grants no authority and does not require automatic activation. Refresh this field when the next action changes, and remove skills whose work is finished. Existing bundles without it remain valid; add it during the next material record update when useful.

## Work and Completion

Execute all authorized in-scope work, including dependency-ready phases and accepted amendments. Treat failed attempts, test failures, unavailable delegation, and context pressure as intermediate states; recover proportionately and continue independent safe work.

A genuine blocker requires a material user choice, unavailable authority/credential/system, a higher-priority prohibition, or an irreconcilable conflict with pre-existing changes. Do not wait for optional tools, reviews, or a preferred number of subagents. Do not retry indefinitely when the same failure requires external intervention.

Use the outcome-specific gate in the completion reference:

- `Implemented`: all in-scope work is complete, with verification results and any limitations recorded.
- `Blocked`: no authorized independent work can proceed; blockers and dependent unfinished items remain accurate.
- `Paused`: the user explicitly stopped with unfinished work. Preserve pending items; do not finish them against the stop instruction.

Keep execute active across normal completion only for this adopted task. Record material follow-ups to that task as amendments. Unrelated conversation does not belong in the bundle. If the user clearly switches to a separate task, persist a concise handoff and pause this workflow instead of silently absorbing the new task into the old plan. An instruction to keep work separate must preserve that boundary.

## Pause, Cancellation, and Exit

Honor explicit exit, pause, cancel, or stop instructions without redundant confirmation. Stop scheduling new work immediately; interrupt owned running work when appropriate and reconcile its actual effects. Close open actions as `paused` or `cancelled`, never `completed` merely to satisfy a gate.

Persist current evidence and verification, leave unfinished checklists accurate, and set `Execute mode: Paused` for a pause or `Exited` for exit/cancel. Preserve `Status: Implemented` or `Blocked` if still accurate; otherwise use `Status: Paused`. Close record writes/actions, checkpoint, and deactivate. Exit authorizes neither discarding changes nor implementing remaining work. Explicitly resuming this record reactivates its workflow.

If persistence cannot complete, suspend and report the last durable checkpoint and unsaved facts honestly. Reporting a stop or blocker does not require completed implementation, a worktree, commits, simplify, or successful final checks.

## Workflow Modes Hook

The hook is an optional execution companion. In execute mode, action paths, effect classes, evidence markers, revisions, rules-sync, and checkpoints are bookkeeping, not a second authorization system. Apply the same policy to direct file tools, shell/Git commands, external tools, and orchestration wrappers. Missing or stale metadata must not cause a permission question or prevent completing delegated work. Explicit user stops still take precedence.

When the installed plugin is available and trusted, use its exact `workflow_modes_control.py` path with the configured Python interpreter. Run lifecycle commands alone, end them with `--marker workflow-modes-v1`, and verify model-visible `WORKFLOW_*` confirmation. A control process exit code alone does not prove a state update.

- On fresh adoption, persist Active metadata and use `activate execute --record <root>`. A successful plan/discuss transition already binds this exact record; reconcile its metadata without reactivating to reset pending state. Never run plan-init for an execute handoff.
- On adoption or compaction, restore the full manifest and applicable references. On later prompts, use `sync_status` to avoid unnecessary rereads. Sync the record and rules when available; acknowledgment is not a prerequisite for delegated implementation.
- Batch material evidence, amendments, phase progress, and verification at meaningful work-unit boundaries. Preserve version 4 bundle consistency. Use `write-open --record <root> --previous-revision <revision>` and `write-close --record <root>` when supported, declaring new Markdown paths with `--path`.
- Actions are optional work-unit tracking. When useful, persist a stable evidence ID and `<!-- workflow-action:<ID> status:open -->` in `evidence.md`, then `action-open` with the record, evidence ID, impact, paths, and effect classes. One action may cover implementation, verification, commits, and requested delivery for a coherent unit. Additional necessary files or effects do not require a new user approval or closing/reopening the action before continuing.
- Reconcile any opened action with its actual terminal marker (`completed`, `failed`, `blocked`, `paused`, or `cancelled`) and matching `action-close --result`. Attempt `checkpoint --record <root>` before a final report; use `--no-change` when the record is still accurate. Progress commentary requires neither a checkpoint nor closing a work unit.

A `WORKFLOW_EXECUTE_CONTROL_NOT_APPLIED` result means that bookkeeping did not change. Correct it when possible, preserve unresolved evidence honestly, and continue independent delegated work. Do not retry the same failed bookkeeping operation indefinitely, fabricate a successful checkpoint, or send a new permission question merely to satisfy it. The hook does not prove semantic authority or the side effects of arbitrary programs; the agent remains responsible for the user's task and constraints.

## Recovery and Compatibility

A record persistence failure does not revoke execution authority. Keep unsaved material evidence in the current task context, repair the exact bundle from known facts, and continue independent work whose scope and prerequisites remain known. Report any evidence that could not be saved; do not claim durable completion of the record. Stop dependent work only when lost context or conflicting evidence makes it impossible to proceed correctly.

Use `suspend --record <root> --reason persistence-failed` to record persistence trouble when supported; execute treats this as a repair reminder. Use `--reason user-stop` only for an actual user stop that cannot yet be reconciled; it blocks new non-record mutation. Never substitute persistence-failed to bypass a user stop.

Repair through an existing record transaction or the last acknowledged revision and cached manifest paths. Preserve unrelated changes and the actual action outcome, sync the repaired record/rules, and `recover --record <root>`. Resume stopped work only when the user resumes it. Recovery never marks unfinished work completed.

Check installed `--help` before relying on new commands. An absent optional plugin does not block execution: maintain the bundle directly and report the integration limitation when relevant. An older installed hook may still deny calls; do not bypass a denial, alter trust, or reinstall during an active task. Use a supported recovery path, continue permitted independent work, and report the exact compatibility blocker if necessary. Do not describe an old hook's bookkeeping denial as missing user authorization.
