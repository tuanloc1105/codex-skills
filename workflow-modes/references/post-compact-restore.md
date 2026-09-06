# Post-compact context restoration

Normal action, transaction, sync, rules-sync, and checkpoint bookkeeping stays advisory. A `PostCompact` event for an explicitly active mode opens the only tool-denial gate: restore the current task context before mutations or worker dispatch. Inactive sessions remain dormant. Ordinary prompts do not reopen the gate; a second compaction starts a new recovery epoch.

## Scoped recovery and confirmation

The agent must restore the bound record's `index.md`, Active Snapshot and latest checkpoint first: goal/scope, decisions, user constraints/stops, progress and next safe action. Read the active mode's `SKILL.md` and applicable references, then follow links into record/phase/evidence files needed for that action. Read more before later dependent steps. Unrelated history need not all be loaded before any work can proceed; a missing fact that affects the next step must still be resolved. Complete tracker/plan recording remains mandatory in all modes.

The hook trusts an explicit agent confirmation after this reading. Any permitted read-only tool may deliver context; observed output receipts are supporting evidence, not the sole unlock mechanism. Supporting skills are not automatically activated; honor user exclusions. The hook's optional catalog includes the manifest, mode instructions and recorded references. It locates instructions in bundled, repository sibling or installed standalone skills and freezes that root for the epoch. Catalog validity and missing historical files do not veto an honest scoped confirmation.

Use the installed control script, with its matching Python interpreter, in a standalone shell call:

```text
python3 /absolute/path/workflow_modes_control.py restore-status --marker workflow-modes-v1
python3 /absolute/path/workflow_modes_control.py restore-confirm --record <root> --epoch <epoch> --summary "restored scope, constraints/stops, next step and relevant documents" --marker workflow-modes-v1
```

Use a concrete nonempty summary of at most 2000 characters. Confirmation must match the active record and epoch; stale or malformed confirmation leaves the gate pending. The hook records only the epoch, agent-confirmed basis and summary hash, never raw summary contents. It does not claim to have observed reading, grant authority, resume a user stop, or update the tracker/plan. Save the restored scope, relevant gaps and next step at the next meaningful record checkpoint. This confirmation is performed by the agent and needs no repeated user approval.

## Optional observed delivery

```text
python3 /absolute/path/workflow_modes_control.py restore-read --record <root> --path <next-path> --offset <next-offset> --epoch <epoch> --marker workflow-modes-v1
```

Quote actual shell paths appropriately. Windows may use `py -3`. Request `max_output_tokens` at least 6000. `restore-status` reports the next unobserved catalog document and Unicode character offset. `restore-read` emits one JSON page containing up to 4000 characters. Read the actual text, then request the next page shown by the hook. A nonempty document needs every page; an empty document still needs a successful empty read receipt.

`PostToolUse` requires the original matching standalone read request and a complete successful shell response (`exit_code: 0` and JSON in `output` or `stdout`). MCP `text` and native orchestration `input_text` blocks containing that shell result are supported, including the exact `Script completed`/wall-time/output header followed by one result block and JSON-encoded envelopes. Extra results, failure/running headers, truncated blocks, and bare pages without shell exit status are not credited. The hook compares all returned page fields and text with the current document, checks the epoch and consecutive offsets, and stores only document paths, revision hashes, and offsets. It stores no raw document contents or tool responses.

A pre-tool read request, plain `cat`, `sync`, `rules-sync`, a failed/running/truncated response, an old epoch, a gap in pages, or changed content does not count as completed delivery. Changed files restart at the offset indicated by status. After all current catalog files have been delivered and the manifest, tracker identity, and reference set remain valid, the hook reports `WORKFLOW_CONTEXT_RESTORED` and removes the gate. Existing pending actions/transactions/evidence remain unchanged. Later edits use normal advisory behavior until another compaction.

This verifies delivery into observed tool output, not understanding, semantic completeness of the record, or user authority. The agent must restore decisions and constraints before making context-dependent conclusions. The hook cannot inspect internal reasoning or reliably distinguish a blocker report from an unsupported final conclusion, so `Stop` is always nonblocking.

## Recovery remains possible

During the gate, known read-only shell forms, direct read/search tools, user questions, owned-process interruption/polling, and direct Markdown edits inside the exact record remain available. Record repair does not require an open transaction. Do not invent missing facts or mutate source as a recovery shortcut. External mutations, source edits, unknown tools, opaque execution, and worker dispatch wait for restoration.

One literal orchestration call is recognized when direct tools are unavailable:

```javascript
text(await tools.exec_command({"cmd":"python3 /absolute/path/workflow_modes_control.py restore-status --marker workflow-modes-v1","max_output_tokens":6000}));
```

Only literal JSON arguments and a single `text(await tools.exec_command(...));` or `text(await tools.apply_patch(...));` call are recognized; the hook never evaluates JavaScript. The shell call must itself be read-only or a valid lifecycle request. Record patch scope is checked after unwrapping. Extra statements, evaluations, or commands remain gated.

Lifecycle state cannot be rebound or deactivated merely to erase the pending read gate. This never forces task completion: report an explicit stop or missing/invalid/unreadable context immediately if needed. A stopped task stays stopped after successful context delivery. `sync`, `rules-sync`, recovery, and checkpoint calls do not substitute for restoration confirmation or observed catalog delivery. Repeated Stop events preserve pending restoration and do not force another work turn.

## Runtime compatibility

Install the complete compatible plugin only when explicitly requested, after closing tasks using the old versioned cache. Source tests do not prove the installed runtime's response routing. If `PostToolUse` is absent or cannot decode the output, do not loop on the same failure. Read the necessary context through another permitted reader and use `restore-confirm`; never fabricate an observation receipt. If necessary context itself remains missing, resolve it or report the affected blocker rather than falsely confirming. A missing unrelated historical file does not prevent the next independent step, but record the gap for later repair. Without the optional plugin the same scoped manual recovery remains mandatory. Older installed versions may lack `restore-confirm`; inspect installed help, use supported recovery and report compatibility limitations without deleting hook state, changing trust, or routing a denied mutation through Python. Source-only changes do not update active cached sessions.
