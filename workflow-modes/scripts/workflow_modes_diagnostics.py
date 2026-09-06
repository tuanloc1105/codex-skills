"""Bounded, model-facing recovery guidance; no database writes or hook imports."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import sys

from workflow_modes_record import BundleError, load_bundle, diagnose_bundle, required_reference_spec

MAX_MESSAGE = 3000


def control_command(action: str, *arguments: str) -> str:
    argv = [sys.executable, str(Path(__file__).with_name("workflow_modes_control.py")),
            action, *arguments, "--marker", "workflow-modes-v1"]
    if os.name == "nt":
        return "& " + " ".join("'" + argument.replace("'", "''") + "'" for argument in argv)
    return shlex.join(argv)


def infrastructure_failure(event: str, error: Exception | str, code: str | None = None) -> int:
    if code is None:
        name = type(error).__name__
        if isinstance(error, (ValueError, json.JSONDecodeError)):
            code, next_step = "WORKFLOW_HOOK_INPUT_INVALID", "Report the malformed hook event to the host owner; retry only after the event schema is fixed."
        elif name in {"OperationalError", "DatabaseError", "IntegrityError"}:
            code, next_step = "WORKFLOW_HOOK_STORAGE_FAILED", "Check PLUGIN_DATA permissions, free space and database lock holders from a terminal. Preserve the database; do not delete or reset it."
        elif isinstance(error, OSError):
            code, next_step = "WORKFLOW_HOOK_FILESYSTEM_FAILED", "Check that PLUGIN_DATA is a writable directory and the installed plugin files exist. Have the owner restore access from a terminal."
        else:
            code, next_step = "WORKFLOW_HOOK_INTERNAL_FAILED", "Report this code and event to the plugin maintainer. Do not edit hook scripts or retry lifecycle mutations blindly."
    else:
        name = str(error)
        next_step = "From a terminal outside this task, check the Python interpreter and installed plugin bundle. Ask the owner to restore missing dependencies/files. Retry only after the launcher succeeds."
    text = (f"{code}: event={event}; failure={name}.\nNext: {next_step}\n"
            "A prior request may already have changed workflow state; after recovery, run snapshot before retrying it. "
            "Do not continue implementation while enforcement is unavailable. Report this blocker to the user.")
    print(text[:MAX_MESSAGE], file=sys.stderr)
    if event == "PreToolUse":
        return 2
    print(json.dumps({"systemMessage": text[:MAX_MESSAGE]}))
    return 0


def enrich_reason(reason: str, payload: dict, state: dict | None, control: dict | None = None) -> str:
    state, control = state or {}, control or {}
    code = reason.split(":", 1)[0]
    record = state.get("record")
    if control.get("record") and (not record or control.get("action") in {"activate", "transition"}):
        target = Path(control["record"]).expanduser()
        if not target.is_absolute():
            target = Path(payload.get("cwd", os.getcwd())) / target
        record = str(target.parent if target.name == "index.md" else target)
    args = ["--record", str(record)] if record else []
    event = payload.get("hook_event_name", "PreToolUse")
    context = f"Event: {event}; mode={state.get('mode')}; record={record}."
    transaction = state.get("write_transaction")
    diagnosis = None
    if record:
        try:
            load_bundle(str(record), str(state["mode"]) if state.get("mode") and not state.get("plan_handoff_source") else None)
        except BundleError as error:
            diagnosis = error
    steps: list[str] = []
    if code in {"WORKFLOW_CONTROL_ARGUMENT_INVALID", "WORKFLOW_CONTROL_AMBIGUOUS", "WORKFLOW_CONTROL_INVALID"}:
        steps = ["Run one Python lifecycle command per tool call, without shell operators. No state was changed by this rejected request.",
                 control_command(control.get("action") if control.get("action") not in {None, "invalid", "ambiguous"} else "snapshot", "--help")]
    elif code == "WORKFLOW_RECORD_MISMATCH":
        steps = ["Use the active record shown above; inspect the session before retrying:", control_command("snapshot")]
    elif code == "WORKFLOW_RECORD_IDENTITY_MISMATCH":
        steps = ["Ask the owner to restore the original tracker identity. Do not rebind or overwrite a different record automatically.", control_command("snapshot")]
    elif diagnosis and code not in {"WORKFLOW_RECOVERY_DENIED", "WORKFLOW_RECOVERY_SCOPE_DENIED"}:
        context += f"\nCause: {diagnosis}"
        steps = [diagnosis.next_step]
        if transaction:
            steps += ["The record write is already open. Repair only its allowed paths with apply_patch; then:", control_command("write-close", *args)]
        elif state.get("baseline_metadata") and record == state.get("record"):
            report = diagnose_bundle(str(record))
            if report["observed_revision"] and not diagnosis.code in {"WORKFLOW_MANIFEST_EXTRA_FILE", "WORKFLOW_RECORD_PATH_UNSAFE"}:
                steps += ["Read the damaged files and baseline from snapshot. To open a guarded repair (identity and baseline will be checked):",
                          control_command("write-open", *args, "--recover", "--previous-revision", state["acknowledged_revision"], "--observed-revision", report["observed_revision"])]
        else:
            steps += ["No trusted automatic recovery baseline is available. Ask the owner to restore an active bundle; for initial activation, finish creating a valid bundle first."]
    elif code in {"WORKFLOW_RECOVERY_DENIED", "WORKFLOW_RECOVERY_SCOPE_DENIED"}:
        steps = ["Inspect the current transaction/baseline. Restore its exact manifest and regular paths; if identity/baseline is unavailable, ask the owner to restore the bundle. Do not reset state.", control_command("snapshot")]
    elif code in {"WORKFLOW_WRITE_CLOSE_REQUIRED", "WORKFLOW_WRITE_ALREADY_OPEN", "WORKFLOW_WRITE_SCOPE_DENIED"}:
        steps = ["Finish the open record transaction using only the paths in snapshot. A valid unchanged bundle can close without artificial edits.", control_command("write-close", *args)]
    elif code in {"WORKFLOW_WRITE_OPEN_REQUIRED", "WORKFLOW_WRITE_OPEN_STALE", "WORKFLOW_RECORD_SYNC_REQUIRED"}:
        if code == "WORKFLOW_WRITE_OPEN_REQUIRED" and state.get("acknowledged_revision") == state.get("record_revision"):
            steps = ["Read the record and open its write transaction before editing:", control_command("write-open", *args, "--previous-revision", state["acknowledged_revision"])]
        else:
            steps = ["Read every manifest member completely; acknowledge the current bundle:", control_command("sync", *args, "--scope", "record"), "Use its returned revision for write-open if a record edit is needed."]
    elif code in {"WORKFLOW_RULES_SYNC_REQUIRED", "WORKFLOW_RULES_SYNC_INVALID", "WORKFLOW_RULES_RECORD_INVALID"}:
        from workflow_modes_record import read_index
        expected, valid = required_reference_spec(state.get("mode", "plan"), read_index(record))
        if not valid:
            steps = ["Repair Required references in index.md through a normal/recovery record write. Retrying --reference arguments cannot repair this field."]
        else:
            references = [value for ref in expected for value in ("--reference", ref)]
            steps = [f"Read the complete ${state.get('mode')} SKILL.md and references: {', '.join(expected) or 'None'}.",
                     "Read and sync the record first if unacknowledged; then:", control_command("rules-sync", *args, *references)]
    elif code in {"WORKFLOW_TURN_CHECKPOINT_REQUIRED", "WORKFLOW_CHECKPOINT_CHANGE_REQUIRED"}:
        steps = ["Persist material deltas through a record write and close it; then:", control_command("checkpoint", *args),
                 "Only after verifying there were no material deltas, use:", control_command("checkpoint", *args, "--no-change")]
    elif code in {"WORKFLOW_ACTION_CLOSE_REQUIRED", "WORKFLOW_EXECUTE_RECONCILIATION_REQUIRED", "WORKFLOW_EVIDENCE_NOT_RECONCILED", "WORKFLOW_ACTION_ALREADY_OPEN"}:
        evidence_id = (state.get("action") or {}).get("evidence_id")
        result = control.get("result") if control.get("result") in {"completed", "failed", "blocked"} else None
        steps = ["Choose the truthful terminal result: completed, failed, or blocked; persist it through a record write."]
        if evidence_id:
            steps += [f"In evidence.md replace <!-- workflow-action:{evidence_id} status:open --> with <!-- workflow-action:{evidence_id} status:{result or '<chosen-result>'} -->; set index.md Active action: None in the same write."]
        steps += ["After write-close, run the matching command:", control_command("action-close", "--result", result or "<chosen-result>"), "Then checkpoint the turn."]
    elif code in {"WORKFLOW_EXECUTE_ACTION_REQUIRED", "WORKFLOW_DISCUSS_ACTION_REQUIRED", "WORKFLOW_ACTION_SCOPE_DENIED", "WORKFLOW_ACTION_UNSCOPED_TOOL", "WORKFLOW_SOURCE_CONFIRMATION_REQUIRED"}:
        steps = ["Use only scope authorized by the user and active record. Reconcile an existing action before opening a different one; persist the evidence and scope through a record write.",
                 "Select --impact non-source or source-confirmed and explicit --path/--unscoped values for that scope:", control_command("action-open", "--help")]
    elif code in {"WORKFLOW_ACTION_MARKER_REQUIRED", "WORKFLOW_EVIDENCE_NOT_PERSISTED", "WORKFLOW_EVIDENCE_ID_REQUIRED", "WORKFLOW_EVIDENCE_ID_INVALID"}:
        evidence_id = control.get("evidence_id") or "<stable-uppercase-ID>"
        steps = [f"Persist <!-- workflow-action:{evidence_id} status:open --> in evidence.md and Active action: {evidence_id} in index.md through one write transaction; close it, then retry action-open with that --evidence-id."]
    elif code == "WORKFLOW_PLAN_ACTIVATION_REQUIRED":
        steps = ["Finish the declared plan bundle; then activate that exact target:", control_command("activate", "plan", "--record", str(state.get("plan_bootstrap")))]
    else:
        steps = ["Inspect the current lifecycle state and the requested action's public usage before retrying. Preserve user authorization and do not bypass this denial.",
                 control_command("snapshot"), control_command(control.get("action", "activate"), "--help")]
    fallback = control_command("diagnose", *args, "--json") if record else control_command("snapshot")
    tail = f"\nInspect: {fallback}\nContinue only after the expected WORKFLOW_* confirmation. If the same blocker remains, report its code and diagnosis; do not edit hook scripts or reset the database."
    body = reason + "\n" + context + "\nNext:\n" + "\n".join(steps)
    if len(body + tail) <= MAX_MESSAGE:
        return body + tail
    # Never emit a clipped command that an agent might execute. Keep a bounded
    # diagnostic fallback when unusually long paths or state exceed the budget.
    compact = reason[:650] + "\nDetails exceed the message limit. Inspect the full diagnosis first."
    if len(compact + tail) <= MAX_MESSAGE:
        return compact + tail
    return compact + "\nRun workflow_modes_control.py diagnose --help from the installed bundle, using the record from the original request. Report path-size limits to the maintainer."
