# Execute Implementation Reference

Read before implementation, amendments, workspace setup, commits, scheduling, or recovery. Add this file to Required references through a record write, read it, then acknowledge rules before mutating work.

## Workspace Selection

Follow the user's chosen workspace and repository policy. Inspect the starting branch, HEAD, staged/unstaged diffs, untracked paths, and existing worktrees before implementation. Preserve all pre-existing changes and record the baseline needed to distinguish this task's changes.

Use a dedicated worktree when isolation is required by policy, requested by the user, or materially protects concurrent/pre-existing work. Otherwise a clean or safely scoped existing checkout is valid. Do not ask about a reversible workspace choice that can be resolved from the task and policy.

- Reuse a worktree only when it belongs to this task and has no conflicting unrelated work. Record the actual path, branch, and base in evidence.
- Choose a task-focused branch under repository conventions. Avoid hiding unrelated files when maintaining ignore rules; prefer an existing ignored worktree location or local Git exclude configuration when permitted.
- If a recorded worktree disappeared, inspect the branch and surviving work before safe recreation. Never discard changes or reset a checkout to recover it.
- When no worktree can be created, use an existing checkout only if authorized and safe; otherwise report the concrete blocker. Do not treat worktree creation itself as a completion criterion.
- For non-Git work, skip Git operations. The execution record stays at its exact bound path even if implementation uses another workspace. Required authorized outputs or skill mirrors may live elsewhere; record their exact scope and repository rules rather than banning all outside-worktree writes.

## Dependency Scheduling and Ownership

For a simple plan, execute its linear checklist. For phases, read each phase's ID, Depends on, Wave, Subagent, Owned scope, Produces, tasks, verification, and acceptance criteria. Phase files are authoritative; `plan.md` links them and describes integration. Validate links and dependencies before acting. A duplicate legacy table must agree with the phase files.

Build the dependency-ready set from accepted completed prerequisites. Wave is the earliest wave derived from those dependencies, not permission to ignore a dependency. Revalidate ownership and coupling against live code.

Delegate only when authorized and useful: a bounded phase needs stable inputs, non-overlapping file/resource ownership, independent verification, and a clear output. Shared contracts, migrations, lockfiles, generated files, external effects, or stateful tests need explicit coordination or serialization. Available slots are a ceiling, never a target. Unavailable or unhelpful delegation means sequential execution, not a blocker.

The coordinator is the sole writer of the record bundle. Subagents do not change phase status metadata, commit, push, deploy, or mutate shared resources unless separately authorized. Assume a shared workspace. Give each delegated task:

- Phase goal, satisfied dependencies, inputs, and output contract
- Exact owned files/resources and exclusions; tell it others share the codebase and their changes must be preserved
- Relevant repository instructions and required verification
- A requirement to report unexpected overlap, scope changes, or blockers before proceeding
- A return contract: changes, checks, assumptions, risks, and remaining work

Mark dispatched phases in progress first. Inspect actual changes and checks before accepting results. Run necessary integration gates before releasing dependent phases. Continue safe independent work while recovering a failed phase.

## Bounded Work Units

Follow the approved goal and constraints; read relevant code and callers before editing. Use the repository's coding workflow, keep changes scoped, and verify preserved behavior. Open one evidence-backed action per coherent work unit as described in the entrypoint, including authorized setup, tests with side effects, Git operations, or external writes. An action can cover several related files and calls; do not create one per file.

A failed test/build is an intermediate result. Inspect the failure, recover proportionately, and rerun the relevant check after a fix. Do not retry endlessly when progress requires an external decision or system. Record useful failure evidence, not raw terminal logs.

## Amendments and Evidence

Before related implementation, record material user corrections, added deliverables, changed decisions, and discovered constraints in `evidence.md`. Give an entry a stable ID (such as A001), timestamp, source locator, affected work, and actual status. Link to existing evidence instead of repeating it across files.

- Add or revise executable checklist items, dependencies, ownership, and verification when the approved task changes. Record the source of authority; do not expand scope merely because a possible improvement was found.
- Preserve completed history. Mark obsolete pending work superseded and create corrective work for already implemented behavior that must change.
- Evidence-only turns need no artificial implementation item or status change.
- Reopen Implemented/Paused/Blocked to In progress only when authorized task work can resume.
- If the user clearly moves to a separate task, record a concise handoff, pause/deactivate this workflow, and respect the new task boundary. Do not append unrelated work to the approved baseline.
- Keep evidence concise: source, result, affected acceptance criterion, and revalidation condition. Do not store transcripts, hidden reasoning, secrets, unrelated conversation, or raw outputs.
- Batch related findings and checklist changes in one record transaction at a meaningful checkpoint. Do not create timestamp-only updates on unchanged turns. Summarize superseded detail before the bundle approaches 2 MiB, preserving authority, unresolved work, decisions, and evidence locators.

Use these checklist states:

- `[ ]` pending
- `[~]` in progress (annotate a user pause if work stops partway)
- `[x]` completed and accepted
- `[!]` genuinely blocked

Multiple items may be in progress only when ownership and dependencies make concurrent work safe. A blocked prerequisite may leave dependent items pending with its ID noted. Update phase status in its phase file, overall status in `index.md`, checks in `verification.md`, and evidence in `evidence.md` through one consistent write. Do not duplicate authoritative scheduling state in plan tables.

## Commits When Authorized

Implementation does not automatically authorize commits. Follow explicit user/plan/repository instructions; if commits are not authorized, leave the verified changes reviewable in the working tree. Do not ask for commit permission merely to finish an otherwise completed task.

When commits are authorized:

1. Use the captured starting HEAD and diff boundaries to isolate this task's changes.
2. Group coherent behavior changes with their necessary tests and dependencies. Commit size follows reviewability, not a mandatory one-file/DTO/component cadence or a forced phase boundary.
3. Run focused checks, review the staged diff, and stage only current-task files/hunks. Preserve pre-existing and concurrent changes.
4. Follow repository message conventions. Do not push, deploy, squash, amend, or rewrite history without corresponding authority.
5. Record SHA, subject, branch, and associated work in evidence. The producing commit cannot contain its own SHA; do not amend to chase a self-reference or create an unrequested metadata commit.
6. Scope any later review to the whole task's committed changes plus in-scope working-tree changes, not just the latest commit. Reconcile a recorded baseline with branch/worktree drift before using it as a range.

## Recovery and User Stops

Inspect partial effects before retrying. Use a safe alternative, serialize coupled work, or finish delegated work locally when that resolves the failure. Continue independent authorized work when a dependency is blocked.

A user stop ends new scheduling immediately. Interrupt owned work appropriately, record actual effects, leave unfinished items pending/in progress, and close actions with paused/cancelled results. Do not run optional cleanup, commits, reviews, or remaining phases to satisfy completion after a stop.

If persistence fails, follow the entrypoint suspend/repair/recover protocol. Keep the exact record, cached manifest scope, and open action evidence; suspension permits reporting the blocker but never grants non-record mutation. Do not discard unrelated changes or erase an open action to escape a denied hook.

## Execution Sequence

1. Adopt the exact record, restore scope/authority, and capture the starting workspace and diff boundaries.
2. Select the workspace under policy, record it, and perform any authorized setup as a bounded action.
3. Inspect context, choose dependency-ready work, and amend the record for material new information.
4. Execute coherent work units, verify and reconcile their evidence; commit only if authorized.
5. Accept phase outputs and integration checks before starting dependents. Continue until the authorized task is complete, genuinely blocked, or explicitly stopped.
6. Apply the outcome-specific completion reference, persist the actual result, checkpoint, and report it.
