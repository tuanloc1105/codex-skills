# Post-compact context restoration

Normal action, transaction, sync, rules-sync, and checkpoint bookkeeping stays advisory. A `PostCompact` event for an explicitly active mode opens the only tool-denial gate: restore the current task context before mutations or worker dispatch. Inactive sessions remain dormant. Ordinary prompts do not reopen the gate; a second compaction starts a new read epoch.

## Required context and delivery

The required set consists of the bound record's `index.md` and every manifest file, the active mode's `SKILL.md`, and its applicable Required references (always including the discuss tracker or plan-record reference in those modes). The hook locates mode instructions in bundled skills, repository sibling skills, or installed standalone skills, then freezes that skill root for the recovery epoch. Supporting skills are not automatically added or activated; the agent reassesses their relevance and honors user exclusions.

Use the installed control script, with its matching Python interpreter, in a standalone shell call:

```text
python3 /absolute/path/workflow_modes_control.py restore-status --marker workflow-modes-v1
python3 /absolute/path/workflow_modes_control.py restore-read --record <root> --path <next-path> --offset <next-offset> --epoch <epoch> --marker workflow-modes-v1
```

Quote actual shell paths appropriately. Windows may use `py -3`. Request `max_output_tokens` at least 6000. `restore-status` reports the next document and Unicode character offset. `restore-read` emits one JSON page containing up to 4000 characters. Read the actual text, then request the next page shown by the hook. A nonempty document needs every page; an empty document still needs a successful empty read receipt.

`PostToolUse` requires the original matching standalone read request and a complete successful shell response (`exit_code: 0` and JSON in `output` or `stdout`). A single MCP text wrapper containing that shell result is supported, as are JSON-encoded result envelopes. The hook compares all returned page fields and text with the current document, checks the epoch and consecutive offsets, and stores only document paths, revision hashes, and offsets. It stores no raw document contents or tool responses.

A pre-tool read request, plain `cat`, `sync`, `rules-sync`, a failed/running/truncated response, an old epoch, a gap in pages, or changed content does not count as completed delivery. Changed files restart at the offset indicated by status. After all current required files have been delivered and the manifest, tracker identity, and reference set remain valid, the hook reports `WORKFLOW_CONTEXT_RESTORED` and removes the gate. Existing pending actions/transactions/evidence remain unchanged. Later edits use normal advisory behavior until another compaction.

This verifies delivery into observed tool output, not understanding, semantic completeness of the record, or user authority. The agent must restore decisions and constraints before making context-dependent conclusions. The hook cannot inspect internal reasoning or reliably distinguish a blocker report from an unsupported final conclusion, so `Stop` is always nonblocking.

## Recovery remains possible

During the gate, known read-only shell forms, direct read/search tools, user questions, owned-process interruption/polling, and direct Markdown edits inside the exact record remain available. Record repair does not require an open transaction. Do not invent missing facts or mutate source as a recovery shortcut. External mutations, source edits, unknown tools, opaque execution, and worker dispatch wait for restoration.

One literal orchestration call is recognized when direct tools are unavailable:

```javascript
text(await tools.exec_command({"cmd":"python3 /absolute/path/workflow_modes_control.py restore-status --marker workflow-modes-v1","max_output_tokens":6000}));
```

Only literal JSON arguments and a single `text(await tools.exec_command(...));` or `text(await tools.apply_patch(...));` call are recognized; the hook never evaluates JavaScript. The shell call must itself be read-only or a valid lifecycle request. Record patch scope is checked after unwrapping. Extra statements, evaluations, or commands remain gated.

Lifecycle state cannot be rebound or deactivated merely to erase the pending read gate. This never forces task completion: report an explicit stop or missing/invalid/unreadable context immediately if needed. A stopped task stays stopped after successful context delivery. `sync`, `rules-sync`, recovery, and checkpoint calls do not substitute for delivery receipts. Repeated Stop events preserve pending restoration and do not force another work turn.

## Runtime compatibility

Install the complete compatible plugin only when explicitly requested, after closing tasks using the old versioned cache. Source tests do not prove the installed runtime's response routing. If `PostToolUse` is absent, shell output is wrapped in an unsupported shape, or a required file is missing, the gate remains pending; report the exact integration/context issue instead of claiming restoration or bypassing trust. The standalone skills require full manual context recovery even when this optional plugin is absent.
