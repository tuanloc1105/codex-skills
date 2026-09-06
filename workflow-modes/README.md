# Workflow Modes

Dormant lifecycle hooks for the standalone `discuss`, `plan`, and `execute` skills. The repository is the source of truth. These hooks do not activate a mode merely because a skill or record is mentioned.

## Mode reminders and required records

Normal workflow bookkeeping is advisory. The sole tool-denial exception is a pending post-compact context confirmation gate; the hook never emits `allow`/`ask` decisions or Stop blocks. It supplies context; actual user instructions and runtime permissions still govern actions.

- Discuss focuses on analysis and decisions, reminding the agent to avoid source changes without an implementation request. Authorized non-source work does not need a hook action grant.
- Plan focuses on creating and updating the plan. Approval alone does not request implementation.
- Execute carries out the delegated task, verification, and requested delivery. Additional files, tool classes, or stale action metadata do not require new permission.
- All three standalone skills require complete tracker/plan content: material requirements, decisions and rationale, evidence, plan/progress changes, verification, unresolved work, and next steps. Save at meaningful checkpoints and reconcile before a final response or handoff. Optional hook acknowledgments never make record content optional or prove semantic completeness.
- Failed persistence requires repair and an honest report of the last durable checkpoint and unsaved facts. Pending work stays pending. Independent in-scope work may continue while its prerequisites are known.
- An actual user stop remains binding on the agent. `suspend --reason user-stop` preserves that instruction as a reminder, without denying tools; `persistence-failed` cannot replace an existing user stop. Resume task work only when the user resumes it.

## Events

- `UserPromptSubmit`: restore mode/record context and remind the agent to save all material turn changes. A mention alone never activates a mode.
- `PreToolUse`: while post-compact restoration is pending, permit reads/questions/record repair and deny task mutations or worker dispatch. Otherwise remind on likely source/implementation drift or outstanding bookkeeping. Outside restoration, classifications focus reminders rather than access control. Suppress repeated identical reminders within a turn using a bounded cache, refreshed on the next prompt or compaction.
- `PostCompact`: open a one-time context confirmation gate. Restore the checkpoint, scope, decisions/stops, next step, active mode instructions and relevant linked context using any permitted reader; load other history as needed. Do not activate excluded supporting skills.
- `PostToolUse`: credit complete successful `restore-read` pages only after comparing returned content and file revision. Complete valid catalog delivery can clear the gate automatically. Alternatively, `restore-confirm --record <root> --epoch <epoch> --summary "restored context and next step" --marker workflow-modes-v1` accepts agent attestation after scoped reading, without requiring output receipts or every historical file. `sync`/`rules-sync` cannot clear it.
- `Stop`: remind about pending evidence, writes, actions, bootstrap, and context restoration. Do not block, auto-suspend, clear pending state, or mark work complete, even after repeated Stop events.
- `SessionEnd`: discard the session's hook metadata; durable Markdown records remain on disk.

See [post-compact restoration](references/post-compact-restore.md) for the bounded reader, output verification, permitted recovery tools, and integration limitations.

## Lifecycle metadata

The optional control CLI tracks activation, handoffs, revisions, transactions, actions, checkpoints, and recovery. The version 4 bundle remains the source of truth for recorded progress. Discuss-to-plan creates a separate linked bundle; direct discuss-to-execute and plan-to-execute retain the exact execution record. Handoffs require actual user execution intent, not a selected behavior option or a successful hook call.

Run each control request alone with the installed bundle's Python script and `--marker workflow-modes-v1` last. Lifecycle CLI processes print requests; model-visible `WORKFLOW_*` context confirms the hook applied them. `restore-read` instead prints the requested document page, which is credited only after observation. `paused` and `cancelled` preserve unfinished actions. `plan-cancel` preserves partial target files instead of deleting them.

Well-formed controls that fail lifecycle validation return `WORKFLOW_CONTROL_NOT_APPLIED`, without acknowledging the requested change or denying the tool. Ambiguous or unverifiable executable calls remain gated during restoration. Record identity, safe manifest paths, phase consistency, and lifecycle transitions still undergo validation. An invalid call cannot fabricate completion, discard pending actions, or replace the bound record. Continue maintaining the complete bundle directly when integration is unavailable; reconcile hook metadata when possible.

Read help using `python3 /absolute/path/to/workflow_modes_control.py --help --marker workflow-modes-v1`, or `<subcommand> --help` before the marker. Help leaves state unchanged. Controls require supported interpreter/request shape and matching script contents. Ambiguous shell commands or stale/mismatched scripts are not acknowledged. During post-compact restoration they are denied because their effects cannot be verified; otherwise the advisory hook does not prevent their execution. It never supplies a tool permission exemption.

## Classification and validation limits

`tool_policy.py` inspects known file/patch schemas (including move destinations), read-only command forms, and opaque wrappers. Source suffixes and shell classifications are hints; the agent must inspect actual effects. A source-like file may be a document, and source can have an unrecognized suffix. See [read-only command coverage](references/read-only-commands.md) for the classifier's supported forms and limitations.

Unknown commands/options are described without echoing their arguments. Outside post-compact restoration, files outside action paths, external effects, shell/Git operations, and wrapper calls are not blocked. The hook cannot prove arbitrary programs' scope or side effects, semantic user authority, or complete record content.

Version 4 manifests, phase links, IDs, dependencies, cycles, earliest waves, and duplicate legacy table fields are validated for lifecycle acknowledgments. Phase files own scheduling metadata; new plan indexes use only ID and Phase file columns. Rejected validation does not grant permission to omit required record content or claim success.

## Validation and distribution

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s workflow-modes/tests -v
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py workflow-modes
```

Tests use temporary plugin data and workspaces, including installer copies. They do not activate a workflow in the current conversation, modify the personal marketplace, or reinstall the live plugin.

Bundle format remains version 4. New handoffs include execution authorization explicitly; existing records are not automatically rewritten. Reconcile older handoff metadata with actual user authority before transition. An approved plan without an execution request remains in plan mode.

Source-only changes do not update the manifest cachebuster or installed hook cache. The three standalone skill mirrors may therefore describe commands absent from the currently installed plugin; check its help and do not rely on new behavior until the complete compatible plugin is installed. Installation is a separate explicit operation after closing tasks that use the old hook cache. Do not reinstall mid-task or bypass hook trust. See `../docs/agent/plugin-maintenance.md` for the repository distribution rules.

## Compatibility

This revision keeps all three modes advisory except for mandatory scoped context restoration after compaction. Existing state and version 4 bundles remain readable; pending actions, transactions, and suspension facts are preserved for reconciliation. Older installed hooks may still deny calls: do not bypass an actual denial or reinstall during an active task. Use supported recovery and report the compatibility limitation.

Distribute the compatible plugin separately when explicitly requested. Source validation does not change an active task's cached hooks. Standalone skill mirrors keep mandatory record completeness even when the new hook is not installed.
