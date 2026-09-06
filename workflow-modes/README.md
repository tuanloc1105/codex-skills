# Workflow Modes

Dormant lifecycle hooks for the standalone `discuss`, `plan`, and `execute` skills. The repository is the source of truth. These hooks do not activate a mode merely because a skill or record is mentioned.

## Lifecycle

- Discuss can exit/pause/cancel, hand off to a separate plan, or make its own bundle execute-ready.
- Discuss never mutates source code. An explicit implementation request uses the direct execute handoff; selecting a behavior option or approving a recommendation is not an implementation request. Authorized non-source actions remain available in discuss.
- Approval keeps plan active. Only an execution request records `Execution authorization: Granted` and permits plan-to-execute transition.
- Execute retains the exact adopted bundle. It supports completion, genuine blockers, and explicit pause/exit with unfinished work preserved.
- In execute, missing actions, stale record/rules revisions, additional file paths and pending record transactions produce non-blocking mutation advisories for direct file work. Stop bookkeeping reminders also advise without retry-blocking or auto-suspending. Lifecycle controls still validate record integrity; advisories do not complete or discard pending work.
- Open record transactions and actions must be reconciled before rebinding or transitioning. Valid no-op record transactions may close without fabricated changes.
- `suspend --record <root> --reason <persistence-failed|user-stop>` retains pending state, permits a blocker/stop response, and denies all non-record mutation. A repeated identical Stop failure also suspends after one retry.
- Repair with the existing write transaction or cached manifest/revision, reconcile actual terminal action evidence, sync record/rules, then `recover --record <root>`. Snapshot output includes the acknowledged revision for recovery.
- `plan-cancel --record <discussion-root>` abandons only pending bootstrap metadata, preserving partial target files for inspection. It does not delete user work.

Run each control request alone with the installed bundle's Python script and `--marker workflow-modes-v1` last. A successful control script process only prints a request; model-visible `WORKFLOW_*` hook context confirms lifecycle handling. `paused` and `cancelled` are valid terminal action results in addition to completed, failed, and blocked.

Read CLI help with `python3 /absolute/path/to/workflow_modes_control.py --help --marker workflow-modes-v1` or replace `--help` with `<subcommand> --help`. `-h` is also supported. Keep the marker last, and run help alone without other arguments or shell commands. These forms are permitted before activation, while active, and while suspended; they do not change workflow state or require an open action. The same script-content and interpreter checks apply as for lifecycle calls.

## Enforcement boundary

This is a workflow guard, not a sandbox or authorization system. The model still owns semantic scope checks and user authority.

- `tool_policy.py` handles known patch/file tool schemas, including raw patch input and move destinations. Exact canonical file paths are compared against action scope.
- Discuss rejects `source-confirmed` actions, declared source-like paths, and `--unscoped shell`/`git`. The mutation gate also blocks source edits and potentially mutating shell/Git calls under legacy actions; those actions can still be reconciled and closed. Prefer direct file tools for authorized non-source edits. External effects and files without recognizable source suffixes still require semantic inspection by the model.
- Known read-only shell forms remain available. Unrecognized commands, scripts, evaluation wrappers, and nonempty process input are treated as potentially mutating. Compound commands require every visible mutation class, including Git commands with global options.
- [Read-only command coverage](references/read-only-commands.md) lists researched command families, supported options, exclusions, and primary sources. Quoted literals and newline-separated read commands are supported. Mixed-use utilities have argument-aware checks; discuss denials identify unrecognized commands/options or unsupported syntax without echoing their arguments.
- In execute, `--unscoped shell`, `git`, and `external` do not restrict arbitrary programs to individual files, repositories, network resources, or read-only effects. Discuss permits only the external class for explicitly authorized non-source effects. Shell configuration, aliases, nested execution, unknown connector schemas, and subprocesses can have effects beyond what lexical inspection establishes.
- A source-confirmed execute action covers shell tooling without a separate `--unscoped shell`. Git/external effects still require their declared classes. Opaque execution without an action remains gated. Explicit non-source actions and user-stop suspension retain hard boundaries; persistence recovery permits record repair, not arbitrary source work. Action path lists are planning metadata in execute, not a machine-verifiable statement of the user's authorization: the model must honor actual task boundaries and obtain authority for destructive operations or broader effects.
- Opaque orchestration/evaluation tools require action scope; prefer direct inspectable tools for read-only planning. Hook integration tests use the documented direct tool payloads. Actual runtime routing/trust and wrapper behavior must also be verified in a fresh installed task.
- Lifecycle calls cannot contain companion shell commands or use an unrelated control script. An identical control script in the marketplace source is accepted when the hook runs from a versioned cache. This prevents the control-call exemption from also exempting an adjacent mutation.
- Control failures distinguish shell/request shape (`WORKFLOW_CONTROL_AMBIGUOUS`), relative paths (`WORKFLOW_CONTROL_PATH_REQUIRED`), missing/unreadable scripts (`WORKFLOW_CONTROL_UNAVAILABLE`), and content/version differences (`WORKFLOW_CONTROL_MISMATCH`). Path failures identify the verified control script beside the running hook when available. Resubmit the same authorized request using that path or an identical installed-source copy; do not repeat a stale cache path, reinstall mid-task, or bypass trust. A rejected request changes no lifecycle state and is never automatically rerouted.
- Version 4 manifests, phase links, IDs, dependencies, cycles, earliest waves, and duplicate legacy table fields are validated. Phase files own scheduling metadata; new plan indexes should contain only ID and Phase file columns. Validation does not prove that tasks, acceptance criteria, or authority are semantically correct.

## Validation and distribution

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s workflow-modes/tests -v
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py workflow-modes
```

Tests use temporary plugin data and workspaces, including installer copies. They do not activate a workflow in the current conversation, modify the personal marketplace, or reinstall the live plugin.

Bundle format remains version 4. New handoffs include execution authorization explicitly; existing records are not automatically rewritten. Reconcile older handoff metadata with actual user authority before transition. An approved plan without an execution request remains in plan mode.

Source-only changes do not update the manifest cachebuster or installed hook cache. The three standalone skill mirrors may therefore describe commands absent from the currently installed plugin; check its help and do not rely on new behavior until the complete compatible plugin is installed. Installation is a separate explicit operation after closing tasks that use the old hook cache. Do not reinstall mid-task or bypass hook trust. See `../docs/agent/plugin-maintenance.md` for the repository distribution rules.
