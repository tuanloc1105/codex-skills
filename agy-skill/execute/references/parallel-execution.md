# Execute Parallel Execution (Antigravity Edition)

Read this reference completely before evaluating delegation for eligible phases, dispatching subagents, or recovering their work. Add `references/parallel-execution.md` through a normal record transaction and verify the saved Required references before dispatch or related mutation.

## Parallel Phase Scheduling

Treat `Subagent: Eligible` as permission, not a mandate. Build a dependency-ready set from phases whose prerequisites are completed and accepted, then form the safest useful execution wave from that set.

Delegate an eligible phase only when all of these are true:

- The phase has a bounded task, stable inputs, a concrete output contract, and phase-local verification.
- Its write ownership does not overlap another active phase or pre-existing user work that cannot be preserved safely.
- It neither consumes another same-wave phase's output nor mutates a shared contract, migration, lockfile, generated artifact, external resource, persistent test data, stateful process, or similarly coupled resource without an explicit safe coordination strategy.
- A separate subagent and runtime capacity are available, and delegation is likely to improve speed or quality enough to justify coordination.

## Antigravity Subagent Dispatch

Use Antigravity's native `invoke_subagent` tool to dispatch subagents:

- **Subagent Type**: Use `TypeName: 'self'` when subagents need file modification and execution tools, or `'research'` when only read-only exploration and inspection are needed.
- **Model**: Default to `inherit` (or `flash` for fast targeted lookups, `pro` for complex refactors).
- **Workspace Isolation**:
  - Set `Workspace: 'branch'` to create an isolated workspace branched or cloned from the parent. This maps directly to dedicated worktrees and guarantees isolation.
  - Set `Workspace: 'share'` when sharing the parent repository directory safely without duplicate storage.
- **Role**: Provide a concise 2-5 word description (e.g. `'Phase P01 Implementer'`).
- **Reactive Wakeup**: Do **NOT** poll or loop on task status. The Antigravity system automatically notifies the coordinator agent when subagents complete or send messages.

## Coordinator and Subagent Ownership

The main coordinator agent is the sole writer of the execution bundle. Subagents never edit `index.md`, `plan.md`, `verification.md`, `evidence.md`, or phase status metadata.

Before dispatch, mark the phase in progress and give the subagent a bounded prompt containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required repository instructions and read-before-write context
- The expected output contract and phase-local checks
- A requirement not to edit the execution record, broaden scope, or run commits, pushes, deployments, or destructive commands outside its ownership
- A return contract covering summary, files or resources changed, checks and results, assumptions, risks, and blockers

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach. Review its reported output and actual changes before accepting the phase; never treat a successful agent status as sufficient verification.
