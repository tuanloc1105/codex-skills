#!/usr/bin/env python3
"""Persist and enforce tracker-backed Kiro workflow modes per session."""

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
SNAPSHOT_START_PATTERN = re.compile(
    r"<!-- workflow-active-snapshot:start version:(?P<version>[12]) -->"
)
SNAPSHOT_END = "<!-- workflow-active-snapshot:end -->"
MANIFEST_START = "<!-- workflow-manifest:start -->"
MANIFEST_END = "<!-- workflow-manifest:end -->"
MAX_RECORD_BYTES = 2 * 1024 * 1024
PROFILES = {"lightweight", "durable", "audited"}
MODES = {"discuss", "plan", "execute"}
MODE_REFERENCES = {
    "discuss": ("references/tracker.md", "references/actions.md"),
    "plan": ("references/plan-record.md", "references/phase-planning.md"),
    "execute": ("references/implementation.md", "references/completion.md"),
}
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
        kiro_home = Path(os.environ.get("KIRO_HOME", Path.home() / ".kiro"))
        root = kiro_home / "workflow-modes" / "state"
        root.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(root / "workflow-modes.sqlite3", timeout=2)
        self.connection.execute("PRAGMA busy_timeout = 2000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "session_key TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        self.connection.commit()

    def __del__(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass

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


def read_index(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    try:
        index = Path(path) / "index.md"
        if not index.is_file() or index.is_symlink() or index.stat().st_size > MAX_RECORD_BYTES:
            return None
        return index.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def manifest_paths(path: str | None, text: str | None = None) -> tuple[str, ...] | None:
    if not isinstance(path, str):
        return None
    text = read_index(path) if text is None else text
    if text is None:
        return None
    if text.count(MANIFEST_START) != 1 or text.count(MANIFEST_END) != 1:
        return None
    start = text.index(MANIFEST_START) + len(MANIFEST_START)
    end = text.index(MANIFEST_END, start)
    entries = tuple(line.strip() for line in text[start:end].splitlines() if line.strip())
    if not entries or entries[0] != "index.md" or len(entries) != len(set(entries)):
        return None
    root = Path(path)
    try:
        resolved_root = root.resolve()
    except OSError:
        return None
    validated: list[str] = []
    total = 0
    for entry in entries:
        relative = Path(entry)
        if relative.is_absolute() or relative.suffix.lower() != ".md" or ".." in relative.parts:
            return None
        candidate = root / relative
        try:
            if not candidate.is_file() or candidate.is_symlink():
                return None
            candidate.resolve().relative_to(resolved_root)
            total += candidate.stat().st_size
        except (OSError, ValueError):
            return None
        if total > MAX_RECORD_BYTES:
            return None
        validated.append(relative.as_posix())
    return tuple(validated)


def record_files(path: str | None) -> dict[str, str] | None:
    text = read_index(path)
    entries = manifest_paths(path, text)
    if text is None or entries is None:
        return None
    root = Path(str(path))
    try:
        actual = {
            candidate.relative_to(root).as_posix()
            for candidate in root.rglob("*.md")
            if candidate.is_file()
        }
    except OSError:
        return None
    if actual != set(entries):
        return None
    files: dict[str, str] = {}
    try:
        for entry in entries:
            files[entry] = (Path(str(path)) / entry).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return files if validate_bundle(files) else None


def validate_bundle(files: dict[str, str]) -> bool:
    index = files.get("index.md", "")
    header = re.search(r"workflow-record[^\n>]*version:4[^\n>]*kind:(discuss|plan)[^\n>]*tracker-id:([^\s>]+)", index)
    if not header:
        return False
    kind = header.group(1)
    required = {"index.md", "context.md", "decisions.md", "evidence.md"}
    required.add("actions.md" if kind == "discuss" else "plan.md")
    if kind == "plan":
        required.add("verification.md")
    if not required.issubset(files):
        return False
    phase_files = sorted(name for name in files if name.startswith("phases/") and name.endswith(".md"))
    phase_ids: dict[str, str] = {}
    dependencies: dict[str, set[str]] = {}
    plan_text = files.get("plan.md", "")
    for name in phase_files:
        filename = Path(name).name
        file_id = filename.split("-", 1)[0]
        match = re.search(r"^#\s+(P\d{2}):\s+.+$", files[name], re.MULTILINE)
        depends = re.search(r"^Depends on:\s*(.*?)\s*$", files[name], re.MULTILINE)
        required_metadata = ("Status:", "Wave:", "Subagent:", "Owned scope:", "Produces:")
        if (
            not match
            or not depends
            or match.group(1) != file_id
            or file_id in phase_ids
            or name not in plan_text
            or missing_markers(files[name], required_metadata)
        ):
            return False
        phase_ids[file_id] = name
        values = set()
        if depends and depends.group(1) != "None":
            values = {item.strip() for item in depends.group(1).split(",") if item.strip()}
        dependencies[file_id] = values
    if any(not values.issubset(phase_ids) for values in dependencies.values()):
        return False
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(phase_id: str) -> bool:
        if phase_id in visiting:
            return False
        if phase_id in visited:
            return True
        visiting.add(phase_id)
        if any(not visit(dependency) for dependency in dependencies.get(phase_id, set())):
            return False
        visiting.remove(phase_id)
        visited.add(phase_id)
        return True

    if any(not visit(phase_id) for phase_id in phase_ids):
        return False
    open_markers = re.findall(r"<!-- workflow-action:([A-Z][A-Z0-9_-]{2,63}) status:open -->", files["evidence.md"])
    active = re.search(r"^Active action:\s*([^\s]+)", index, re.MULTILINE)
    if len(open_markers) > 1 or (open_markers and (not active or active.group(1) != open_markers[0])):
        return False
    if not open_markers and active and active.group(1) != "None":
        return False
    return True


def record_revision(path: str | None) -> str | None:
    files = record_files(path)
    if files is None:
        return None
    return files_revision(files)


def files_revision(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(files[name].encode("utf-8")).digest())
    return "sha256:" + digest.hexdigest()


def content_revision(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_snapshot(text: str | None) -> str | None:
    if text is None or len(SNAPSHOT_START_PATTERN.findall(text)) != 1 or text.count(SNAPSHOT_END) != 1:
        return None
    marker = SNAPSHOT_START_PATTERN.search(text)
    assert marker is not None
    start = marker.end()
    end = text.index(SNAPSHOT_END, start)
    snapshot = text[start:end]
    if len(snapshot.encode("utf-8")) > 64 * 1024:
        return None
    return snapshot


def record_revisions(path: str | None) -> tuple[str | None, str | None, str | None]:
    files = record_files(path)
    if files is None:
        return None, None, None
    text = files["index.md"]
    revision = files_revision(files)
    snapshot = record_snapshot(text)
    if snapshot is None:
        return revision, None, None
    marker = SNAPSHOT_START_PATTERN.search(text)
    assert marker is not None
    index_outside = text[:marker.start()] + text[text.index(SNAPSHOT_END, marker.end()) + len(SNAPSHOT_END):]
    outside_digest = hashlib.sha256(index_outside.encode("utf-8") + b"\0")
    for name in sorted(files):
        if name != "index.md":
            outside_digest.update(name.encode("utf-8"))
            outside_digest.update(b"\0")
            outside_digest.update(hashlib.sha256(files[name].encode("utf-8")).digest())
    return revision, content_revision(snapshot), "sha256:" + outside_digest.hexdigest()


def record_profile(path: str | None) -> str:
    if not isinstance(path, str):
        return "audited"
    snapshot = record_snapshot(read_index(path))
    if snapshot is None:
        return "audited"
    match = re.search(r"^Profile:\s*(\S+)\s*$", snapshot, flags=re.MULTILINE)
    profile = match.group(1).lower() if match else "audited"
    return profile if profile in PROFILES else "audited"


def required_reference_spec(mode: str, text: str | None) -> tuple[tuple[str, ...], bool]:
    """Return the snapshot allowlist, using the full-mode safe legacy fallback."""
    allowed = MODE_REFERENCES[mode]
    snapshot = record_snapshot(text)
    marker = SNAPSHOT_START_PATTERN.search(text or "")
    if snapshot is None or marker is None or marker.group("version") == "1":
        return allowed, True
    match = re.search(r"^Required references:\s*(.*?)\s*$", snapshot, re.MULTILINE)
    if not match:
        return allowed, True
    value = match.group(1)
    if value == "None":
        return (), True
    references = tuple(part.strip() for part in value.split(",") if part.strip())
    if len(references) != len(set(references)) or not set(references).issubset(allowed):
        return allowed, False
    return tuple(reference for reference in allowed if reference in references), True


def required_references(mode: str, text: str | None) -> tuple[str, ...]:
    return required_reference_spec(mode, text)[0]


def refresh_required_references(state: dict[str, Any]) -> bool:
    references, valid = required_reference_spec(
        str(state["mode"]), read_index(str(state.get("record")))
    )
    changed = list(references) != state.get("required_references")
    state["required_references"] = list(references)
    state["required_references_valid"] = valid
    if changed:
        state["rules_sync_required"] = True
    return changed


def record_tracker_id(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    text = read_index(path)
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
        first_script_index = next(
            (
                index for index, token in enumerate(segment)
                if Path(token).name == "workflow_modes_control.py"
            ),
            None,
        )
        script_indexes = [] if first_script_index is None else [first_script_index]
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
            "--unscoped", "--reason", "--scope", "--previous-revision", "--reference",
            "--target",
        } and index + 1 < len(args):
            key = token[2:].replace("-", "_")
            if key == "path":
                result.setdefault("paths", []).append(args[index + 1])
            elif key == "unscoped":
                result.setdefault("unscoped", []).append(args[index + 1])
            elif key == "reference":
                result.setdefault("references", []).append(args[index + 1])
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
        absolute_record = canonical_record(record, cwd) if isinstance(record, str) else None
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
            missing = missing_markers(record_text or "", ("Mode status:",))
            if not any(
                marker in (record_text or "")
                for marker in ("Mode: $discuss", "Mode: /workflow-discuss")
            ):
                missing.append("Mode: /workflow-discuss")
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
                bundle_files = record_files(absolute_record)
                if not bundle_files or not {"plan.md", "verification.md"}.issubset(bundle_files):
                    return deny_tool(
                        "WORKFLOW_HANDOFF_NOT_DURABLE: direct execute requires plan.md and verification.md."
                    )
            else:
                required = ("Status: Approved plan, not yet implemented", "Execute mode: Ready")
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
        if (
            action == "transition"
            and current
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
        if not valid or len(supplied) != len(set(supplied)) or set(supplied) != set(expected):
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
        record = control.get("record")
        if not record_matches(record, current.get("record"), cwd):
            return deny_tool("WORKFLOW_RECORD_MISMATCH: write-close record differs from active bundle.")
        transaction = current.get("write_transaction")
        if not isinstance(transaction, dict):
            return deny_tool("WORKFLOW_WRITE_MISSING: no record write transaction is open.")
        previous = transaction.get("baseline")
        revision, snapshot_revision, outside_revision = record_revisions(
            str(current.get("record"))
        )
        if revision is None or revision == previous:
            return deny_tool(
                "WORKFLOW_WRITE_CLOSE_INVALID: the bundle must be valid and have a new revision."
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
        current["sync_required"] = False
        current["sync_scope"] = None
        current["write_transaction"] = None
        current["profile"] = record_profile(str(current.get("record")))
        refresh_required_references(current)
        current["updated_at"] = utc_now()
        store.mutate(key, lambda _old: current)
        return context_output(
            "PreToolUse",
            f"WORKFLOW_WRITE_CLOSED: mode={current.get('mode')}, "
            f"record={current.get('record')}, revision={revision}.",
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
        current["recovery_pending"] = False
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


def handle_pre_tool(
    store: StateStore,
    key: str,
    payload: dict[str, Any],
    state: dict[str, Any] | None,
) -> dict[str, Any] | None:
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
    if paths:
        requested = {normalized(path, cwd) for path in paths}
        record = str(state.get("record"))
        owned = {
            normalized(str(Path(record) / entry), cwd)
            for entry in (manifest_paths(record) or ())
        }
        record_or_housekeeping = all(
            path in owned
            or (mode != "execute" and Path(path).name == ".gitignore")
            for path in requested
        )
        if record_or_housekeeping:
            if requested & owned:
                return deny_tool(
                    "WORKFLOW_WRITE_OPEN_REQUIRED: open a record write transaction before "
                    "changing manifest-owned Markdown files."
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
        return common + "exit=only plan or execute. </workflow-anchor>"
    if mode == "plan":
        return common + "boundary=source-read-only until execute transition. </workflow-anchor>"
    return common + "exit=explicit request only, including after implementation. </workflow-anchor>"


def handle_stop(store: StateStore, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    state = store.get(key)
    if not state:
        return None
    pending = [
        name
        for name, active in (
            ("write-close", state.get("write_transaction")),
            ("plan-activation", state.get("plan_bootstrap")),
            ("rules-sync", state.get("rules_sync_required")),
            ("action-close", state.get("action")),
            ("checkpoint", state.get("checkpoint_required")),
        )
        if active
    ]
    if not pending:
        return None
    refresh_sync_requirement(state, force_record=True)
    state["rules_sync_required"] = True
    state["recovery_pending"] = True
    state["checkpoint_required"] = True
    state["updated_at"] = utc_now()
    store.mutate(key, lambda _old: state)
    return context_output(
        "Stop",
        "WORKFLOW_STOP_RECOVERY_PENDING: Kiro Stop cannot block. Pending recovery="
        + ",".join(pending)
        + "; the next prompt/tool boundary denies mutation until record and rules "
        "synchronization, terminal action/write repair, and checkpoint complete.",
    )


EVENT_ALIASES = {
    "sessionstart": "SessionStart",
    "agentspawn": "SessionStart",
    "userpromptsubmit": "UserPromptSubmit",
    "promptsubmit": "UserPromptSubmit",
    "pretooluse": "PreToolUse",
    "stop": "Stop",
    "agentstop": "Stop",
}


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload = dict(payload)
    aliases = {
        "sessionId": "session_id",
        "hookEventName": "hook_event_name",
        "eventName": "hook_event_name",
        "toolName": "tool_name",
        "toolInput": "tool_input",
        "workingDirectory": "cwd",
    }
    for source, target in aliases.items():
        if target not in normalized_payload and source in normalized_payload:
            normalized_payload[target] = normalized_payload[source]
    raw_event = str(normalized_payload.get("hook_event_name", ""))
    event_key = re.sub(r"[^a-z]", "", raw_event.lower())
    normalized_payload["hook_event_name"] = EVENT_ALIASES.get(event_key, raw_event)
    return normalized_payload


def project_owns_workflow(cwd: str) -> bool:
    if os.environ.get("KIRO_WORKFLOW_SCOPE") != "global":
        return False
    current = Path(cwd).resolve(strict=False)
    for candidate in (current, *current.parents):
        if (candidate / ".kiro" / "workflow-modes" / "project-owned").is_file():
            return True
    return False


def run(payload: dict[str, Any]) -> dict[str, Any] | None:
    payload = normalize_payload(payload)
    event = str(payload.get("hook_event_name", ""))
    session_id = str(payload.get("session_id", ""))
    if not session_id:
        return None
    cwd = str(payload.get("cwd", os.getcwd()))
    if project_owns_workflow(cwd):
        return None
    key = session_key(session_id)
    store = StateStore()
    if event == "PreToolUse":
        control = parse_control(payload)
        if control:
            return handle_control(store, key, payload, control)
        state = store.get(key)
        result = handle_pre_tool(store, key, payload, state)
        if result is not None:
            return result
        return context_output(event, mode_message(state)) if state else None
    if event == "UserPromptSubmit":
        state = store.get(key)
        if not state:
            return None
        refresh_sync_requirement(state, force_record=state.get("profile") == "audited")
        state["checkpoint_required"] = True
        state["turn_start_revision"] = state.get("record_revision")
        store.mutate(key, lambda _old: state)
        return context_output(event, mode_message(state))
    if event == "SessionStart":
        state = store.get(key)
        if not state:
            return None
        refresh_sync_requirement(state)
        store.mutate(key, lambda _old: state)
        return context_output(event, mode_message(state))
    if event == "Stop":
        return handle_stop(store, key, payload)
    return None


def render_kiro(output: dict[str, Any] | None) -> tuple[int, str, str]:
    if output is None:
        return 0, "", ""
    specific = output.get("hookSpecificOutput")
    if isinstance(specific, dict):
        reason = specific.get("permissionDecisionReason")
        if specific.get("permissionDecision") == "deny" and isinstance(reason, str):
            return 2, "", reason
        context = specific.get("additionalContext")
        if isinstance(context, str):
            return 0, context, ""
    for key in ("systemMessage", "reason"):
        message = output.get(key)
        if isinstance(message, str):
            return 0, message, ""
    return 0, "", ""


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
        if isinstance(payload, dict):
            code, stdout, stderr = render_kiro(run(payload))
            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)
            return code
        return 0
    except Exception as error:
        print(f"Workflow Modes hook failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
