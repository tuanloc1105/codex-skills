---
name: handoff-execute
description: Coordinate execution of an approved version 4 $plan bundle or execution-ready $discuss tracker by launching a separate lower-cost Codex CLI session, then reconcile its work, run $simplify in the current session, and complete verification. Use when the user explicitly requests $handoff-execute or asks to hand off an accepted execution record to another Codex CLI session. Never use subagents for this workflow.
---

# Handoff Execute

Act as the controlling parent session. Evaluate the accepted execution record, launch one independent Codex CLI worker only when the handoff is safe, wait for it to finish its complete `$execute` quality gates, inspect its actual work, then retain ownership for an independent second simplification pass and final verification. Launch the worker with `codex exec`; never use `spawn_agent`, another subagent facility, or `$handoff-execute` inside the worker.

This skill is a coordinator in front of `$execute`, not a replacement execution record. Adopt the exact version 4 bundle produced by an approved `$plan` or a `$discuss` tracker that passed `Direct Execute Handoff`. Never copy it, create a second plan, or infer the newest bundle. Require its path or reuse the exact already-active canonical root and tracker ID.

## Required Skills and References

Read `$execute` completely, including each reference it requires for the current stage. Read `$simplify` and all of its runtime references before the post-worker simplify pass.

Before evaluating or launching a handoff, read:

- [preflight.md](references/preflight.md) for eligibility and result classification.
- [handoff-contract.md](references/handoff-contract.md) for worker ownership, launch, monitoring, and receipt rules.

Read [recovery.md](references/recovery.md) before recovering an interrupted, failed, missing, or uncertain worker run.

## Persistent Lifecycle

Bind the current session to the exact canonical bundle root and tracker ID. On entry, resume, or after compaction, recover those identifiers from durable state and validate the complete bundle before any substantive tool call. If they cannot be recovered, ask for the path and stop; never choose a bundle by recency.

Keep `$execute`'s record transaction, evidence, authorization, worktree, commit, completion, and explicit-exit contracts in force. `handoff-execute` changes who performs the implementation interval, not what execution is authorized or how completion is proven. Record the handoff preflight, launch configuration, runtime directory, worker process/session information available from the CLI, result, reconciliation, both simplify passes, and final verification in the adopted bundle.

Only one session may write source files or the execution bundle at a time:

1. The parent owns both before launch and records an open handoff action.
2. Ownership transfers to the worker for the bounded execution interval after the saved handoff state is verified.
3. The parent remains read-only and does not run parallel implementation, record updates, or subagents while the worker is active.
4. Ownership returns to the parent only after the process terminates or recovery establishes that it is no longer writing.
5. The parent reconciles the complete bundle and repository state before any mutation.

Do not interpret approval alone as implementation authorization. The current request must explicitly authorize execution, as required by `$execute`. Handoff never grants push, deploy, merge, destructive operations, external mutation, or history rewriting that the user and record did not authorize.

## Workflow

1. Capture the user's initial terminal directory, resolve and validate the exact bundle through `$execute` intake, and establish or safely reuse every required dedicated worktree under the recorded anchor.
2. Run the mandatory preflight. Classify the result as `READY`, `READY_WITH_CONSTRAINTS`, or `NOT_READY`; do not launch for `NOT_READY`.
3. Resolve worker settings from explicit invocation overrides first, otherwise [worker.toml](config/worker.toml). Validate the model and reasoning level against `codex debug models`. Never silently substitute another model or reasoning level.
4. Persist and verify the handoff action and ownership transfer. Store runtime files outside the repository, worktree, and execution bundle, and record their exact paths for recovery.
5. Invoke [launch_worker.py](scripts/launch_worker.py) with the canonical bundle root, tracker ID, dedicated worktree, runtime directory, and any verified constraints. The script must launch `codex exec`, pass the prompt through stdin, and return the worker's exit code. Do not use interactive `codex`, `codex -p` as a prompt flag, or shell-built prompt interpolation.
6. Wait on the actual CLI process. Allow the command to yield and poll its process handle rather than using blind sleep loops. Give the user concise progress updates during long runs.
7. Require the worker to complete `$execute`'s own implementation, verification, `$simplify`, simplify-fix commit, and post-simplify verification gates before handoff. Its receipt must describe that quality pass and any residual risk accurately.
8. After termination, reclaim ownership and reconcile the receipt, complete bundle, Git state, declared scope, commits, checks, and working-tree changes. A zero exit code or `implemented` receipt is evidence, never proof of completion.
9. Invoke `$simplify` again in the parent as an independent acceptance pass on the full `$execute` session scope: starting `HEAD` exclusive through current `HEAD` inclusive, including the worker's implementation and simplify commits plus remaining in-scope staged, unstaged, and untracked changes.
10. Apply only verified improvements from the parent's second pass directly in the parent session, run focused checks, commit those fixes separately when commits are authorized, and record them. Do not prompt or resume the worker for normal simplify fixes.
11. Complete every `$execute` completion gate and persist the final checkpoint. Implementation completion does not exit execute mode.

## Failure Boundary

Do not automatically relaunch a failed or uncertain worker. Follow [recovery.md](references/recovery.md), preserve partial work, and determine whether the existing session can be resumed safely. A CLI failure is not automatically a genuine blocker, but concurrent or uncertain writers must be resolved before further mutation.

If preflight returns `NOT_READY`, report the concrete deficiencies and do not silently execute with the parent model. The user invoked handoff specifically; switching execution modes requires their direction.
