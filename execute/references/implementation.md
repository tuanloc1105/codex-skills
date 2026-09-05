# Execute Implementation Reference

Read before implementation, amendments, workspace setup, commits, scheduling, or recovery. Add this file to Required references through a record write, read it, then acknowledge rules before mutating work.

## Mandatory Dedicated Worktree

Follow the user's chosen workspace and repository policy. Inspect the starting branch, HEAD, staged/unstaged diffs, untracked paths, and existing worktrees before implementation. Preserve all pre-existing changes and record the baseline needed to distinguish this task's changes.

Before beginning or resuming implementation in each affected Git repository, create or safely reuse a dedicated linked worktree bound to this execution record. This is mandatory for small and large plans alike, including sequential work and clean repositories. Never implement in the user's original checkout. Do not ask whether isolation is worth the overhead or infer an exception from plan size. Higher-priority instructions still apply; report an actual conflict rather than silently choosing the original checkout.

- Inspect `git worktree list --porcelain`. Reuse a linked worktree only when it is dedicated to this record and has no conflicting unrelated work. Keep new worktrees under the main repository's `.worktrees/` directory unless repository policy specifies another dedicated location. Verify an in-repository location is ignored before creating it; use a narrow ignore rule or permitted local Git exclude configuration without hiding unrelated files.
- Use the approved task branch and base under repository and domain policy. Respect any required branch-creation authorization; do not invent a different branch to avoid it or force-checkout a branch already used elsewhere. Record the canonical worktree path, branch, base, and registration evidence before implementation.
- Run implementation edits, generators, checks, staging, authorized commits, integration, and simplify fixes from the dedicated worktree. Set tool working directories and subagent paths explicitly; changing a terminal directory alone does not redirect absolute file paths or other tools. Verify the worktree identity again on resume or after workspace drift.
- If a recorded worktree disappeared, inspect the branch and surviving work before safe recreation. Update the recorded replacement path and verify it before resuming. Never discard changes or reset the original checkout to recover it.
- If a dedicated worktree cannot be created or safely reused, stop dependent implementation and report the concrete blocker after safe recovery. Do not fall back to the original checkout. Read-only investigation and accurate blocker/pause reporting remain allowed without successful worktree setup.
- For non-Git work, skip Git operations. The execution record stays at its exact bound path even if implementation uses another workspace. Required authorized outputs or skill mirrors may live elsewhere; record their exact scope and repository rules rather than banning all outside-worktree writes.

## Dependency Scheduling and Ownership

For a simple plan, execute its linear checklist. For phases, read each phase's ID, Depends on, Wave, Subagent, Owned scope, Produces, tasks, verification, and acceptance criteria. Phase files are authoritative; `plan.md` links them and describes integration. Validate links and dependencies before acting. A duplicate legacy table must agree with the phase files.

Build the dependency-ready set from accepted completed prerequisites. Wave is the earliest wave derived from those dependencies, not permission to ignore a dependency. Revalidate ownership and coupling against live code.

Delegate only when authorized and useful: a bounded phase needs stable inputs, non-overlapping file/resource ownership, independent verification, and a clear output. Shared contracts, migrations, lockfiles, generated files, external effects, or stateful tests need explicit coordination or serialization. Available slots are a ceiling, never a target. Unavailable or unhelpful delegation means sequential execution, not a blocker.

The coordinator is the sole writer of the record bundle. Subagents do not change phase status metadata, commit, push, deploy, or mutate shared resources unless separately authorized. Assume a shared workspace. Give each delegated task:

- Phase goal, satisfied dependencies, inputs, and output contract
- Exact dedicated-worktree path, owned files/resources and exclusions; tell it others share the codebase and their changes must be preserved. Prohibit implementation in the original checkout.
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

## Mandatory Small Commits When Authorized

In a Git repository, a clear request to implement the adopted record authorizes local incremental commits for that implementation unless the user or plan explicitly forbids commits. Follow repository and applicable domain commit policies. Do not require a separate commit request for each unit or phase. If commits are forbidden or authority is otherwise withheld, preserve the verified changes in the working tree; reading or adopting a record alone does not authorize commits.

After implementation is authorized, commit the smallest complete, accepted, and independently verifiable unit of work as soon as its proportionate focused check passes. Apply this cadence across every domain; a single finished component, DTO, design token set, configuration unit, migration, documentation section, test fixture, script, workflow step, or similarly self-contained artifact may each be its own commit. Prefer a smaller valid checkpoint over combining separately complete units merely because they belong to the same task, checklist step, feature, layer, or phase. Include only the minimum dependent edits required to make the unit complete and keep the repository in an acceptable state. A saved file, partial scaffold, broken artifact, or change that is only valid after omitted required work is not a commit unit. Treat phases and checklist steps as scheduling containers, never as commit boundaries: either may produce many commits, and the same cadence applies when the current execution session covers only one phase or step. Preserve dependency order, commit before starting the next separable unit, and do not wait until the phase, step, or plan is complete. Do not commit when the user or plan forbids commits.

When commits are authorized:

1. Use the captured starting HEAD and diff boundaries to isolate this task's changes.
2. Before coding, identify the smallest complete, independently verifiable units within the selected phase. A behavior slice, component, DTO, configuration change, or refactor prerequisite may be a unit only when it is coherent with its required tests and dependencies. Do not split mechanically by file or line count, or commit a scaffold that only works after omitted changes.
3. As soon as a unit's focused checks pass and the coordinator accepts it, stage only its current-task files/hunks, review the staged diff, and commit immediately before starting the next separable unit. Preserve pre-existing and concurrent changes. Do not combine separately complete units merely because they share a phase, checklist step, feature, or layer. A phase normally produces multiple commits unless it is genuinely indivisible; this cadence is mandatory even when executing only one phase. Subagents return bounded unit results for coordinator verification and commit, without staging or committing another worker's changes.
4. Follow repository message conventions. Do not push, deploy, squash, amend, or rewrite history without corresponding authority.
5. Record SHA, subject, branch, and associated work in evidence. The producing commit cannot contain its own SHA; do not amend to chase a self-reference or create an unrequested metadata commit.
6. Scope any later review to the whole task's committed changes plus in-scope working-tree changes, not just the latest commit. Reconcile a recorded baseline with branch/worktree drift before using it as a range.

If a commit fails, inspect the failure and recover before moving to the next separable unit; do not defer failed commits into an end-of-phase batch. A user stop still takes precedence: preserve the verified but uncommitted work and report it instead of creating a commit after a stop. Apply the same cadence to authorized review/simplify fixes as separate coherent commits; do not rewrite earlier history without authority.

## Recovery and User Stops

Inspect partial effects before retrying. Use a safe alternative, serialize coupled work, or finish delegated work locally when that resolves the failure. Continue independent authorized work when a dependency is blocked.

A user stop ends new scheduling immediately. Interrupt owned work appropriately, record actual effects, leave unfinished items pending/in progress, and close actions with paused/cancelled results. Do not run optional cleanup, commits, reviews, or remaining phases to satisfy completion after a stop.

If persistence fails, follow the entrypoint suspend/repair/recover protocol. Keep the exact record, cached manifest scope, and open action evidence; suspension permits reporting the blocker but never grants non-record mutation. Do not discard unrelated changes or erase an open action to escape a denied hook.

## Execution Sequence

1. Adopt the exact record, restore scope/authority, and capture the starting workspace and diff boundaries.
2. For every affected Git repository, create or verify its mandatory dedicated linked worktree as an authorized bounded setup action, record the path and branch, and bind implementation tools/subagents to it before any implementation. Skip this setup only for non-Git work or an explicit higher-priority instruction.
3. Inspect context, choose dependency-ready work, and amend the record for material new information.
4. Execute the smallest complete work units, verify and reconcile their evidence, and, when commits are authorized, commit each accepted unit immediately before beginning the next separable unit. Do not wait for the phase or plan to finish.
5. Accept phase outputs and integration checks before starting dependents. Continue until the authorized task is complete, genuinely blocked, or explicitly stopped.
6. Apply the outcome-specific completion reference, persist the actual result, checkpoint, and report it.
