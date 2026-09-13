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

Assume subagents share the current workspace unless the runtime explicitly guarantees isolation. Enforce one writer per file or mutable touchpoint within a wave. Mutating delegated Git phases must always use `Workspace: 'branch'`; `Workspace: 'share'` is reserved strictly for read-only delegation.

Before dispatch, mark the phase in progress and give the subagent a bounded task containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required repository instructions and read-before-write context
- The expected output or handoff contract and phase-local checks
- A requirement not to edit the execution record, broaden scope, or run pushes, deployments, destructive commands, broad formatters, or other operations outside its ownership unless separately authorized
- A lossless return contract:
  - Before returning, the subagent MUST commit all owned changes with a clear commit message and return the exact commit SHA(s) created in its workspace.
  - Alternatively, if committing cannot be completed, the subagent must provide a verified patch-transfer fallback while the subagent is still alive (generate the patch, provide exact patch content or file path, and wait until the coordinator verifies and applies it).
  - Never accept a branch-name-only handoff when the worktree is dirty or contains uncommitted changes. Uncommitted changes in an ephemeral workspace branch will be destroyed upon subagent termination.
  - Summary of files and resources changed matching assigned ownership
  - Checks run and verification results
  - Assumptions, risks, and blockers

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach. Review its reported output and actual changes before accepting the phase; never treat a successful agent status as sufficient verification.

## Antigravity Subagent Workspace Branch Integration Contract

When dispatching subagents with `Workspace: 'branch'`, Antigravity creates an isolated Git worktree branched from the parent repository. Because this temporary worktree and branch are cleaned up when the subagent lifecycle ends, the coordinator must integrate the subagent's changes into the coordinator's dedicated worktree before accepting the phase or killing the subagent.

Follow this lossless integration sequence for every delegated phase:

1. **Verify Subagent Completion and Lossless Return**:
   - Confirm the subagent reported completion with its exact commit SHAs (or verified live patch fallback) and clean worktree status, list of modified files matching the assigned ownership, and passing phase-local checks.
   - Strictly reject any handoff that only provides a branch name with dirty or uncommitted changes. If the subagent returned with uncommitted changes, do not terminate or kill the subagent; instruct it while still alive to commit all owned changes and return the exact commit SHA(s), or generate and verify a patch before proceeding.
2. **Inspect Changed Files and Commits**:
   - The coordinator reviews the subagent's actual diff and commits (or verified patch) to ensure no unassigned files, scope creep, or invariant violations were introduced.
3. **Fetch and Integrate into Coordinator Dedicated Worktree**:
   - In the coordinator's dedicated worktree, fetch the subagent's branch or commits into the local repository if needed (`git fetch <subagent-workspace-path> <subagent-branch>` or local ref). Fetching is strictly a preparation step to ensure commits exist in the object database; fetching is NOT integration.
   - The coordinator then integrates the changes into the dedicated worktree using one of these explicit methods:
     - **Merge**: `git merge --no-ff <commit-SHA-or-branch>`
     - **Cherry-pick**: `git cherry-pick <commit-SHAs>`
     - **Patch**: verify with `git apply --check <patch-file>`, apply with `git apply <patch-file>`, run focused verification, and create a coordinator commit for the applied patch.
   - If a merge conflict occurs, follow `Failure and Conflict Handling`: inspect the conflict, resolve it cleanly without discarding legitimate changes, or abort the merge, serialize the phase, and execute locally.
4. **Method-Specific Integration Verification and HEAD Inclusion**:
   Verify integration according to the exact method used. Never rely on tree cleanliness or a clean worktree as proof of content equivalence:
   - **Merge**:
     - Verify that every original accepted subagent commit SHA is actually an ancestor of coordinator HEAD (`git merge-base --is-ancestor <subagent-commit-SHA> HEAD`).
   - **Cherry-pick**:
     - Because cherry-pick creates new commit SHAs in the coordinator's history, do not require the original subagent SHA to be an ancestor of HEAD.
     - Verify content equivalence by comparing the stable patch IDs of each original subagent commit and its mapped coordinator commit: compute `git show --pretty=format: <sha> | git patch-id --stable` for each commit and verify the patch ID hashes match. When integrating multiple commits, verify each mapping in consecutive order.
     - Record the mapping `original subagent SHA -> new coordinator SHA` along with their verified stable patch IDs in `evidence.md`.
     - Verify that each new coordinator commit SHA is an ancestor of coordinator HEAD (`git merge-base --is-ancestor <new-coordinator-SHA> HEAD`).
     - Never use tree cleanliness or tree snapshot comparison as proof of equivalence between different parent trees.
   - **Patch Fallback**:
     - Verify `git apply --check <patch-file>` passed prior to applying.
     - Apply the verified patch (`git apply <patch-file>`).
     - Run focused verification on the applied changes.
     - The coordinator commits the applied changes in the dedicated worktree.
     - Record the patch digest/source and the resulting coordinator commit SHA in `evidence.md`.
     - Verify that the resulting commit/tree contains the intended scoped diff (comparing `git show <coordinator-commit-SHA>` or commit diff against the patch content) and that the coordinator commit is an ancestor of coordinator HEAD (`git merge-base --is-ancestor <coordinator-commit-SHA> HEAD`).
     - Never use tree cleanliness alone as proof of patch equivalence.
5. **Run Integration and Local Verification**:
   - Run the phase-local checks and wave integration checks from `verification.md` inside the coordinator's dedicated worktree against the newly integrated tree.
6. **Commit and Record Evidence**:
   - Record the integration method used (`merge`, `cherry-pick`, or `patch`), subagent conversation ID, subagent commit SHA(s) or patch digest, mapping to coordinator commit SHA(s) and stable patch IDs (for cherry-pick), coordinator commit SHA and patch digest (for patch), and verification results in `evidence.md`.
7. **Accept and Update Phase Status**:
   - Only after successful integration, method-specific verification of content equivalence and HEAD inclusion, and passing verification checks, mark the phase item completed `- [x]` in the phase file and `index.md`.
   - Only after this verification step may the subagent conversation be closed or allowed to terminate safely.
