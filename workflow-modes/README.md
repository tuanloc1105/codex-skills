# Workflow Modes diagnostics and recovery

Workflow Modes distinguishes workflow denials from infrastructure failures. A
workflow denial keeps its `WORKFLOW_*` code and names the record, cause and next
step. Follow its public control command and confirm the expected hook response;
reading or editing the hook implementation is not a recovery step.

## Inspect without changing state

Run with the Python interpreter and control path supplied by the hook:

```text
python3 /installed/plugin/scripts/workflow_modes_control.py diagnose --record /path/to/bundle --json
python3 /installed/plugin/scripts/workflow_modes_control.py snapshot --marker workflow-modes-v1
```

`diagnose` works outside a hooked session, reads the bundle only, and never opens
SQLite. Exit 0 means valid, 1 means a diagnosed bundle problem, and 2 means the
control/diagnostic runtime failed. Its report includes the first validation
failure and a raw `observed_revision`; repeat after fixing that failure to expose
any remaining problems. It does not sync or authorize the record.

`snapshot` gets its state from PreToolUse. The hook confirmation includes the
acknowledged/current revisions, required references, write transaction and its
allowed paths, action/evidence ID, checkpoint status and baseline metadata. The
control CLI's own “request sent” output is not proof that a hook ran.

Run lifecycle calls individually, with literal arguments and no pipelines,
redirection, shell expansion or command chaining. The marker can appear anywhere
after the action. `--help` does not change state. On Windows, generated recovery
commands use PowerShell's `&` call operator and single-quoted arguments; hook
registration itself uses the CMD launcher.

## Repair a record

- A normal write is opened against the acknowledged revision. Close it only when
  the bundle is valid. A valid unchanged bundle closes with `changed=false`;
  cancellation or exact rollback does not need an artificial edit.
- If Required references is invalid, repair that field in `index.md`. Changing
  `rules-sync --reference` arguments alone cannot fix the record. Close the write,
  read the selected references and then run `rules-sync`.
- If a bundle becomes invalid outside a write, use the `write-open --recover`
  command supplied by its denial. It contains the acknowledged baseline and the
  observed damaged revision; the hook rechecks both inside its state transaction.
- Recovery updates or restores only acknowledged Markdown paths through
  `apply_patch`. Keep the exact baseline manifest and tracker identity. It cannot
  delete/rename files, add phases, adopt another record, follow symlinks or clear
  an existing action. Run `write-close`, then reconcile actions and checkpoint as
  required by the workflow.
- If another process changes the bundle after diagnosis, obtain a fresh snapshot
  and diagnosis. Missing baseline metadata, missing/changed identity, unsafe paths
  or unacknowledged Markdown require the owner to restore/reconcile the bundle.
  Do not delete another session's files or reset the database.

Existing sessions acquire baseline metadata on their next valid sync or closed
write. Only the manifest, hashes, identity and resolved root are saved, not record
contents. An already-damaged legacy session without this metadata cannot recover
automatically.

## Infrastructure failures

The launcher/supervisor handles missing interpreter, runtime files/imports,
malformed input/output, state-access errors and timeouts. Failed PreToolUse
returns exit 2 with actionable stderr. Infrastructure failure at Stop permits
stopping so the assistant can report a blocker. Normal workflow Stop denials
still require completion of bookkeeping; they are not treated as infrastructure
errors.

The hook watchdog is 3 seconds inside a 5-second host timeout; SessionEnd uses
1 second inside the host's 3-second budget. A timeout can happen after a state
update committed. After restoring enforcement, inspect snapshot before retrying
a lifecycle request. There is no automatic retry, reinstall or state reset.

If the hook cannot start at all, even read-only tools in that task can be blocked.
Use an external terminal to check the interpreter, installed bundle and
`PLUGIN_DATA` permissions/space/lock holders. Report the diagnostic code to the
owner. A host that cannot launch its shell, or is killed externally, cannot
receive plugin-generated diagnostics.

## Validation and installation

```text
python3 -m unittest discover -s workflow-modes/tests -v
```

The tests use temporary bundles and SQLite files, exercise the registered POSIX
launcher on macOS/Linux and CMD launcher on Windows, and never install the plugin
or change a live session. Windows-specific execution requires a Windows runner;
a passing POSIX suite does not establish Windows or Codex-host behavior.

Repository updates remain source-only. Do not change the cachebuster, sync or
install without an explicit installation request. Before an authorized reinstall,
close tasks still using the previous versioned hook cache. Verify/trust the new
hooks and smoke-test their model-visible behavior in a new task. Source tests do
not replace that host check.
