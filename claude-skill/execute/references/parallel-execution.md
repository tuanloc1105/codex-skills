# Execute Parallel Execution

Read this reference completely before evaluating delegation for eligible phases, dispatching subagents, or recovering their work. Add `references/parallel-execution.md` through a normal record transaction and verify the saved Required references before dispatch or related mutation. Keep this reference required while delegated work or its integration/recovery remains active.

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
