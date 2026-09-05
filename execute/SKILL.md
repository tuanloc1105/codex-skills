---
name: execute
description: Execute an approved version 4 plan or execution-ready discussion bundle, preserving its exact path, scope, evidence, and verification across sessions. Support explicit pause, exit, and recovery without marking unfinished work complete.
---

# Execute

## Entry and Authority

Use this workflow when the user invokes `$execute` or clearly requests executing/resuming an accepted execution record. Reading, reviewing, summarizing, or mentioning a record alone does not activate execute. If execute is already active, a read-only turn may update relevant evidence without authorizing implementation.

Require the bundle directory or its `index.md`, unless an exact record is already active. Canonicalize and retain that root as the sole execution record. Read `index.md` and every manifest file on adoption, restore the checkpoint, and revalidate material repository or external drift. Do not copy a direct discussion handoff into another plan.

Accept only version 4 bundles with a valid manifest, `context.md`, `decisions.md`, `plan.md`, `verification.md`, `evidence.md`, and every declared phase file. A discussion record must already have `Mode status: Exited` and `Execution readiness: Ready`. If it is not ready, report the missing handoff state; do not silently select unresolved options or manufacture approval.

An explicit request to execute the supplied plan approves its recorded scope even if its status is still Draft or Ready, unless a conflicting prohibition or material unresolved choice requires clarification. A read/adopt request adds no implementation authority. Existing authorization persists for the same task and scope unless revoked or invalidated; do not demand renewed permission solely because context was compacted or a session resumed.

Implementation authority does not imply commit, push, deploy, or unrelated external actions. Follow explicit user instructions, repository policy, and recorded authorization. Ask only when a missing decision materially affects outcome or authority; safe implementation details do not require a new approval.

Before beginning or resuming implementation in any Git repository, create or safely reuse a dedicated linked worktree for this execution record. This is mandatory regardless of plan size, checkout cleanliness, or whether work runs sequentially. Never implement in the user's original checkout or silently fall back to it. Follow the dedicated-worktree procedure in the implementation reference, record its path and branch, and give every implementation tool and subagent that workspace explicitly. Read-only adoption does not require a worktree; non-Git directories skip Git-specific setup.

When local commits are authorized, the smallest-complete-verified-unit commit cadence is mandatory. Commit each such unit immediately after its focused checks pass and its changes are accepted, before starting the next separable unit. Do not accumulate an entire phase or plan before committing. Unit boundaries follow coherent behavior and dependencies, not an arbitrary file or line count. Follow the implementation reference; this cadence does not itself grant commit, push, or deployment authority.

On entry, persist `Execute mode: Active`, current timestamp, and the resume instruction to read this exact bundle. Use the `Durable` profile by default, upgrading Lightweight and preserving Audited. Keep implementation status independent of mode status. Record the source and scope of execution authority; `Execution authorization: Granted` is an acknowledgment of user authority, not a grant produced by the hook.

## Reference Routing

Read each applicable reference completely:

- [references/implementation.md](references/implementation.md): implementation, amendments, commits, workspace selection, phase scheduling, or recovery.
- [references/completion.md](references/completion.md): final implementation verification and reporting, including a blocked or paused result.

Read-only evidence turns need neither reference unless their subject requires it. Keep Required references minimal (`None` when neither applies), add the relevant file through a record transaction, read it, and acknowledge rules before the next mutation. Do not activate other skills merely because the record mentions their names; use them only when the task requires them and the user has not excluded them.

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

Use the installed, trusted plugin's exact `workflow_modes_control.py` path with the configured Python interpreter. Run each command alone, end it with `--marker workflow-modes-v1`, and verify model-visible `WORKFLOW_*` confirmation.

- Fresh adoption without an active hook: persist Active metadata, then `activate execute --record <root>`. On a plan/discuss handoff, the successful transition already binds execute to this exact record: read/sync the bundle and rules first, then transactionally persist Active metadata. Do not reactivate to discard or reset state, and never run plan-init for an execute handoff. If this same execute record is already active, resume it without another activate call.
- Activation and compaction require reading the full manifest, record sync, and rules-sync. On a prompt, follow `sync_status`: current needs no reread, snapshot needs only the Active Snapshot and snapshot sync, record needs a complete bundle read and record sync.
- Before bundle edits, `write-open --record <root> --previous-revision <acknowledged revision>`, declaring new Markdown paths with `--path`; update affected files together and `write-close --record <root>`. A valid no-op transaction may close.
- Before a final response, `checkpoint --record <root>`; use `--no-change` only when the record remains accurate and the turn has no material deltas. Routine progress commentary does not require checkpointing or closing an active work unit.

For each bounded mutating work unit:

1. Through one record transaction, persist a stable evidence ID, `<!-- workflow-action:<ID> status:open -->` in `evidence.md`, and its matching Active action summary in `index.md`.
2. Close the write, then `action-open --record <root> --evidence-id <ID> --impact <non-source|source-confirmed> --path <absolute-file>...`, with only needed `--unscoped <shell|git|external>` classes. Do not open a separate action for every file/tool call.
3. Perform only authorized effects in that unit. Reconcile results, affected phase status, and verification in one write transaction; replace the marker with `status:completed`, `failed`, `blocked`, `paused`, or `cancelled`, and clear Active action.
4. Close the write, then `action-close --result <matching-result>` before a final response, deactivation, or unrelated work unit.

The hook enforces recognized file schemas and conservative classification of opaque execution. It is not a sandbox or proof of shell/external side effects. File scopes are exact files; unscoped classes grant no semantic authority and cannot enforce a repository-root boundary for arbitrary programs. Inspect commands and actual effects, include every visible mutation class in compound commands, and prefer inspectable file tools. Never attach other commands to a lifecycle call.

## Recovery and Compatibility

Use `suspend --record <root> --reason persistence-failed` when a bundle cannot be saved; use `--reason user-stop` when a stop cannot be reconciled immediately. This permits a final blocker/stop response, retains open action/transaction state, and denies all non-record mutation. Repeated unresolved Stop blocks also suspend after a retry instead of looping.

Repair through the existing record transaction, or open one using the last acknowledged revision and the cached manifest paths if the bundle became unreadable. Restore from known evidence without overwriting unrelated changes. Close the valid write, persist and close the actual action result, read/sync the repaired bundle and required rules, then `recover --record <root>`. Resume only within surviving user authority, or persist exit and deactivate. Recovery never marks incomplete work completed. The legacy action-abort command now suspends and retains action state.

Check installed `--help` before relying on new commands. If the installed hook is incompatible, report that limitation; do not bypass its denial or reinstall during an active task. If enforcement is unavailable, read-only adoption and evidence updates may continue, but implementation waits for compatible enforcement unless a higher-priority user instruction explicitly chooses an unenforced workflow.
