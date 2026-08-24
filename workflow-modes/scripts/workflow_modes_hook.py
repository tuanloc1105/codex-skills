#!/usr/bin/env python3
"""Persist and enforce tracker-backed Codex workflow modes per session."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import sys
import tempfile
import time
from typing import Any, Callable


MARKER = "workflow-modes-v1"
MODES = {"discuss", "plan", "execute"}
GIT_MUTATION_COMMANDS = "add|commit|push|merge|rebase|reset|clean|checkout|switch|restore"
GIT_MUTATION_PATTERN = rf"\bgit\s+(?:{GIT_MUTATION_COMMANDS})\b"
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


def read_record(path: str) -> str | None:
    try:
        record = Path(path)
        if not record.is_file() or record.stat().st_size > 2 * 1024 * 1024:
            return None
        return record.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def record_revision(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    text = read_record(path)
    if text is None:
        return None
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_tracker_id(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    text = read_record(path)
    if text is None:
        return None
    header = re.search(r"workflow-record[^\n>]*tracker-id:([^\s>]+)", text)
    if header:
        return header.group(1)
    metadata = re.search(r"^Tracker ID:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    return metadata.group(1) if metadata else None


def contains_evidence_id(text: str, evidence_id: str) -> bool:
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_-]){re.escape(evidence_id)}(?![A-Za-z0-9_-])",
            text,
        )
    )


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
    try:
        lexer = shlex.shlex(
            tool_command(payload), posix=True, punctuation_chars=";&|"
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return None

    segments: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= {";", "&", "|"}:
            segments.append([])
        else:
            segments[-1].append(token)

    candidates: list[tuple[list[str], int, int]] = []
    for segment in segments:
        script_indexes = [
            index for index, token in enumerate(segment)
            if Path(token).name == "workflow_modes_control.py"
        ]
        for script_index in script_indexes:
            try:
                marker_index = segment.index("--marker", script_index + 1)
            except ValueError:
                continue
            if marker_index + 1 < len(segment) and segment[marker_index + 1] == MARKER:
                candidates.append((segment, script_index, marker_index))

    if not candidates:
        return None
    if len(candidates) > 1:
        return {"action": "ambiguous"}

    segment, script_index, marker_index = candidates[0]
    args = segment[script_index + 1:marker_index]
    if not args:
        return None
    result: dict[str, Any] = {"action": args[0]}
    positionals: list[str] = []
    index = 1
    while index < len(args):
        token = args[index]
        if token in {
            "--record", "--path", "--result", "--impact", "--evidence-id",
            "--unscoped", "--reason",
        } and index + 1 < len(args):
            key = token[2:].replace("-", "_")
            if key == "path":
                result.setdefault("paths", []).append(args[index + 1])
            elif key == "unscoped":
                result.setdefault("unscoped", []).append(args[index + 1])
            else:
                result[key] = args[index + 1]
            index += 2
        elif token == "--no-change":
            result["no_change"] = True
            index += 1
        else:
            positionals.append(token)
            index += 1
    result["positionals"] = positionals
    return result


def state_summary(state: dict[str, Any]) -> str:
    action = state.get("action")
    action_text = "none" if not action else str(action.get("status", "unknown"))
    return (
        f"mode={state.get('mode')}, record={state.get('record')}, "
        f"action={action_text}"
    )


def mark_sync_required(state: dict[str, Any]) -> None:
    current_revision = record_revision(state.get("record"))
    state["record_revision"] = current_revision
    state["sync_required"] = bool(state.get("record"))


def record_is_synced(state: dict[str, Any]) -> bool:
    current_revision = record_revision(state.get("record"))
    state["record_revision"] = current_revision
    return bool(
        current_revision
        and not state.get("sync_required")
        and state.get("acknowledged_revision") == current_revision
    )


def handle_control(
    store: StateStore, key: str, payload: dict[str, Any], control: dict[str, Any]
) -> dict[str, Any] | None:
    action = control.get("action")
    if action == "ambiguous":
        return deny_tool(
            "WORKFLOW_CONTROL_AMBIGUOUS: run only one marker-backed lifecycle control "
            "request per tool call."
        )
    cwd = str(payload.get("cwd", os.getcwd()))
    current = store.get(key)
    if action in {"activate", "transition"}:
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
        absolute_record = normalized(record, cwd) if isinstance(record, str) else None
        record_text = read_record(absolute_record) if absolute_record else None
        if mode in {"discuss", "execute"} and record_text is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
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
            allowed = {
                "discuss": {"plan", "execute"},
                "plan": {"execute"},
                "execute": set(),
            }
            if mode not in allowed.get(str(current.get("mode")), set()):
                return deny_tool(
                    f"WORKFLOW_TRANSITION_DENIED: {current.get('mode')} cannot transition to {mode}."
                )
            if record_text is None:
                return deny_tool("WORKFLOW_RECORD_UNREADABLE: transition record is not readable.")
            if current.get("mode") == "discuss" and mode == "plan":
                required = ("Mode status: Exited",)
            elif current.get("mode") == "discuss" and mode == "execute":
                required = (
                    "Mode status: Exited",
                    "Execution readiness: Ready",
                    "Execute mode: Ready",
                )
            else:
                required = ("Status: Approved plan, not yet implemented", "Execute mode: Ready")
            missing = missing_markers(record_text, required)
            if missing:
                return deny_tool(
                    "WORKFLOW_HANDOFF_NOT_DURABLE: record lacks required markers: "
                    + ", ".join(missing)
                )
        state = {
            "active": True,
            "mode": mode,
            "record": absolute_record,
            "action": None,
            "stop_warning_issued": False,
            "record_revision": record_revision(absolute_record),
            "tracker_id": record_tracker_id(absolute_record),
            "acknowledged_revision": None,
            "sync_required": bool(absolute_record),
            "checkpoint_required": False,
            "turn_start_revision": record_revision(absolute_record),
            "updated_at": utc_now(),
        }
        store.mutate(key, lambda _old: state)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_MODE_ACTIVE: {state_summary(state)}. The tracker is authoritative; "
            "read and reconcile it before substantive work.",
        )
    if action == "deactivate":
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
        return deny_tool("WORKFLOW_MODE_INACTIVE: activate a tracker-backed mode first.")
    if action == "sync":
        record = control.get("record")
        if not isinstance(record, str) or normalized(record, cwd) != current.get("record"):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: sync record differs from active tracker.")
        revision = record_revision(str(current.get("record")))
        if revision is None:
            return deny_tool("WORKFLOW_RECORD_UNREADABLE: the tracker must exist and be readable.")
        tracker_id = record_tracker_id(str(current.get("record")))
        if current.get("tracker_id") and tracker_id != current.get("tracker_id"):
            return deny_tool(
                "WORKFLOW_RECORD_IDENTITY_MISMATCH: the active path now contains a different "
                "tracker ID; restore the record or explicitly rebind the workflow."
            )
        current["tracker_id"] = tracker_id or current.get("tracker_id")
        current["record_revision"] = revision
        current["acknowledged_revision"] = revision
        current["sync_required"] = False
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_RECORD_SYNCED: mode={current.get('mode')}, "
            f"record={current.get('record')}, revision={revision}.",
        )
    if action == "checkpoint":
        record = control.get("record")
        if not isinstance(record, str) or normalized(record, cwd) != current.get("record"):
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
        if current.get("action"):
            return deny_tool(
                "WORKFLOW_ACTION_CLOSE_REQUIRED: close the active action before checkpointing."
            )
        current["record_revision"] = current_revision
        changed = current_revision != current.get("turn_start_revision")
        if not changed and current.get("acknowledged_revision") != current_revision:
            current["sync_required"] = True
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
        return context_output("PreToolUse", f"WORKFLOW_MODE_SNAPSHOT: {state_summary(current)}.")
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
        if not isinstance(record, str) or normalized(record, cwd) != current.get("record"):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: action record differs from active tracker.")
        record_text = read_record(str(current.get("record")))
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
            record_text = read_record(str(current.get("record")))
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
        if read_record(str(current.get("record"))) is not None:
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
    if isinstance(record, str) and absolute == record:
        return True
    if state.get("mode") != "execute" and Path(absolute).name == ".gitignore":
        return True
    if state.get("mode") == "plan" and Path(absolute).suffix.lower() == ".md":
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
    if paths and all(record_or_housekeeping_path(path, state, cwd) for path in paths):
        return None
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
    if action.get("impact") == "non-source":
        return None
    return deny_tool(
        "WORKFLOW_ACTION_UNSCOPED_TOOL: mutating tools without inspectable file targets are "
        "blocked during a temporary discuss action. Use a file-scoped tool or transition to execute."
    )


def mode_message(state: dict[str, Any]) -> str:
    mode = state.get("mode")
    common = (
        "<workflow-anchor version=\"2\"> "
        f"mode={mode}; record={state.get('record')}; tracker_id={state.get('tracker_id')}; "
        f"record_revision={state.get('record_revision')}; sync_status=required; "
        "rule=read the exact tracker completely, then run sync before substantive work; "
        "rule=persist material turn changes and run checkpoint before final response. "
    )
    if mode == "discuss":
        return common + "exit=only plan or execute. </workflow-anchor>"
    if mode == "plan":
        return common + "boundary=source-read-only until execute transition. </workflow-anchor>"
    return common + "exit=explicit request only, including after implementation. </workflow-anchor>"


def handle_stop(store: StateStore, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    state = store.get(key)
    if not state:
        return None
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
        return handle_pre_tool(store, key, payload)
    if event == "UserPromptSubmit":
        state = store.get(key)
        if not state:
            return None
        mark_sync_required(state)
        state["checkpoint_required"] = True
        state["turn_start_revision"] = state.get("record_revision")
        store.mutate(key, lambda _old: state)
        return context_output(event, mode_message(state))
    if event == "PostCompact":
        state = store.get(key)
        if not state:
            return None
        mark_sync_required(state)
        store.mutate(key, lambda _old: state)
        return {"systemMessage": mode_message(state)}
    if event == "Stop":
        return handle_stop(store, key, payload)
    if event == "SessionEnd":
        store.mutate(key, lambda _old: None)
    return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
        if isinstance(payload, dict):
            output = run(payload)
            if output is not None:
                print(json.dumps(output, separators=(",", ":")))
        return 0
    except Exception as error:
        print(f"Workflow Modes hook failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
