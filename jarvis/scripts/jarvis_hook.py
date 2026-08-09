#!/usr/bin/env python3
"""Dormant lifecycle guardrails for explicitly activated Jarvis sessions."""

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


MARKER = "jarvis-explicit-v1"
RECENT_EVENT_LIMIT = 20
DEFAULT_SCOPE_LIMIT = 5

FAILURE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\btraceback \(most recent call last\)",
        r"\bpermission denied\b",
        r"\bno such file or directory\b",
        r"\bcommand not found\b",
        r"\btimed? out\b",
        r"\btests? failed\b",
        r"\bfailed tests?\b",
        r"\buncaught (?:exception|error)\b",
    )
)

MUTATING_SHELL = re.compile(
    r"(?:^|[;&|]\s*|\s)"
    r"(?:rm|mv|cp|mkdir|touch|chmod|chown|install)\b"
    r"|\bgit\s+(?:add|commit|push|merge|rebase|reset|clean|checkout|switch)\b"
    r"|\b(?:npm|pnpm|yarn|pip|pip3|uv)\s+(?:install|uninstall|add|remove|publish)\b"
    r"|\b(?:docker|podman)\s+(?:build|push|run|compose\s+up)\b"
    r"|\bkubectl\s+(?:apply|create|delete|patch|replace|scale|set)\b"
    r"|\bterraform\s+(?:apply|destroy|import)\b"
    r"|(?:^|[^>])>{1,2}(?!>)",
    re.IGNORECASE,
)

MUTATING_TOOL_VERBS = {
    "add",
    "archive",
    "commit",
    "create",
    "delete",
    "deploy",
    "edit",
    "install",
    "move",
    "publish",
    "push",
    "remove",
    "rename",
    "send",
    "set",
    "update",
    "write",
}

COORDINATION_TOOLS = {
    "agent",
    "followup_task",
    "get_goal",
    "interrupt_agent",
    "list_agents",
    "request_user_input",
    "send_message",
    "spawn_agent",
    "update_goal",
    "update_plan",
    "wait_agent",
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def session_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def default_state() -> dict[str, Any]:
    return {
        "active": True,
        "activated_at": utc_now(),
        "baseline_ready": False,
        "final_approved": False,
        "stuck": False,
        "failure_score": 0,
        "total_failures": 0,
        "touched_files": [],
        "scope_limit": DEFAULT_SCOPE_LIMIT,
        "pending_scope_count": 0,
        "stop_continuation_issued": False,
        "recent_events": [],
    }


class StateStore:
    def __init__(self) -> None:
        root = Path(
            os.environ.get("PLUGIN_DATA")
            or Path(tempfile.gettempdir()) / "jarvis-plugin-data"
        )
        root.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(root / "jarvis-state.sqlite3", timeout=2)
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
            current = self.get(key)
            updated = callback(current)
            if updated is None:
                self.connection.execute(
                    "DELETE FROM sessions WHERE session_key = ?", (key,)
                )
            else:
                self.connection.execute(
                    "INSERT INTO sessions(session_key, state_json, updated_at) "
                    "VALUES(?, ?, ?) ON CONFLICT(session_key) DO UPDATE SET "
                    "state_json = excluded.state_json, updated_at = excluded.updated_at",
                    (key, json.dumps(updated, sort_keys=True), utc_now()),
                )
            self.connection.commit()
            return updated
        except Exception:
            self.connection.rollback()
            raise

    def delete(self, key: str) -> None:
        self.mutate(key, lambda _state: None)


def emit(payload: dict[str, Any] | None = None) -> None:
    if payload is not None:
        print(json.dumps(payload, separators=(",", ":")))


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


def add_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    events = list(state.get("recent_events", []))
    events.append({"at": utc_now(), **event})
    state["recent_events"] = events[-RECENT_EVENT_LIMIT:]


def tool_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        return command if isinstance(command, str) else ""
    return ""


def parse_control_call(payload: dict[str, Any]) -> tuple[str, str | None] | None:
    if str(payload.get("tool_name", "")).lower() != "bash":
        return None
    command = tool_command(payload)
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    try:
        script_index = next(
            index
            for index, token in enumerate(tokens)
            if Path(token).name == "jarvis_control.py"
        )
    except StopIteration:
        return None
    if "--marker" not in tokens:
        return None
    marker_index = tokens.index("--marker")
    if marker_index + 1 >= len(tokens) or tokens[marker_index + 1] != MARKER:
        return None
    if script_index + 1 >= len(tokens):
        return None
    action = tokens[script_index + 1]
    detail = tokens[script_index + 2] if action == "checkpoint" else None
    valid = {
        "activate": None,
        "approve-final": None,
        "deactivate": None,
        "snapshot": None,
        "checkpoint": {"baseline", "scope", "rescue"},
    }
    if action not in valid:
        return None
    if action == "checkpoint" and detail not in valid[action]:
        return None
    return action, detail


def touched_files(command: str) -> set[str]:
    paths = set(
        re.findall(
            r"^\*\*\* (?:Add|Update|Delete) File: (.+)$",
            command,
            flags=re.MULTILINE,
        )
    )
    paths.update(
        re.findall(r"^\*\*\* Move to: (.+)$", command, flags=re.MULTILINE)
    )
    return {path.strip() for path in paths if path.strip()}


def is_mutating_tool(payload: dict[str, Any]) -> bool:
    name = str(payload.get("tool_name", ""))
    lowered = name.lower()
    if lowered in COORDINATION_TOOLS:
        return False
    if lowered == "apply_patch":
        return True
    if lowered == "bash":
        return bool(MUTATING_SHELL.search(tool_command(payload)))
    parts = {part for part in re.split(r"[_\W]+", lowered) if part}
    return bool(parts & MUTATING_TOOL_VERBS)


def collect_exit_codes(value: Any) -> list[int]:
    codes: list[int] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"exit_code", "exitCode"} and isinstance(child, int):
                codes.append(child)
            else:
                codes.extend(collect_exit_codes(child))
    elif isinstance(value, list):
        for child in value:
            codes.extend(collect_exit_codes(child))
    return codes


def response_failed(response: Any) -> bool:
    if isinstance(response, dict) and response.get("isError") is True:
        return True
    exit_codes = collect_exit_codes(response)
    if any(code != 0 for code in exit_codes):
        return True
    text = json.dumps(response, ensure_ascii=False, default=str)[:8000]
    return any(pattern.search(text) for pattern in FAILURE_PATTERNS)


def state_summary(state: dict[str, Any]) -> str:
    recent_failures = sum(
        1 for event in state.get("recent_events", [])[-8:] if event.get("failed")
    )
    return (
        f"baseline={'ready' if state.get('baseline_ready') else 'missing'}, "
        f"stuck={'yes' if state.get('stuck') else 'no'}, "
        f"recent_failures={recent_failures}, "
        f"touched_files={len(state.get('touched_files', []))}, "
        f"scope_limit={state.get('scope_limit', DEFAULT_SCOPE_LIMIT)}, "
        f"final={'approved' if state.get('final_approved') else 'pending'}"
    )


def handle_user_prompt(
    store: StateStore, key: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    prompt = str(payload.get("prompt", ""))
    invoked = re.search(r"(?<![\w-])\$jarvis(?![\w-])", prompt, re.IGNORECASE)
    if invoked and re.search(r"\$jarvis\s+(?:off|stop|disable)\b", prompt, re.IGNORECASE):
        store.delete(key)
        return context_output(
            "UserPromptSubmit", "Jarvis supervision was explicitly deactivated."
        )
    if invoked:
        state = store.mutate(key, lambda _state: default_state())
        return context_output(
            "UserPromptSubmit",
            "JARVIS_ACTIVE: Spawn exactly one frontier Jarvis supervisor, obtain its "
            "baseline verdict, and complete the baseline checkpoint before mutation. "
            f"Hook state: {state_summary(state or default_state())}.",
        )
    state = store.get(key)
    if not state:
        return None
    return context_output(
        "UserPromptSubmit",
        "JARVIS_ACTIVE: Reuse the existing supervisor and preserve the goal contract. "
        f"Hook state: {state_summary(state)}.",
    )


def handle_control(
    store: StateStore,
    key: str,
    event: str,
    control: tuple[str, str | None],
) -> dict[str, Any] | None:
    action, detail = control
    if action == "activate":
        state = store.mutate(key, lambda current: current or default_state())
        return context_output(
            event,
            "JARVIS_ACTIVE: Explicit activation confirmed. Spawn and consult the "
            "frontier supervisor before material mutation. "
            f"Hook state: {state_summary(state or default_state())}.",
        )
    if action == "deactivate":
        store.delete(key)
        return context_output(event, "Jarvis supervision explicitly deactivated.")

    state = store.get(key)
    if not state:
        return deny_tool(
            "Jarvis control was requested without an active session. Invoke $jarvis first."
        )
    if action == "snapshot":
        return context_output(event, f"JARVIS_SNAPSHOT: {state_summary(state)}.")

    def update(current: dict[str, Any] | None) -> dict[str, Any]:
        current = current or default_state()
        if action == "approve-final":
            current["final_approved"] = True
            add_event(current, {"event": "final-approved"})
        elif detail == "baseline":
            current["baseline_ready"] = True
            current["scope_limit"] = max(
                DEFAULT_SCOPE_LIMIT,
                len(current.get("touched_files", [])) + DEFAULT_SCOPE_LIMIT,
            )
            add_event(current, {"event": "baseline-ready"})
        elif detail == "scope":
            current["scope_limit"] = max(
                len(current.get("touched_files", [])) + DEFAULT_SCOPE_LIMIT,
                int(current.get("pending_scope_count", 0)),
            )
            current["pending_scope_count"] = 0
            add_event(current, {"event": "scope-reviewed"})
        elif detail == "rescue":
            current["stuck"] = False
            current["failure_score"] = 0
            add_event(current, {"event": "rescue-reviewed"})
        return current

    updated = store.mutate(key, update) or state
    label = "final approval" if action == "approve-final" else f"{detail} checkpoint"
    return context_output(
        event, f"JARVIS_CHECKPOINT: Recorded {label}. {state_summary(updated)}."
    )


def handle_pre_tool(
    store: StateStore, key: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    control = parse_control_call(payload)
    if control:
        return handle_control(store, key, "PreToolUse", control)
    state = store.get(key)
    if not state:
        return None

    mutating = is_mutating_tool(payload)
    if mutating and not state.get("baseline_ready"):
        return deny_tool(
            "JARVIS_BASELINE_REQUIRED: Obtain READY from the Jarvis supervisor and "
            "record the baseline checkpoint before mutation."
        )
    if mutating and state.get("stuck"):
        return deny_tool(
            "JARVIS_STUCK: Mutation is paused. Ask the Jarvis supervisor for a ranked "
            "diagnosis, follow the narrowest falsification step, obtain RESUME, then "
            "record the rescue checkpoint."
        )

    paths = touched_files(tool_command(payload))
    if mutating and paths:
        existing = set(state.get("touched_files", []))
        projected = len(existing | paths)
        if projected > int(state.get("scope_limit", DEFAULT_SCOPE_LIMIT)):
            def mark_scope(current: dict[str, Any] | None) -> dict[str, Any]:
                current = current or state
                current["pending_scope_count"] = max(
                    projected, int(current.get("pending_scope_count", 0))
                )
                return current

            store.mutate(key, mark_scope)
            return deny_tool(
                "JARVIS_SCOPE_REVIEW: This mutation crosses the current touched-file "
                "budget. Ask Jarvis whether the expansion is necessary and user-authorized, "
                "then record the scope checkpoint."
            )
    return None


def handle_post_tool(
    store: StateStore, key: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    state = store.get(key)
    if not state:
        return None
    failed = response_failed(payload.get("tool_response"))
    paths = touched_files(tool_command(payload))
    became_stuck = False

    def update(current: dict[str, Any] | None) -> dict[str, Any]:
        nonlocal became_stuck
        current = current or state
        was_stuck = bool(current.get("stuck"))
        score = int(current.get("failure_score", 0))
        if failed:
            score += 2
            current["total_failures"] = int(current.get("total_failures", 0)) + 1
        else:
            score = max(0, score - 1)
            if paths:
                current["touched_files"] = sorted(
                    set(current.get("touched_files", [])) | paths
                )
        current["failure_score"] = score
        add_event(
            current,
            {
                "event": "tool-result",
                "tool": str(payload.get("tool_name", "unknown")),
                "failed": failed,
                "paths": sorted(paths)[:10],
            },
        )
        recent_failures = sum(
            1
            for event in current.get("recent_events", [])[-8:]
            if event.get("failed")
        )
        current["stuck"] = was_stuck or score >= 4 or recent_failures >= 3
        became_stuck = not was_stuck and bool(current["stuck"])
        return current

    updated = store.mutate(key, update) or state
    if became_stuck:
        return context_output(
            "PostToolUse",
            "JARVIS_STUCK: Repeated failure signals indicate the primary agent may be "
            "thrashing. Pause mutation, send compact failure evidence to Jarvis, request "
            "a ranked diagnosis and falsification step, and obtain RESUME before recording "
            f"the rescue checkpoint. Hook state: {state_summary(updated)}.",
        )
    return None


def handle_stop(
    store: StateStore, key: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    state = store.get(key)
    if not state:
        return None
    if state.get("final_approved"):
        store.delete(key)
        return None
    if payload.get("stop_hook_active") or state.get("stop_continuation_issued"):
        store.delete(key)
        return {
            "systemMessage": "Jarvis final approval is still missing; the second stop is "
            "allowed only to prevent an infinite continuation loop."
        }

    def mark_continuation(current: dict[str, Any] | None) -> dict[str, Any]:
        current = current or state
        current["stop_continuation_issued"] = True
        return current

    store.mutate(key, mark_continuation)
    return {
        "decision": "block",
        "reason": "JARVIS_FINAL_REVIEW_REQUIRED: Send the goal contract, result, checks, "
        "and residual risk to the Jarvis supervisor. Address CHANGES_REQUESTED. After PASS, "
        "record approve-final before stopping."
    }


def run(payload: dict[str, Any]) -> dict[str, Any] | None:
    event = str(payload.get("hook_event_name", ""))
    session_id = str(payload.get("session_id", ""))
    if not session_id:
        return None
    key = session_key(session_id)
    store = StateStore()
    if event == "UserPromptSubmit":
        return handle_user_prompt(store, key, payload)
    if event == "PreToolUse":
        return handle_pre_tool(store, key, payload)
    if event == "PostToolUse":
        return handle_post_tool(store, key, payload)
    if event == "PostCompact":
        state = store.get(key)
        if state:
            return {
                "systemMessage": "Jarvis supervision remains active after compaction: "
                + state_summary(state)
            }
        return None
    if event == "Stop":
        return handle_stop(store, key, payload)
    if event == "SessionEnd":
        store.delete(key)
    return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        emit(run(payload))
        return 0
    except Exception as error:
        print(f"Jarvis hook failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
