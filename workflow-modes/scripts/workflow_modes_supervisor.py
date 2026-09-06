#!/usr/bin/env python3
"""Independent startup boundary. Intentionally does not import the hook or SQLite."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

EVENTS = {"PreToolUse", "Stop", "UserPromptSubmit", "PostCompact", "SessionEnd"}


def fail(event: str, code: str, detail: str) -> int:
    message = (
        f"{code}: event={event}; {detail}\n"
        "Next: from a terminal outside this task, check python3 (Windows: py -3), "
        "PLUGIN_ROOT/scripts and PLUGIN_DATA access. Ask the owner to restore missing "
        "runtime files/dependencies; close tasks using an old cache before any requested reinstall. "
        "Do not edit hook scripts, delete the database, or retry lifecycle mutations blindly. "
        "After enforcement is healthy, run snapshot before retrying an uncertain request. "
        "Report this blocker; implementation must wait."
    )
    print(message, file=sys.stderr)
    if event == "PreToolUse":
        return 2
    print(json.dumps({"systemMessage": message}))
    return 0


def valid_output(output: dict, event: str) -> bool:
    if set(output) - {"hookSpecificOutput", "systemMessage", "decision", "reason"}:
        return False
    if event == "PreToolUse" and set(output).intersection({"continue", "stopReason", "suppressOutput"}):
        return False
    specific = output.get("hookSpecificOutput")
    if specific is not None:
        if not isinstance(specific, dict) or specific.get("hookEventName") != event:
            return False
        if set(specific) - {"hookEventName", "additionalContext", "permissionDecision", "permissionDecisionReason"}:
            return False
        if event == "PreToolUse":
            if specific.get("permissionDecision") not in (None, "deny"):
                return False
            if specific.get("permissionDecision") == "deny" and (not isinstance(specific.get("permissionDecisionReason"), str) or not specific["permissionDecisionReason"].strip()):
                return False
        elif "permissionDecision" in specific or "permissionDecisionReason" in specific:
            return False
        if "additionalContext" in specific and not isinstance(specific["additionalContext"], str):
            return False
    if "decision" in output:
        if event != "Stop" or output["decision"] != "block" or not isinstance(output.get("reason"), str):
            return False
    return "systemMessage" not in output or isinstance(output["systemMessage"], str)


def main() -> int:
    event = sys.argv[1] if len(sys.argv) == 2 and sys.argv[1] in EVENTS else "PreToolUse"
    if len(sys.argv) != 2 or sys.argv[1] not in EVENTS:
        return fail(event, "WORKFLOW_HOOK_EVENT_INVALID", "Launcher must pass its registered event.")
    hook = Path(__file__).with_name("workflow_modes_hook.py")
    if not hook.is_file():
        return fail(event, "WORKFLOW_HOOK_SCRIPT_MISSING", "workflow_modes_hook.py is missing from the installed bundle.")
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != event or not isinstance(payload.get("session_id"), str) or not payload["session_id"]:
            return fail(event, "WORKFLOW_HOOK_INPUT_INVALID", "Expected a JSON object with the registered event and a nonempty session_id.")
        result = subprocess.run(
            [sys.executable, str(hook), event], input=raw, capture_output=True,
            timeout=1 if event == "SessionEnd" else 3, check=False,
        )
    except subprocess.TimeoutExpired:
        return fail(event, "WORKFLOW_HOOK_TIMEOUT", "Hook exceeded its runtime budget; a previous state update may have committed.")
    except (ValueError, UnicodeError):
        return fail(event, "WORKFLOW_HOOK_INPUT_INVALID", "Could not decode hook stdin as JSON.")
    except OSError:
        return fail(event, "WORKFLOW_HOOK_START_FAILED", "Unable to start the hook process.")
    try:
        stdout = result.stdout.decode("utf-8").strip()
        stderr = result.stderr.decode("utf-8").strip()
        if result.returncode == 2 and event == "PreToolUse" and stderr.startswith("WORKFLOW_HOOK_") and len(stderr) <= 3000 and not stdout:
            print(stderr, file=sys.stderr)
            return 2
        if result.returncode != 0:
            return fail(event, "WORKFLOW_HOOK_CHILD_FAILED", f"Hook exited with status {result.returncode}; check its runtime dependencies.")
        output = json.loads(stdout) if stdout else None
        if stdout and (not isinstance(output, dict) or not valid_output(output, event)):
            return fail(event, "WORKFLOW_HOOK_OUTPUT_INVALID", "Hook did not return the supported event JSON shape.")
        if stderr:
            # Child diagnostics contain curated infrastructure guidance, never
            # arbitrary tracebacks or plugin payloads.
            if not stderr.startswith("WORKFLOW_HOOK_") or len(stderr) > 3000:
                return fail(event, "WORKFLOW_HOOK_OUTPUT_INVALID", "Unexpected diagnostic output from the hook.")
            print(stderr, file=sys.stderr)
        if output is not None:
            print(json.dumps(output, separators=(",", ":")))
        return 0
    except (ValueError, UnicodeError):
        return fail(event, "WORKFLOW_HOOK_OUTPUT_INVALID", "Hook stdout is not valid UTF-8 JSON.")


if __name__ == "__main__":
    raise SystemExit(main())
