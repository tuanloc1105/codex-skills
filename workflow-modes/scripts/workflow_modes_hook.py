#!/usr/bin/env python3
"""Persist and enforce tracker-backed Codex workflow modes per session."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from typing import Any, Callable
from workflow_modes_diagnostics import control_command, enrich_reason, infrastructure_failure

from workflow_modes_record import (
    MODES, BundleError, diagnose_bundle, load_bundle, manifest_paths,
    record_files, read_index, record_revision, record_revisions, record_profile,
    record_tracker_id, observation_revision, required_reference_spec, required_references,
    refresh_required_references, files_revision, observed_files, safe_member,
)
from workflow_modes_control import parse_args, shell_arguments, ControlError, ControlHelp

GIT_MUTATION_COMMANDS = "add|commit|push|merge|rebase|reset|clean|checkout|switch|restore"
GIT_MUTATION_PATTERN = rf"\bgit\s+(?:{GIT_MUTATION_COMMANDS})(?=$|[\s;&|])"
EXTERNAL_MUTATION_PATTERN = (
    r"\b(?:glab|gh|tea)\b[^;&|\n]*"
    r"\b(?:approve|close|comment|create|delete|edit|merge|note|reopen|review|update)\b"
    r"|\bacli\s+jira\s+workitem\b[^;&|\n]*"
    r"\b(?:comment|create|edit|transition)\b"
)
MUTATING_SHELL = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:rm|mv|cp|mkdir|touch|chmod|chown|install)\b"
    rf"|{GIT_MUTATION_PATTERN}"
    r"|\b(?:npm|pnpm|yarn|pip|pip3|uv)\s+(?:install|uninstall|add|remove|publish)\b"
    r"|\b(?:docker|podman)\s+(?:build|push|run|compose\s+up)\b"
    r"|\bkubectl\s+(?:apply|create|delete|patch|replace|scale|set)\b"
    r"|\bterraform\s+(?:apply|destroy|import)\b"
    rf"|{EXTERNAL_MUTATION_PATTERN}"
    r"|(?:^|[^>])>{1,2}(?!>)",
    re.IGNORECASE,
)
MUTATING_TOOL_VERBS = {
    "add", "approve", "archive", "close", "comment", "commit", "create",
    "delete", "deploy", "edit", "install", "merge", "move", "publish",
    "push", "remove", "rename", "reopen", "send", "set", "transition",
    "update", "write",
}
COORDINATION_TOOLS = {
    "followup_task", "get_goal", "interrupt_agent", "list_agents",
    "request_user_input", "send_message", "spawn_agent", "update_goal",
    "update_plan", "wait_agent",
}
SOURCE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
    ".java", ".js", ".jsx", ".kt", ".kts", ".lua", ".php", ".py", ".rb",
    ".rs", ".sh", ".sql", ".swift", ".ts", ".tsx", ".vue",
}
SOURCE_MUTATING_SHELL = re.compile(GIT_MUTATION_PATTERN, re.IGNORECASE)
EXTERNAL_MUTATING_SHELL = re.compile(EXTERNAL_MUTATION_PATTERN, re.IGNORECASE)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def session_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


class StateStore:
    def __init__(self) -> None:
        root = Path(
            os.environ.get("PLUGIN_DATA")
            or Path(tempfile.gettempdir()) / "workflow-modes-plugin-data"
        )
        root.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(root / "workflow-modes.sqlite3", timeout=2)
        self.connection.execute("PRAGMA busy_timeout = 2000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "session_key TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        self.connection.commit()

    def get(self, key: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT state_json FROM sessions WHERE session_key = ?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def mutate(
        self,
        key: str,
        callback: Callable[[dict[str, Any] | None], dict[str, Any] | None],
    ) -> dict[str, Any] | None:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            updated = callback(self.get(key))
            if updated is None:
                self.connection.execute("DELETE FROM sessions WHERE session_key = ?", (key,))
            else:
                self.connection.execute(
                    "INSERT INTO sessions(session_key, state_json, updated_at) VALUES(?, ?, ?) "
                    "ON CONFLICT(session_key) DO UPDATE SET state_json=excluded.state_json, "
                    "updated_at=excluded.updated_at",
                    (key, json.dumps(updated, sort_keys=True), utc_now()),
                )
            self.connection.commit()
            return updated
        except Exception:
            self.connection.rollback()
            raise


def context_output(event: str, message: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": message,
        }
    }


def deny_tool(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def tool_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def is_shell_tool(payload: dict[str, Any]) -> bool:
    name = str(payload.get("tool_name", "")).lower()
    return name == "bash" or bool(re.search(r"(?:^|[.:/_-])exec_command$", name))


def is_mutating_tool(payload: dict[str, Any]) -> bool:
    name = str(payload.get("tool_name", ""))
    lowered = name.lower()
    if lowered in COORDINATION_TOOLS:
        return False
    if lowered == "apply_patch" or lowered.endswith("apply_patch"):
        return True
    if is_shell_tool(payload):
        return bool(MUTATING_SHELL.search(tool_command(payload)))
    parts = {part for part in re.split(r"[_\W]+", lowered) if part}
    return bool(parts & MUTATING_TOOL_VERBS)


def patch_paths(command: str) -> set[str]:
    paths = set(
        re.findall(
            r"^\*\*\* (?:Add|Update|Delete) File: (.+)$",
            command,
            flags=re.MULTILINE,
        )
    )
    paths.update(re.findall(r"^\*\*\* Move to: (.+)$", command, flags=re.MULTILINE))
    return {path.strip() for path in paths if path.strip()}


def normalized(path: str, cwd: str) -> str:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    return os.path.normcase(os.path.abspath(candidate))


def canonical_record(path: str, cwd: str | None = None) -> str:
    candidate = Path(normalized(path, cwd or os.getcwd()))
    if candidate.name == "index.md":
        candidate = candidate.parent
    return normalized(str(candidate), cwd or os.getcwd())


def record_matches(path: object, active: object, cwd: str) -> bool:
    return isinstance(path, str) and isinstance(active, str) and canonical_record(path, cwd) == active


def contains_evidence_id(text: str, evidence_id: str) -> bool:
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_-]){re.escape(evidence_id)}(?![A-Za-z0-9_-])",
            text,
        )
    )


def read_evidence(path: str | None) -> str | None:
    files = record_files(path)
    return files.get("evidence.md") if files else None


def action_marker(evidence_id: str, status: str) -> str:
    return f"<!-- workflow-action:{evidence_id} status:{status} -->"


def unscoped_mutation_kind(payload: dict[str, Any]) -> str:
    if not is_shell_tool(payload):
        return "external"
    command = tool_command(payload)
    if SOURCE_MUTATING_SHELL.search(command):
        return "git"
    if EXTERNAL_MUTATING_SHELL.search(command):
        return "external"
    return "shell"


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def paths_for_tool(payload: dict[str, Any]) -> set[str]:
    if str(payload.get("tool_name", "")).lower().endswith("apply_patch"):
        return patch_paths(tool_command(payload))
    return set()


def parse_control(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not is_shell_tool(payload):
        return None
    command = tool_command(payload)
    if "workflow_modes_control.py" not in command:
        return None
    try:
        tokens = shell_arguments(command, windows=os.name == "nt")
    except ControlError as error:
        if "--marker" not in command:
            return None
        return {"action": "ambiguous", "error": str(error)}
    positions = [i for i, t in enumerate(tokens) if Path(t).name == "workflow_modes_control.py"]
    if not positions:
        return None
    script_index = positions[0]
    prefix = tokens[:script_index]
    # Reading a script is not a lifecycle call. A lifecycle invocation must have
    # an interpreter prefix, or execute the script directly, and no shell syntax.
    if prefix and not re.fullmatch(r"(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?", Path(prefix[0]).name.lower()):
        if "--marker" not in tokens:
            return None
        return {"action": "invalid", "error": "Use Python to run the control script directly, without shell wrappers."}
    if len(prefix) > 2 or (len(prefix) == 2 and (Path(prefix[0]).stem.lower() != "py" or prefix[1] != "-3")):
        return {"action": "invalid", "error": "Use Python without interpreter switches (except py -3 on Windows)."}
    script = Path(normalized(tokens[script_index], str(payload.get("cwd", os.getcwd()))))
    if script.resolve() != Path(__file__).with_name("workflow_modes_control.py").resolve() or not script.is_file():
        return {"action": "invalid", "error": "Use the control script from this installed hook bundle."}
    if prefix and shutil.which(prefix[0]) is None:
        return {"action": "invalid", "error": "The requested Python interpreter is unavailable; use the interpreter shown in the diagnostic command."}
    if not prefix and not os.access(script, os.X_OK):
        return {"action": "invalid", "error": "The control script is not executable; invoke it through Python."}
    try:
        parsed = vars(parse_args(tokens[script_index + 1:]))
    except ControlHelp:
        return {"action": "help"}
    except ControlError as error:
        return {"action": "invalid", "error": str(error)}
    parsed["positionals"] = [parsed["mode"]] if "mode" in parsed else []
    for singular, plural in (("path", "paths"), ("reference", "references")):
        if singular in parsed:
            parsed[plural] = parsed.pop(singular)
    return parsed


def state_summary(state: dict[str, Any]) -> str:
    action = state.get("action")
    action_text = "none" if not action else str(action.get("status", "unknown"))
    return (
        f"mode={state.get('mode')}, record={state.get('record')}, "
        f"action={action_text}"
    )


def refresh_sync_requirement(state: dict[str, Any], force_record: bool = False) -> None:
    record, snapshot, outside = record_revisions(state.get("record"))
    state["record_revision"] = record
    state["snapshot_revision"] = snapshot
    state["outside_revision"] = outside
    scope = None
    if force_record:
        scope = "record"
    elif record != state.get("acknowledged_revision"):
        if (
            snapshot is not None
            and snapshot != state.get("acknowledged_snapshot_revision")
            and outside == state.get("acknowledged_outside_revision")
        ):
            scope = "snapshot"
        else:
            scope = "record"
    state["sync_scope"] = scope
    state["sync_required"] = scope is not None


def record_is_synced(state: dict[str, Any]) -> bool:
    refresh_sync_requirement(state)
    return bool(
        state.get("record_revision")
        and not state.get("sync_required")
        and state.get("acknowledged_revision") == state.get("record_revision")
    )


def remember_baseline(state: dict[str, Any], revision: str) -> None:
    files = load_bundle(str(state["record"]))
    if files_revision(files) != revision:
        raise BundleError("WORKFLOW_RECORD_CHANGED", str(state["record"]), "Bundle changed while acknowledging it.", "Read the latest record and retry sync; no new baseline was saved.")
    state["baseline_metadata"] = {
        "revision": revision,
        "root": str(Path(str(state["record"])).resolve()),
        "tracker_id": state.get("tracker_id"),
        "manifest": list(files),
        "files": {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in files.items()},
    }


def recovery_observation(state: dict[str, Any], control: dict[str, Any]) -> tuple[Path, dict[str, bytes]]:
    root = Path(str(state["record"]))
    baseline = state.get("baseline_metadata")
    def reject(detail: str) -> None:
        raise BundleError("WORKFLOW_RECOVERY_DENIED", str(root), detail, "Run snapshot and diagnose. Ask the owner to restore the original bundle if the trusted baseline or identity is unavailable; do not reset session state.")
    if not isinstance(baseline, dict) or not baseline.get("files") or not baseline.get("manifest"):
        reject("No trusted baseline metadata; a valid full sync is required before automatic recovery is available.")
    if (control.get("previous_revision") != state.get("acknowledged_revision")
            or baseline.get("revision") != state.get("acknowledged_revision")):
        reject("Acknowledged baseline changed; take a fresh snapshot before requesting recovery.")
    if (str(root.resolve()) != baseline.get("root") or not state.get("tracker_id")
            or record_tracker_id(str(root)) != state.get("tracker_id")
            or baseline.get("tracker_id") != state.get("tracker_id")):
        reject("Bundle root or tracker identity is missing or changed.")
    observed = observed_files(root)
    extra = sorted(set(observed) - set(baseline["files"]))
    if extra:
        reject("Unacknowledged Markdown exists: " + ", ".join(extra) + ". Ask its owner to reconcile it; recovery cannot add or delete these files.")
    for name in baseline["files"]:
        safe_member(root, name)
    if observation_revision(observed) != control.get("observed_revision"):
        reject("Observed bundle changed; run diagnose again before requesting recovery.")
    try:
        load_bundle(str(root), str(state["mode"]))
    except BundleError:
        return root, observed
    reject("Bundle is valid; use ordinary read/sync/write-open instead of recovery.")


def open_recovery(store: StateStore, key: str, current: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    def begin(latest):
        if not latest or latest.get("record") != current.get("record") or latest.get("write_transaction"):
            raise BundleError("WORKFLOW_RECOVERY_DENIED", str(current.get("record")), "Session changed or another transaction opened.", "Take a fresh snapshot; finish the existing transaction before retrying.")
        root, _ = recovery_observation(latest, control)
        latest["write_transaction"] = {
            "baseline": latest["acknowledged_revision"], "opened_at": utc_now(),
            "recovery": True, "observed_revision": control["observed_revision"],
            "paths": sorted(normalized(str(root / name), str(root)) for name in latest["baseline_metadata"]["files"]),
        }
        latest["updated_at"] = utc_now()
        return latest
    try:
        store.mutate(key, begin)
    except BundleError as error:
        return deny_tool("WORKFLOW_RECOVERY_DENIED: " + str(error))
    return context_output("PreToolUse", "WORKFLOW_RECOVERY_OPEN: repair only acknowledged Markdown files using apply_patch; keep the original manifest and tracker ID. Then run write-close. Existing actions still require reconciliation.")


def handle_control(
    store: StateStore, key: str, payload: dict[str, Any], control: dict[str, Any]
) -> dict[str, Any] | None:
    action = control.get("action")
    if action == "invalid":
        return deny_tool("WORKFLOW_CONTROL_ARGUMENT_INVALID: " + str(control.get("error")))
    if action in {"help", "diagnose"}:
        return None
    if action == "ambiguous":
        return deny_tool(
            "WORKFLOW_CONTROL_AMBIGUOUS: run only one marker-backed lifecycle control "
            "request per tool call."
        )
    cwd = str(payload.get("cwd", os.getcwd()))
    current = store.get(key)
    if (current and (current.get("write_transaction") or {}).get("recovery")
            and action not in {"snapshot", "write-close"}):
        return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: finish the recovery transaction before another lifecycle change.")
    if action in {"activate", "transition"}:
        if current and current.get("write_transaction"):
            return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: close the current record write before activation or transition.")
        if current and current.get("action"):
            return deny_tool("WORKFLOW_ACTION_CLOSE_REQUIRED: close the current action before activation or transition.")
        positionals = control.get("positionals", [])
        mode = positionals[0] if positionals else None
        record = control.get("record")
        if mode not in MODES or (
            not isinstance(record, str) and not (action == "activate" and mode == "plan")
        ):
            return deny_tool(
                "WORKFLOW_MODE_INVALID: a valid mode is required, and --record is required "
                "except for initial plan activation."
            )
        if action == "activate" and current and current.get("mode") != mode:
            return deny_tool(
                f"WORKFLOW_TRANSITION_REQUIRED: {current.get('mode')} is active; use a valid "
                f"transition instead of activating {mode}."
            )
        absolute_record = canonical_record(record, cwd) if isinstance(record, str) else None
        if current and current.get("plan_revision"):
            if absolute_record != current.get("record"):
                return deny_tool("WORKFLOW_RECORD_MISMATCH: keep the active revision bundle.")
            if record_tracker_id(absolute_record) != current.get("tracker_id"):
                return deny_tool("WORKFLOW_RECORD_IDENTITY_MISMATCH: preserve the active tracker identity.")
        if (
            action == "activate"
            and mode == "plan"
            and current
            and current.get("mode") == "plan"
            and current.get("plan_handoff_source")
        ):
            target = current.get("plan_bootstrap")
            if not isinstance(target, str):
                return deny_tool(
                    "WORKFLOW_PLAN_INIT_REQUIRED: declare the separate plan target with "
                    "plan-init before creating or activating it."
                )
            if absolute_record != target:
                return deny_tool(
                    "WORKFLOW_PLAN_TARGET_MISMATCH: activate the exact target declared by plan-init."
                )
        record_text = read_index(absolute_record) if absolute_record else None
        if record_text is not None and not re.search(
            r"workflow-record[^\n>]*version:4[^\n>]*tracker-id:[^\s>]+", record_text
        ):
            return deny_tool("WORKFLOW_RECORD_VERSION_UNSUPPORTED: record bundles require version 4.")
        if absolute_record and record_files(absolute_record) is None:
            record_text = None
        if isinstance(record, str) and record_text is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the record bundle must exist and be valid.")
        if action == "activate" and mode == "discuss":
            missing = missing_markers(record_text or "", ("Mode: $discuss", "Mode status:"))
            if missing:
                return deny_tool(
                    "WORKFLOW_RECORD_NOT_DISCUSS: tracker lacks required discuss markers: "
                    + ", ".join(missing)
                )
        if action == "activate" and mode == "execute":
            missing = missing_markers(record_text or "", ("Execute mode: Active",))
            if missing:
                return deny_tool(
                    "WORKFLOW_RECORD_NOT_ACTIVE: persist execute activation before implementation."
                )
        if action == "transition":
            if not current:
                return deny_tool("WORKFLOW_MODE_INACTIVE: activate a tracker-backed mode first.")
            if current.get("write_transaction"):
                return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: close the record write transaction before transition.")
            allowed = {
                "discuss": {"plan", "execute"},
                "plan": {"execute"},
                "execute": {"discuss"},
            }
            if mode not in allowed.get(str(current.get("mode")), set()):
                return deny_tool(
                    f"WORKFLOW_TRANSITION_DENIED: {current.get('mode')} cannot transition to {mode}."
                )
            if record_text is None:
                return deny_tool("WORKFLOW_RECORD_UNREADABLE: transition record is not readable.")
            if current.get("mode") == "execute" and mode == "discuss":
                if not control.get("user_authorized"):
                    return deny_tool(
                        "WORKFLOW_PLAN_REVISION_AUTHORIZATION_REQUIRED: return to discuss only "
                        "when the user explicitly authorizes plan revision; attest with --user-authorized."
                    )
                if not record_matches(record, current.get("record"), cwd):
                    return deny_tool("WORKFLOW_RECORD_MISMATCH: revise the active bundle, not a different record.")
                if record_tracker_id(absolute_record) != current.get("tracker_id"):
                    return deny_tool("WORKFLOW_RECORD_IDENTITY_MISMATCH: preserve the active tracker identity.")
                if not record_is_synced(current):
                    return deny_tool("WORKFLOW_RECORD_SYNC_REQUIRED: read and sync the active bundle before revising it.")
                required = ("Status: Draft", "Execute mode: Inactive", "Mode: $discuss", "Mode status: Active")
            elif current.get("mode") == "discuss" and current.get("plan_revision"):
                if mode != "plan":
                    return deny_tool("WORKFLOW_TRANSITION_DENIED: return to plan after revision discussion before execute.")
                if not record_is_synced(current):
                    return deny_tool("WORKFLOW_RECORD_SYNC_REQUIRED: read and sync the revision bundle before planning.")
                required = ("Mode status: Exited", "Status: Draft", "Execute mode: Inactive")
            elif current.get("mode") == "discuss" and mode == "plan":
                required = ("Mode status: Exited",)
            elif current.get("mode") == "discuss" and mode == "execute":
                required = (
                    "Mode status: Exited",
                    "Execution readiness: Ready",
                    "Execute mode: Ready",
                )
                bundle_files = record_files(absolute_record)
                if not bundle_files or not {"plan.md", "verification.md"}.issubset(bundle_files):
                    return deny_tool(
                        "WORKFLOW_HANDOFF_NOT_DURABLE: direct execute requires plan.md and verification.md."
                    )
            else:
                required = ("Status: Approved plan, not yet implemented", "Execute mode: Ready")
            if mode == "discuss" or current.get("plan_revision"):
                for marker in required:
                    label = marker.split(":", 1)[0]
                    values = re.findall(rf"^{re.escape(label)}:[^\n]*", record_text, re.MULTILINE)
                    if not values or any(value.strip() != marker for value in values):
                        return deny_tool(
                            "WORKFLOW_PLAN_REVISION_NOT_DURABLE: persist the user's permission "
                            "and scope through a record write; required lifecycle fields: " + ", ".join(required)
                        )
            missing = missing_markers(record_text, required)
            if missing:
                return deny_tool(
                    "WORKFLOW_HANDOFF_NOT_DURABLE: record lacks required markers: "
                    + ", ".join(missing)
                )
        revision, snapshot_revision, outside_revision = record_revisions(absolute_record)
        state = {
            "active": True,
            "mode": mode,
            "record": absolute_record,
            "action": None,
            "write_transaction": None,
            "stop_warning_issued": False,
            "record_revision": revision,
            "snapshot_revision": snapshot_revision,
            "outside_revision": outside_revision,
            "profile": record_profile(absolute_record),
            "tracker_id": record_tracker_id(absolute_record),
            "acknowledged_revision": None,
            "acknowledged_snapshot_revision": None,
            "acknowledged_outside_revision": None,
            "sync_required": bool(absolute_record),
            "sync_scope": "record" if absolute_record else None,
            "checkpoint_required": False,
            "turn_start_revision": revision,
            "required_references": list(required_references(mode, record_text)),
            "required_references_valid": required_reference_spec(mode, record_text)[1],
            "rules_sync_required": True,
            "updated_at": utc_now(),
        }
        if current and mode == "discuss" and (
            current.get("plan_revision") or (action == "transition" and current.get("mode") == "execute")
        ):
            state["plan_revision"] = True
        if (
            action == "transition"
            and current
            and not current.get("plan_revision")
            and current.get("mode") == "discuss"
            and mode == "plan"
        ):
            state["plan_handoff_source"] = absolute_record
        store.mutate(key, lambda _old: state)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_MODE_ACTIVE: {state_summary(state)}. The tracker is authoritative; "
            "read and reconcile it before substantive work.",
        )
    if action == "deactivate":
        if current and current.get("write_transaction"):
            return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: close the record write transaction first.")
        if current and current.get("mode") == "execute" and current.get("action"):
            return deny_tool(
                "WORKFLOW_ACTION_CLOSE_REQUIRED: reconcile and close the execute action "
                "before deactivating execute mode."
            )
        if current and current.get("mode") != "execute":
            return deny_tool(
                "WORKFLOW_EXIT_DENIED: discuss and plan exit only through a valid plan/execute transition."
            )
        store.mutate(key, lambda _old: None)
        return context_output("PreToolUse", "WORKFLOW_MODE_INACTIVE: execute explicitly exited.")
    if not current:
        if action == "snapshot":
            return context_output(
                "PreToolUse",
                "WORKFLOW_MODE_SNAPSHOT: inactive; no workflow is active in this session. "
                "To resume an accepted execution bundle, follow execute's Fresh-Session Bootstrap, "
                "then activate execute with that exact --record and sync record/rules before implementation. "
                "--help only displays usage; it does not activate a mode.\n"
                + json.dumps({"active": False, "mode": None, "record": None}, sort_keys=True),
            )
        return deny_tool("WORKFLOW_MODE_INACTIVE: activate a tracker-backed mode first.")
    if action == "plan-init":
        if current.get("mode") != "plan" or not current.get("plan_handoff_source"):
            return deny_tool(
                "WORKFLOW_PLAN_INIT_DENIED: plan-init is only valid immediately after a "
                "discuss-to-plan transition."
            )
        if current.get("write_transaction") or current.get("action"):
            return deny_tool(
                "WORKFLOW_PLAN_INIT_DENIED: close the active transaction or action first."
            )
        if current.get("plan_bootstrap"):
            return deny_tool(
                "WORKFLOW_PLAN_INIT_ALREADY_OPEN: activate the declared target before "
                "starting another plan bundle."
            )
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool(
                "WORKFLOW_RECORD_MISMATCH: plan-init source differs from the transitioned tracker."
            )
        target_value = control.get("target")
        if not isinstance(target_value, str):
            return deny_tool("WORKFLOW_PLAN_TARGET_INVALID: plan-init requires --target.")
        target = canonical_record(target_value, cwd)
        target_path = Path(target)
        source_path = Path(str(current.get("record")))
        try:
            resolved_target = target_path.resolve(strict=False)
            resolved_source = source_path.resolve(strict=True)
        except OSError:
            return deny_tool("WORKFLOW_PLAN_TARGET_INVALID: plan target could not be resolved safely.")
        if (
            target_path.exists()
            or ".git" in target_path.parts
            or resolved_target == resolved_source
            or resolved_source in resolved_target.parents
        ):
            return deny_tool(
                "WORKFLOW_PLAN_TARGET_INVALID: target must be a new directory outside the "
                "source bundle and Git metadata."
            )
        existing = target_path.parent
        while not existing.exists() and existing != existing.parent:
            existing = existing.parent
        if existing.is_symlink():
            return deny_tool(
                "WORKFLOW_PLAN_TARGET_INVALID: target ancestry must not traverse a symlink."
            )
        current["plan_bootstrap"] = target
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_PLAN_INIT_OPEN: target={target}; only files beneath this new plan "
            "bundle may be created until activate plan validates and binds it.",
        )
    if action == "rules-sync":
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: rules-sync record differs from active tracker.")
        expected, valid = required_reference_spec(
            str(current.get("mode")), read_index(str(current.get("record")))
        )
        supplied = control.get("references", [])
        if not valid:
            return deny_tool("WORKFLOW_RULES_RECORD_INVALID: repair index.md Required references; changing CLI arguments alone cannot fix the snapshot.")
        if len(supplied) != len(set(supplied)) or set(supplied) != set(expected):
            return deny_tool(
                "WORKFLOW_RULES_SYNC_INVALID: --reference values must exactly match the "
                f"required {current.get('mode')} reference set: {', '.join(expected) or 'None'}."
            )
        current["required_references"] = list(expected)
        current["rules_sync_required"] = False
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_RULES_SYNCED: mode={current.get('mode')}, references="
            f"{','.join(expected) or 'None'}.",
        )
    if action in {"action-open", "checkpoint"} and current.get("rules_sync_required"):
        return deny_tool(
            "WORKFLOW_RULES_SYNC_REQUIRED: reread the mode SKILL.md and required references, "
            "then run rules-sync before this control call."
        )
    if action == "sync":
        if current.get("write_transaction"):
            return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: close the record write before sync.")
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: sync record differs from active tracker.")
        scope = control.get("scope", "record")
        if scope not in {"record", "snapshot"}:
            return deny_tool("WORKFLOW_SYNC_SCOPE_INVALID: sync scope must be record or snapshot.")
        if not current.get("sync_required"):
            refresh_sync_requirement(current)
        if scope == "snapshot" and current.get("sync_scope") != "snapshot":
            return deny_tool(
                "WORKFLOW_RECORD_SYNC_REQUIRED: snapshot sync cannot satisfy the currently "
                "required record scope."
            )
        revision, snapshot_revision, outside_revision = record_revisions(
            str(current.get("record"))
        )
        if revision is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
        tracker_id = record_tracker_id(str(current.get("record")))
        if current.get("tracker_id") and tracker_id != current.get("tracker_id"):
            return deny_tool(
                "WORKFLOW_RECORD_IDENTITY_MISMATCH: the active path now contains a different "
                "tracker ID; restore the record or explicitly rebind the workflow."
            )
        if scope == "snapshot" and (
            snapshot_revision is None
            or outside_revision != current.get("acknowledged_outside_revision")
        ):
            return deny_tool(
                "WORKFLOW_RECORD_SYNC_REQUIRED: snapshot-only sync cannot acknowledge "
                "missing snapshot state or changes outside the active snapshot."
            )
        current["tracker_id"] = tracker_id or current.get("tracker_id")
        current["record_revision"] = revision
        current["snapshot_revision"] = snapshot_revision
        current["outside_revision"] = outside_revision
        current["acknowledged_revision"] = revision
        current["acknowledged_snapshot_revision"] = snapshot_revision
        current["acknowledged_outside_revision"] = outside_revision
        remember_baseline(current, revision)
        current["sync_required"] = False
        current["sync_scope"] = None
        current["profile"] = record_profile(str(current.get("record")))
        refresh_required_references(current)
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_RECORD_SYNCED: mode={current.get('mode')}, "
            f"record={current.get('record')}, scope={scope}, revision={revision}.",
        )
    if action == "write-open":
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: write-open record differs from active bundle.")
        if current.get("write_transaction"):
            return deny_tool("WORKFLOW_WRITE_ALREADY_OPEN: close the current write transaction first.")
        if control.get("recover"):
            return open_recovery(store, key, current, control)
        previous = control.get("previous_revision")
        if previous != current.get("acknowledged_revision") or not record_is_synced(current):
            return deny_tool(
                "WORKFLOW_WRITE_OPEN_STALE: previous revision is not the acknowledged bundle "
                "baseline; read and sync the record first."
            )
        root = Path(str(current.get("record")))
        allowed = {
            normalized(str(root / entry), cwd)
            for entry in (manifest_paths(str(root)) or ())
        }
        for requested_path in control.get("paths", []):
            candidate = Path(normalized(requested_path, cwd))
            try:
                candidate.relative_to(root)
            except ValueError:
                return deny_tool("WORKFLOW_WRITE_PATH_INVALID: declared write paths must stay inside the bundle.")
            if candidate.suffix.lower() != ".md":
                return deny_tool("WORKFLOW_WRITE_PATH_INVALID: record bundle paths must be Markdown files.")
            allowed.add(str(candidate))
        current["write_transaction"] = {
            "baseline": previous,
            "opened_at": utc_now(),
            "paths": sorted(allowed),
        }
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_WRITE_OPEN: record={current.get('record')}; only manifest-owned "
            "Markdown files may change until write-close.",
        )
    if action == "write-close":
        before_close = copy.deepcopy(current)
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: write-close record differs from active bundle.")
        transaction = current.get("write_transaction")
        if not isinstance(transaction, dict):
            return deny_tool("WORKFLOW_WRITE_MISSING: no record write transaction is open.")
        previous = transaction.get("baseline")
        try:
            files = load_bundle(str(current.get("record")), str(current.get("mode")))
        except BundleError as error:
            return deny_tool("WORKFLOW_WRITE_CLOSE_INVALID: " + str(error))
        if transaction.get("recovery"):
            baseline = current.get("baseline_metadata", {})
            if list(files) != baseline.get("manifest") or str(Path(str(current["record"])).resolve()) != baseline.get("root"):
                return deny_tool("WORKFLOW_RECOVERY_SCOPE_DENIED: restore the exact acknowledged manifest and original bundle root before closing recovery.")
        revision, snapshot_revision, outside_revision = record_revisions(
            str(current.get("record"))
        )
        if revision is None or revision != files_revision(files):
            return deny_tool(
                "WORKFLOW_WRITE_CLOSE_INVALID: repair the invalid bundle before closing this transaction."
            )
        tracker_id = record_tracker_id(str(current.get("record")))
        if current.get("tracker_id") and tracker_id != current.get("tracker_id"):
            return deny_tool(
                "WORKFLOW_RECORD_IDENTITY_MISMATCH: write-close cannot acknowledge a different tracker."
            )
        current["record_revision"] = revision
        current["snapshot_revision"] = snapshot_revision
        current["outside_revision"] = outside_revision
        current["acknowledged_revision"] = revision
        current["acknowledged_snapshot_revision"] = snapshot_revision
        current["acknowledged_outside_revision"] = outside_revision
        remember_baseline(current, revision)
        current["sync_required"] = False
        current["sync_scope"] = None
        current["write_transaction"] = None
        current["profile"] = record_profile(str(current.get("record")))
        refresh_required_references(current)
        current["updated_at"] = utc_now()
        def close_if_current(latest):
            if latest != before_close:
                raise BundleError("WORKFLOW_STATE_CHANGED", str(record), "Session changed during write-close.", "Take a fresh snapshot before retrying write-close.")
            final_files = load_bundle(str(current["record"]), str(current["mode"]))
            if files_revision(final_files) != revision:
                raise BundleError("WORKFLOW_RECORD_CHANGED", str(record), "Bundle changed during write-close.", "Read and repair the current bundle before retrying write-close.")
            return current
        try:
            store.mutate(key, close_if_current)
        except BundleError as error:
            return deny_tool(str(error))
        return context_output(
            "PreToolUse",
            f"WORKFLOW_WRITE_CLOSED: mode={current.get('mode')}, "
            f"record={current.get('record')}, revision={revision}, changed={str(revision != previous).lower()}.",
        )
    if action == "checkpoint":
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool(
                "WORKFLOW_RECORD_MISMATCH: checkpoint record differs from active tracker."
            )
        current_revision = record_revision(str(current.get("record")))
        if current_revision is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
        if current.get("sync_required") or not current.get("acknowledged_revision"):
            return deny_tool(
                "WORKFLOW_RECORD_SYNC_REQUIRED: read the exact tracker completely and run "
                "sync before checkpointing the turn."
            )
        if current.get("write_transaction"):
            return deny_tool("WORKFLOW_WRITE_CLOSE_REQUIRED: close the record write transaction before checkpointing.")
        if current.get("action"):
            return deny_tool(
                "WORKFLOW_ACTION_CLOSE_REQUIRED: close the active action before checkpointing."
            )
        current["record_revision"] = current_revision
        changed = current_revision != current.get("turn_start_revision")
        if current.get("acknowledged_revision") != current_revision:
            current["sync_required"] = True
            current["sync_scope"] = "record"
            store.mutate(key, lambda _old: current)
            return deny_tool(
                "WORKFLOW_RECORD_SYNC_REQUIRED: the active tracker revision was not acknowledged."
            )
        if current.get("checkpoint_required") and not changed and not control.get("no_change"):
            return deny_tool(
                "WORKFLOW_CHECKPOINT_CHANGE_REQUIRED: the tracker did not change this turn; "
                "persist material deltas or use checkpoint --no-change after confirming none exist."
            )
        current["checkpoint_required"] = False
        current["acknowledged_revision"] = current_revision
        current["last_checkpoint_revision"] = current.get("record_revision")
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_TURN_CHECKPOINTED: mode={current.get('mode')}, "
            f"record={current.get('record')}, changed={str(changed).lower()}.",
        )
    if action == "snapshot":
        fields = ("mode", "record", "tracker_id", "acknowledged_revision", "record_revision",
                  "sync_scope", "rules_sync_required", "required_references", "write_transaction",
                  "action", "checkpoint_required", "baseline_metadata")
        snapshot = {field: current.get(field) for field in fields}
        snapshot["current_revision"] = record_revision(current.get("record"))
        snapshot["diagnosis"] = diagnose_bundle(str(current["record"])) if current.get("record") else None
        return context_output("PreToolUse", f"WORKFLOW_MODE_SNAPSHOT: {state_summary(current)}.\n" + json.dumps(snapshot, sort_keys=True))
    if action == "action-open":
        if current.get("mode") not in {"discuss", "execute"}:
            return deny_tool("WORKFLOW_ACTION_DENIED: scoped actions require discuss or execute mode.")
        if current.get("action"):
            return deny_tool("WORKFLOW_ACTION_ALREADY_OPEN: close the current action first.")
        if not record_is_synced(current):
            store.mutate(key, lambda _old: current)
            return deny_tool(
                "WORKFLOW_RECORD_SYNC_REQUIRED: read the exact tracker completely and run "
                "sync before opening a workflow action."
            )
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: action record differs from active tracker.")
        record_text = read_evidence(str(current.get("record"))) if current.get("mode") == "execute" else read_index(str(current.get("record")))
        if record_text is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
        impact = control.get("impact")
        if impact not in {"non-source", "source-confirmed"}:
            return deny_tool("WORKFLOW_ACTION_INVALID: --impact must classify source impact.")
        paths = [normalized(path, cwd) for path in control.get("paths", [])]
        unscoped = control.get("unscoped", [])
        if not isinstance(unscoped, list) or not set(unscoped).issubset(
            {"git", "external", "shell"}
        ):
            return deny_tool("WORKFLOW_ACTION_INVALID: unsupported --unscoped classification.")
        evidence_id = control.get("evidence_id")
        if current.get("mode") == "execute":
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                return deny_tool(
                    "WORKFLOW_EVIDENCE_ID_REQUIRED: execute actions require --evidence-id "
                    "for a checkpoint already persisted in the tracker."
                )
            if not re.fullmatch(r"[A-Z][A-Z0-9_-]{2,63}", evidence_id):
                return deny_tool(
                    "WORKFLOW_EVIDENCE_ID_INVALID: use a stable uppercase tracker ID such "
                    "as A057."
                )
            if not contains_evidence_id(record_text, evidence_id):
                return deny_tool(
                    "WORKFLOW_EVIDENCE_NOT_PERSISTED: the execute action evidence ID is "
                    "absent from the active tracker."
                )
            if action_marker(evidence_id, "open") not in record_text:
                return deny_tool(
                    "WORKFLOW_ACTION_MARKER_REQUIRED: persist the exact open marker for the "
                    "execute action before action-open."
                )
        current["action"] = {
            "status": "authorized",
            "paths": sorted(set(paths)),
            "impact": impact,
            "opened_at": utc_now(),
            "evidence_id": evidence_id,
            "unscoped": sorted(set(unscoped)),
        }
        current["stop_warning_issued"] = False
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_ACTION_OPEN: bounded {current.get('mode')} action authorized; close it "
            "only after persisting the terminal result in the tracker.",
        )
    if action == "action-close":
        if current.get("mode") not in {"discuss", "execute"} or not current.get("action"):
            return deny_tool("WORKFLOW_ACTION_MISSING: no workflow action is open.")
        action_mode = current.get("mode")
        result = control.get("result")
        if result not in {"completed", "failed", "blocked"}:
            return deny_tool(
                "WORKFLOW_ACTION_RESULT_INVALID: action-close requires completed, failed, "
                "or blocked."
            )
        if current.get("mode") == "execute":
            record_text = read_evidence(str(current.get("record")))
            if record_text is None:
                return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
            evidence_id = current["action"].get("evidence_id")
            if not isinstance(evidence_id, str) or not contains_evidence_id(record_text, evidence_id):
                return deny_tool(
                    "WORKFLOW_EVIDENCE_NOT_PERSISTED: the action evidence ID must remain in "
                    "the execution record."
                )
            if action_marker(evidence_id, result) not in record_text:
                return deny_tool(
                    "WORKFLOW_EVIDENCE_NOT_RECONCILED: replace the action's open marker with "
                    "the exact terminal marker matching --result before action-close."
                )
            if action_marker(evidence_id, "open") in record_text:
                return deny_tool(
                    "WORKFLOW_EVIDENCE_NOT_RECONCILED: remove the action's open marker before "
                    "action-close."
                )
        current["action"] = None
        current["stop_warning_issued"] = False
        store.mutate(key, lambda _old: current)
        close_message = (
            "full discuss guardrails restored."
            if action_mode == "discuss"
            else "tracker evidence reconciled."
        )
        return context_output(
            "PreToolUse",
            f"WORKFLOW_ACTION_CLOSED: result={control.get('result')}; {close_message}",
        )
    if action == "action-abort":
        if current.get("mode") != "execute" or not current.get("action"):
            return deny_tool("WORKFLOW_ACTION_MISSING: no execute action is open.")
        if control.get("reason") != "record-unreadable":
            return deny_tool(
                "WORKFLOW_ACTION_ABORT_DENIED: only record-unreadable recovery is supported."
            )
        if record_files(str(current.get("record"))) is not None:
            return deny_tool(
                "WORKFLOW_ACTION_ABORT_DENIED: the active execution record is still readable."
            )
        current["action"] = None
        current["stop_warning_issued"] = False
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            "WORKFLOW_ACTION_ABORTED: unreadable-record recovery cleared the execute action; "
            "repair or restore the tracker before further mutation.",
        )
    return deny_tool("WORKFLOW_CONTROL_INVALID: unsupported lifecycle action.")


def record_or_housekeeping_path(path: str, state: dict[str, Any], cwd: str) -> bool:
    absolute = normalized(path, cwd)
    record = state.get("record")
    if isinstance(record, str):
        entries = manifest_paths(record) or tuple(state.get("baseline_metadata", {}).get("files", {}))
        owned = {normalized(str(Path(record) / entry), cwd) for entry in entries}
        if absolute in owned:
            return True
    if state.get("mode") != "execute" and Path(absolute).name == ".gitignore":
        return True
    return False


def handle_pre_tool(
    store: StateStore, key: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    control = parse_control(payload)
    if control:
        return handle_control(store, key, payload, control)
    state = store.get(key)
    if not state or not is_mutating_tool(payload):
        return None
    mode = state.get("mode")
    cwd = str(payload.get("cwd", os.getcwd()))
    paths = paths_for_tool(payload)
    if state.get("write_transaction"):
        if paths:
            requested = {normalized(path, cwd) for path in paths}
            allowed = set(state["write_transaction"].get("paths", []))
            if requested.issubset(allowed):
                if state["write_transaction"].get("recovery"):
                    if re.search(r"^\*\*\* (?:Delete File:|Move to:)", tool_command(payload), re.MULTILINE):
                        return deny_tool("WORKFLOW_RECOVERY_SCOPE_DENIED: recovery only updates or restores acknowledged files; deletion and renames are forbidden.")
                    try:
                        root = Path(str(state["record"]))
                        if str(root.resolve()) != state.get("baseline_metadata", {}).get("root"):
                            raise ValueError("bundle root changed")
                        for path in requested:
                            safe_member(root, Path(path).relative_to(root).as_posix())
                    except (BundleError, ValueError):
                        return deny_tool("WORKFLOW_RECOVERY_SCOPE_DENIED: restore the original regular bundle paths; symlinks and changed roots cannot be repaired automatically.")
                return None
        return deny_tool(
            "WORKFLOW_WRITE_SCOPE_DENIED: while a record write is open, only manifest-owned "
            "Markdown files may be mutated."
        )
    bootstrap = state.get("plan_bootstrap")
    if isinstance(bootstrap, str):
        requested = {normalized(path, cwd) for path in paths}
        inside_target = bool(requested) and all(
            (Path(path) == Path(bootstrap) or Path(bootstrap) in Path(path).parents)
            and Path(path).suffix.lower() == ".md"
            for path in requested
        )
        if str(payload.get("tool_name", "")).lower().endswith("apply_patch") and inside_target:
            return None
        return deny_tool(
            "WORKFLOW_PLAN_BOOTSTRAP_SCOPE_DENIED: while plan initialization is open, "
            "only apply_patch writes beneath the declared target are allowed."
        )
    if paths and all(record_or_housekeeping_path(path, state, cwd) for path in paths):
        requested = {normalized(path, cwd) for path in paths}
        record = str(state.get("record"))
        owned = {
            normalized(str(Path(record) / entry), cwd)
            for entry in (manifest_paths(record) or tuple(state.get("baseline_metadata", {}).get("files", {})))
        }
        if requested & owned:
            return deny_tool(
                "WORKFLOW_WRITE_OPEN_REQUIRED: open a record write transaction before changing "
                "manifest-owned Markdown files."
            )
        return None
    if state.get("rules_sync_required"):
        return deny_tool(
            "WORKFLOW_RULES_SYNC_REQUIRED: activate the current skill, reread its complete "
            "SKILL.md and required references, sync the record, then run rules-sync before mutation."
        )
    if not record_is_synced(state):
        store.mutate(key, lambda _old: state)
        return deny_tool(
            "WORKFLOW_RECORD_SYNC_REQUIRED: the active tracker is unacknowledged or changed; "
            "read it completely and run sync before non-record mutation."
        )
    if mode == "execute" and not state.get("action"):
        return deny_tool(
            "WORKFLOW_EXECUTE_ACTION_REQUIRED: persist an evidence checkpoint, open an "
            "execute action, then perform the mutation."
        )
    if mode == "plan":
        return deny_tool(
            "WORKFLOW_PLAN_READ_ONLY: source mutation is blocked in plan mode. Persist the "
            "approved plan, then transition explicitly to execute."
        )
    action = state.get("action")
    if not action:
        return deny_tool(
            "WORKFLOW_DISCUSS_ACTION_REQUIRED: persist and open a scoped discuss action "
            "before mutation."
        )
    allowed_paths = set(action.get("paths", []))
    if paths:
        requested = {normalized(path, cwd) for path in paths}
        if (not allowed_paths and mode == "execute") or not requested.issubset(
            allowed_paths | {str(state.get("record"))}
        ):
            return deny_tool(
                "WORKFLOW_ACTION_SCOPE_DENIED: requested files exceed the persisted action scope."
            )
        if action.get("impact") == "non-source" and any(
            Path(path).suffix.lower() in SOURCE_EXTENSIONS for path in requested
        ):
            return deny_tool(
                "WORKFLOW_SOURCE_CONFIRMATION_REQUIRED: source-like files require a "
                "source-confirmed discuss action."
            )
        return None
    if mode == "execute":
        mutation_kind = unscoped_mutation_kind(payload)
        if action.get("impact") == "non-source" and mutation_kind == "git":
            return deny_tool(
                "WORKFLOW_SOURCE_CONFIRMATION_REQUIRED: Git source/history mutations require "
                "an execute action opened with --impact source-confirmed."
            )
        allowed_unscoped = set(action.get("unscoped", []))
        if mutation_kind not in allowed_unscoped:
            return deny_tool(
                "WORKFLOW_ACTION_UNSCOPED_TOOL: this execute action did not authorize the "
                f"unscoped mutation class '{mutation_kind}'."
            )
        return None
    mutation_kind = unscoped_mutation_kind(payload)
    if action.get("impact") == "non-source" and mutation_kind == "git":
        return deny_tool(
            "WORKFLOW_SOURCE_CONFIRMATION_REQUIRED: Git source/history mutations require "
            "a discuss action opened with --impact source-confirmed."
        )
    allowed_unscoped = set(action.get("unscoped", []))
    if mutation_kind not in allowed_unscoped:
        return deny_tool(
            "WORKFLOW_ACTION_UNSCOPED_TOOL: this discuss action did not authorize the "
            f"unscoped mutation class '{mutation_kind}'."
        )
    return None


def mode_message(state: dict[str, Any]) -> str:
    mode = state.get("mode")
    common = (
        "<workflow-anchor version=\"2\"> "
        f"mode={mode}; record={state.get('record')}; tracker_id={state.get('tracker_id')}; "
        f"record_revision={state.get('record_revision')}; profile={state.get('profile')}; "
        f"sync_status={state.get('sync_scope') or 'current'}; "
        f"required_references={','.join(state.get('required_references', [])) or 'None'}; "
        f"rules_sync_required={str(bool(state.get('rules_sync_required'))).lower()}; "
        "rule=when sync is required, read the requested record or active snapshot scope, "
        "then run matching sync before substantive work; "
        "rule=persist material turn changes and run checkpoint before final response. "
    )
    if mode == "discuss":
        if state.get("plan_revision"):
            return common + "exit=transition plan using the same bundle after revision discussion; no plan-init. </workflow-anchor>"
        return common + "exit=only plan or execute. </workflow-anchor>"
    if mode == "plan":
        return common + "boundary=source-read-only until execute transition. </workflow-anchor>"
    return common + (
        "exit=explicit request only, including after implementation; "
        "revision=when the user permits plan changes, reconcile open actions, write permission/scope "
        "and Status: Draft, Execute mode: Inactive, Mode: $discuss, Mode status: Active to the record; "
        "close the write, then use workflow_modes_control.py transition discuss --record <active-record> "
        "--user-authorized --marker workflow-modes-v1. Discuss, transition plan on the same bundle, "
        "and obtain approval again before execute. </workflow-anchor>"
    )


def handle_stop(store: StateStore, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    state = store.get(key)
    if not state:
        return None
    if state.get("write_transaction"):
        return {
            "decision": "block",
            "reason": "WORKFLOW_WRITE_CLOSE_REQUIRED: repair and close the active record "
            "write transaction before stopping.",
        }
    if state.get("plan_bootstrap"):
        return {
            "decision": "block",
            "reason": "WORKFLOW_PLAN_ACTIVATION_REQUIRED: finish the declared plan bundle "
            "and activate that exact target before stopping.",
        }
    if state.get("rules_sync_required"):
        return {
            "decision": "block",
            "reason": "WORKFLOW_RULES_SYNC_REQUIRED: reread the mode SKILL.md and required "
            "references, sync the record, and run rules-sync before stopping.",
        }
    if not state.get("action") and state.get("checkpoint_required"):
        return {
            "decision": "block",
            "reason": "WORKFLOW_TURN_CHECKPOINT_REQUIRED: sync the active tracker, persist "
            "material deltas or explicitly confirm no change, then run checkpoint before stopping.",
        }
    if not state.get("action"):
        return None
    if state.get("mode") == "execute":
        return {
            "decision": "block",
            "reason": "WORKFLOW_EXECUTE_RECONCILIATION_REQUIRED: persist terminal evidence "
            "and run action-close before stopping.",
        }
    if state.get("mode") != "discuss":
        return None
    if payload.get("stop_hook_active") or state.get("stop_warning_issued"):
        state["stop_warning_issued"] = False
        store.mutate(key, lambda _old: state)
        return {"systemMessage": "A discuss action is still open; stop allowed to prevent a loop."}
    state["stop_warning_issued"] = True
    store.mutate(key, lambda _old: state)
    return {
        "decision": "block",
        "reason": "WORKFLOW_ACTION_CLOSE_REQUIRED: persist the terminal action result, run "
        "action-close, and return to full discuss behavior before stopping.",
    }


def run(payload: dict[str, Any]) -> dict[str, Any] | None:
    event = str(payload.get("hook_event_name", ""))
    session_id = str(payload.get("session_id", ""))
    if not session_id:
        return None
    key = session_key(session_id)
    store = StateStore()
    if event == "PreToolUse":
        output = handle_pre_tool(store, key, payload)
        if output and output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny":
            field = output["hookSpecificOutput"]
            field["permissionDecisionReason"] = enrich_reason(field["permissionDecisionReason"], payload, store.get(key), parse_control(payload))
        return output
    if event == "UserPromptSubmit":
        state = store.get(key)
        if not state:
            return None
        refresh_sync_requirement(state, force_record=state.get("profile") == "audited")
        state["checkpoint_required"] = True
        state["turn_start_revision"] = state.get("record_revision")
        store.mutate(key, lambda _old: state)
        return context_output(event, mode_message(state))
    if event == "PostCompact":
        state = store.get(key)
        if not state:
            return None
        refresh_sync_requirement(state, force_record=True)
        state["rules_sync_required"] = True
        store.mutate(key, lambda _old: state)
        references = ", ".join(state.get("required_references", [])) or "None"
        return {"systemMessage": (
            mode_message(state) + " Recovery order: (1) activate the current skill and read its "
            "complete SKILL.md; (2) read all Required references: " + references + "; (3) read "
            "and sync the active record using the required scope; (4) run rules-sync before "
            "substantive work or a final response."
        )}
    if event == "Stop":
        output = handle_stop(store, key, payload)
        if output and output.get("decision") == "block":
            output["reason"] = enrich_reason(output["reason"], payload, store.get(key))
        return output
    if event == "SessionEnd":
        store.mutate(key, lambda _old: None)
    return None


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else "PreToolUse"
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict) or not isinstance(payload.get("session_id"), str) or not payload["session_id"]:
            raise ValueError("Expected an object with a nonempty session_id")
        if len(sys.argv) > 1 and payload.get("hook_event_name") != event:
            raise ValueError("Hook event does not match its registration")
        event = str(payload.get("hook_event_name", event))
        if event not in {"PreToolUse", "Stop", "UserPromptSubmit", "PostCompact", "SessionEnd"}:
            event = "PreToolUse"
            raise ValueError("Unsupported hook event")
        output = run(payload)
        if output is not None:
            print(json.dumps(output, separators=(",", ":")))
        return 0
    except BundleError as error:
        reason = f"{error}\nNext: {error.next_step}\nInspect: {control_command('snapshot')}"
        if event == "PreToolUse":
            output = deny_tool(reason)
        elif event == "Stop":
            output = {"decision": "block", "reason": reason}
        else:
            output = {"systemMessage": reason}
        print(json.dumps(output, separators=(",", ":")))
        return 0
    except Exception as error:
        return infrastructure_failure(event, error)


if __name__ == "__main__":
    raise SystemExit(main())
