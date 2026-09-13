# Execute Parallel Execution (Antigravity Edition)

Read this reference completely before evaluating delegation for eligible phases, dispatching subagents, or recovering their work. Add `references/parallel-execution.md` through a normal record transaction and verify the saved Required references before dispatch or related mutation. Keep this reference required while delegated work or its integration/recovery remains active.

## Parallel Phase Scheduling

Treat `Subagent: Eligible` as permission, not a mandate. Build a dependency-ready set from phases whose prerequisites are completed and accepted, then form the safest useful execution wave from that set.

Delegate an eligible phase only when all of these are true:

- The phase has a bounded task, stable inputs, a concrete output contract, and phase-local verification.
- Its write ownership does not overlap another active phase or pre-existing user work that cannot be preserved safely.
- It neither consumes another same-wave phase's output nor mutates a shared contract, migration, lockfile, generated artifact, external resource, persistent test data, stateful process, or similarly coupled resource without an explicit safe coordination strategy.
- A separate subagent and runtime capacity are available, and delegation is likely to improve speed or quality enough to justify coordination.

Use one subagent per eligible phase. The coordinator agent may execute another dependency-ready, non-conflicting phase concurrently within the dedicated worktree. Never hardcode a concurrency count; respect the active runtime's available capacity.

If delegation is unavailable, unsafe, or not worthwhile, execute the eligible phase sequentially and add a concise plan note when the reason matters for handoff. Lack of subagent capacity is not a blocker.

## Coordinator and Subagent Ownership

The main coordinator agent is the sole writer of the execution bundle. Subagents never edit `index.md`, `plan.md`, `verification.md`, `evidence.md`, or phase status metadata.

Assume subagents share the current workspace unless the runtime explicitly guarantees isolation. Enforce one writer per file or mutable touchpoint within a wave.

Before dispatch, mark the phase in progress and give the subagent a bounded task containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required repository instructions and read-before-write context
- The expected output or handoff contract and phase-local checks
- A requirement not to edit the execution record, broaden scope, or run pushes, deployments, destructive commands, broad formatters, or other operations outside its ownership unless separately authorized
- A return contract covering:
  - Branch name or commit SHAs created in the subagent's workspace
  - Summary of files and resources changed
  - Checks run and verification results
  - Assumptions, risks, and blockers

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach.

## Antigravity Subagent Workspace Branch Integration Contract

When dispatching subagents with `Workspace: 'branch'`, Antigravity creates an isolated Git worktree branched from the parent repository. Because this temporary worktree and branch are cleaned up when the subagent lifecycle ends, the coordinator must integrate the subagent's changes into the coordinator's dedicated worktree before accepting the phase or killing the subagent.

Follow this integration sequence for every delegated phase:

1. **Verify Subagent Completion**: Confirm the subagent reported completion with its commit SHAs or branch identifier, list of modified files matching the assigned ownership, and passing phase-local checks.
2. **Inspect Changed Files**: The coordinator reviews the subagent's actual diff and commits to ensure no unassigned files, scope creep, or invariant violations were introduced.
3. **Integrate into Coordinator Dedicated Worktree**:
   - In the coordinator's dedicated worktree, fetch or merge the subagent's branch/commits (e.g. `git merge --no-ff <subagent-branch>` or cherry-pick the verified commit SHAs).
   - If a merge conflict occurs, follow `Failure and Conflict Handling`: inspect the conflict, resolve it cleanly without discarding legitimate changes, or abort the merge, serialize the phase, and execute locally.
4. **Run Integration and Local Verification**:
   - Run the phase-local checks and wave integration checks from `verification.md` inside the coordinator's dedicated worktree against the newly integrated tree.
5. **Commit and Record Evidence**:
   - Record the integrated commit SHA, subagent conversation ID, and verification results in `evidence.md`.
6. **Accept and Update Phase Status**:
   - Only after successful integration and verification, mark the phase item completed `- [x]` in the phase file and `index.md`.
   - The subagent may then be closed or allowed to terminate safely.
