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
MUTATING_SHELL = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:rm|mv|cp|mkdir|touch|chmod|chown|install)\b"
    r"|\bgit\s+(?:add|commit|push|merge|rebase|reset|clean|checkout|switch)\b"
    r"|\b(?:npm|pnpm|yarn|pip|pip3|uv)\s+(?:install|uninstall|add|remove|publish)\b"
    r"|\b(?:docker|podman)\s+(?:build|push|run|compose\s+up)\b"
    r"|\bkubectl\s+(?:apply|create|delete|patch|replace|scale|set)\b"
    r"|\bterraform\s+(?:apply|destroy|import)\b"
    r"|(?:^|[^>])>{1,2}(?!>)",
    re.IGNORECASE,
)
MUTATING_TOOL_VERBS = {
    "add", "archive", "commit", "create", "delete", "deploy", "edit",
    "install", "move", "publish", "push", "remove", "rename", "send",
    "set", "update", "write",
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
        tokens = shlex.split(tool_command(payload))
    except ValueError:
        return None
    try:
        script_index = next(
            index for index, token in enumerate(tokens)
            if Path(token).name == "workflow_modes_control.py"
        )
    except StopIteration:
        return None
    if "--marker" not in tokens:
        return None
    marker_index = tokens.index("--marker")
    if marker_index + 1 >= len(tokens) or tokens[marker_index + 1] != MARKER:
        return None
    args = tokens[script_index + 1:marker_index]
    if not args:
        return None
    result: dict[str, Any] = {"action": args[0]}
    positionals: list[str] = []
    index = 1
    while index < len(args):
        token = args[index]
        if token in {"--record", "--path", "--result", "--impact"} and index + 1 < len(args):
            key = token[2:].replace("-", "_")
            if key == "path":
                result.setdefault("paths", []).append(args[index + 1])
            else:
                result[key] = args[index + 1]
            index += 2
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


def handle_control(
    store: StateStore, key: str, payload: dict[str, Any], control: dict[str, Any]
) -> dict[str, Any] | None:
    action = control.get("action")
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
            "updated_at": utc_now(),
        }
        store.mutate(key, lambda _old: state)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_MODE_ACTIVE: {state_summary(state)}. The tracker is authoritative; "
            "read and reconcile it before substantive work.",
        )
    if action == "deactivate":
        if current and current.get("mode") != "execute":
            return deny_tool(
                "WORKFLOW_EXIT_DENIED: discuss and plan exit only through a valid plan/execute transition."
            )
        store.mutate(key, lambda _old: None)
        return context_output("PreToolUse", "WORKFLOW_MODE_INACTIVE: execute explicitly exited.")
    if not current:
        return deny_tool("WORKFLOW_MODE_INACTIVE: activate a tracker-backed mode first.")
    if action == "snapshot":
        return context_output("PreToolUse", f"WORKFLOW_MODE_SNAPSHOT: {state_summary(current)}.")
    if action == "action-open":
        if current.get("mode") != "discuss":
            return deny_tool("WORKFLOW_ACTION_DENIED: scoped actions belong to discuss mode.")
        record = control.get("record")
        if not isinstance(record, str) or normalized(record, cwd) != current.get("record"):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: action record differs from active tracker.")
        impact = control.get("impact")
        if impact not in {"non-source", "source-confirmed"}:
            return deny_tool("WORKFLOW_ACTION_INVALID: --impact must classify source impact.")
        paths = [normalized(path, cwd) for path in control.get("paths", [])]
        current["action"] = {
            "status": "authorized",
            "paths": sorted(set(paths)),
            "impact": impact,
            "opened_at": utc_now(),
        }
        current["stop_warning_issued"] = False
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            "WORKFLOW_ACTION_OPEN: bounded discuss action authorized; close it after persisting "
            "the terminal result, then resume full discuss behavior.",
        )
    if action == "action-close":
        if current.get("mode") != "discuss" or not current.get("action"):
            return deny_tool("WORKFLOW_ACTION_MISSING: no discuss action is open.")
        current["action"] = None
        current["stop_warning_issued"] = False
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_ACTION_CLOSED: result={control.get('result')}; full discuss guardrails restored.",
        )
    return deny_tool("WORKFLOW_CONTROL_INVALID: unsupported lifecycle action.")


def record_or_housekeeping_path(path: str, state: dict[str, Any], cwd: str) -> bool:
    absolute = normalized(path, cwd)
    record = state.get("record")
    if isinstance(record, str) and absolute == record:
        return True
    if Path(absolute).name == ".gitignore":
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
    if mode == "execute":
        return None
    cwd = str(payload.get("cwd", os.getcwd()))
    paths = paths_for_tool(payload)
    if paths and all(record_or_housekeeping_path(path, state, cwd) for path in paths):
        return None
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
        if not requested.issubset(allowed_paths | {str(state.get("record"))}):
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
    if action.get("impact") == "non-source":
        return None
    return deny_tool(
        "WORKFLOW_ACTION_UNSCOPED_TOOL: mutating tools without inspectable file targets are "
        "blocked during a temporary discuss action. Use a file-scoped tool or transition to execute."
    )


def mode_message(state: dict[str, Any]) -> str:
    mode = state.get("mode")
    common = (
        f"WORKFLOW_MODE_ACTIVE after context boundary: {state_summary(state)}. "
        "Read the exact tracker completely and reconcile it before substantive work. "
    )
    if mode == "discuss":
        return common + (
            "Discuss remains active across scoped actions; only plan or execute may durably exit it."
        )
    if mode == "plan":
        return common + "Plan remains source-read-only until an explicit execute transition."
    return common + (
        "Execute remains active after implementation completion and exits only on explicit request."
    )


def handle_stop(store: StateStore, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    state = store.get(key)
    if not state or state.get("mode") != "discuss" or not state.get("action"):
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
        return context_output(event, mode_message(state)) if state else None
    if event == "PostCompact":
        state = store.get(key)
        return {"systemMessage": mode_message(state)} if state else None
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
