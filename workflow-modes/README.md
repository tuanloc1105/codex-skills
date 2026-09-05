# Workflow Modes

Dormant lifecycle hooks for the standalone `discuss`, `plan`, and `execute` skills. The repository is the source of truth. These hooks do not activate a mode merely because a skill or record is mentioned.

## Lifecycle

- Discuss can exit/pause/cancel, hand off to a separate plan, or make its own bundle execute-ready.
- Approval keeps plan active. Only an execution request records `Execution authorization: Granted` and permits plan-to-execute transition.
- Execute retains the exact adopted bundle. It supports completion, genuine blockers, and explicit pause/exit with unfinished work preserved.
- Open record transactions and actions must be reconciled before rebinding or transitioning. Valid no-op record transactions may close without fabricated changes.
- `suspend --record <root> --reason <persistence-failed|user-stop>` retains pending state, permits a blocker/stop response, and denies all non-record mutation. A repeated identical Stop failure also suspends after one retry.
- Repair with the existing write transaction or cached manifest/revision, reconcile actual terminal action evidence, sync record/rules, then `recover --record <root>`. Snapshot output includes the acknowledged revision for recovery.
- `plan-cancel --record <discussion-root>` abandons only pending bootstrap metadata, preserving partial target files for inspection. It does not delete user work.

Run each control request alone with the installed bundle's Python script and `--marker workflow-modes-v1` last. A successful control script process only prints a request; model-visible `WORKFLOW_*` hook context confirms lifecycle handling. `paused` and `cancelled` are valid terminal action results in addition to completed, failed, and blocked.

## Enforcement boundary

This is a workflow guard, not a sandbox or authorization system. The model still owns semantic scope checks and user authority.

- `tool_policy.py` handles known patch/file tool schemas, including raw patch input and move destinations. Exact canonical file paths are compared against action scope.
- Known read-only shell forms remain available. Unrecognized commands, scripts, evaluation wrappers, and nonempty process input are treated as potentially mutating. Compound commands require every visible mutation class, including Git commands with global options.
- `--unscoped shell`, `git`, and `external` do not restrict arbitrary programs to individual files, repositories, network resources, or read-only effects. Shell configuration, aliases, nested execution, unknown connector schemas, and subprocesses can have effects beyond what lexical inspection establishes.
- Opaque orchestration/evaluation tools require action scope; prefer direct inspectable tools for read-only planning. Hook integration tests use the documented direct tool payloads. Actual runtime routing/trust and wrapper behavior must also be verified in a fresh installed task.
- Lifecycle calls cannot contain companion shell commands or use an unrelated control script. An identical control script in the marketplace source is accepted when the hook runs from a versioned cache. This prevents the control-call exemption from also exempting an adjacent mutation.
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
