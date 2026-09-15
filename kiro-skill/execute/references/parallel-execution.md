# Execute Parallel Execution

Read this reference completely before evaluating delegation for eligible phases, dispatching `spawn_run` subagents, or recovering their work. Add `references/parallel-execution.md` through a normal record transaction and verify the saved Required references before dispatch or related mutation. Keep this reference required while delegated work or its integration/recovery remains active.

## Parallel Phase Scheduling

Treat `Subagent: Eligible` as permission, not a mandate. Build a dependency-ready set from phases whose prerequisites are completed and accepted, then form the safest useful execution wave from that set.

Delegate an eligible phase only when all of these are true:

- The phase has a bounded task, stable inputs, a concrete output contract, and phase-local verification.
- Its write ownership does not overlap another active phase or pre-existing user work that cannot be preserved safely.
- It neither consumes another same-wave phase's output nor mutates a shared contract, migration, lockfile, generated artifact, external resource, persistent test data, stateful process, or similarly coupled resource without an explicit safe coordination strategy.
- Delegation is likely to improve speed or quality enough to justify coordination, and `resource_status` (checked before a wide wave) does not report a `tight`/`critical` posture that would make serial execution safer.

Use one `spawn_run` task per eligible phase, passed together with any other ready phase in the **same batch call** (Kiro Crew queues and drains overflow automatically beyond the concurrency cap — never split a ready wave into multiple manual `spawn_run` rounds). The main agent (this session) may execute another dependency-ready, non-conflicting phase concurrently while subagents run. After calling `spawn_run`, **end the turn** and wait for `[Subagent completion event]` messages — do not duplicate a dispatched phase's work by doing it yourself in the same turn.

If delegation is unavailable, unsafe, or not worthwhile, execute the eligible phase sequentially and add a concise plan note when the reason matters for handoff. Lack of subagent capacity (a `spawn_run` refusal as memory back-pressure) is not a blocker — it is a decision to take the lighter, serial path.

## Coordinator and Subagent Ownership

The main agent (this session) is the sole writer of the execution bundle. Subagents spawned via `spawn_run` never edit `index.md`, `plan.md`, `verification.md`, `evidence.md`, or phase status metadata — they are not given those paths or that authority in their task text.

Assume subagents share the current workspace/checkout unless explicitly isolated (e.g. a dedicated worktree passed as `cwd`). Enforce one writer per file or mutable touchpoint within a wave.

Before dispatch, mark the phase in progress and give the subagent a bounded task (the `task` string in `spawn_run`) containing:

- The exact phase ID, goal, satisfied dependencies, and authoritative inputs
- Allowed files, modules, services, or mutable resources, plus explicit exclusions
- Required project steering and read-before-write context (or `include_project=true`, the default, if the subagent should discover this itself)
- The expected output or handoff contract and phase-local checks
- A requirement not to edit the execution record, broaden scope, or run commits, pushes, deployments, destructive commands, broad formatters, or other operations outside its ownership unless separately authorized
- A return contract covering summary, files or resources changed, checks and results, assumptions, risks, and blockers

Set `include_lessons=true` for any phase that writes code, edits files, or runs git (the default) — that is where the user's learned corrections live. Set `include_memory=false` when the phase's task text is fully self-contained, which is the norm for fan-out over a plan you already wrote.

Require a subagent to stop and report before touching an unassigned or overlapping resource or materially changing the approved approach — put this instruction directly in the task text, since a subagent cannot be steered mid-run unless you use `spawn_steer`. Review its reported output and actual changed files/diff before accepting the phase; never treat a successful agent completion event as sufficient verification on its own.

If a dispatched phase looks like it is heading the wrong direction while still running, use `spawn_steer` to correct it in place rather than waiting for it to finish and then re-dispatching. If a finished phase's subagent conversation needs a follow-up question about the same work (not a new mutation), use `spawn_continue` instead of spawning a fresh one.
