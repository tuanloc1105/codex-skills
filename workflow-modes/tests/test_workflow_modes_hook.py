from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "scripts" / "workflow_modes_hook.py"
CONTROL = PLUGIN_ROOT / "scripts" / "workflow_modes_control.py"
HOOKS = PLUGIN_ROOT / "hooks" / "hooks.json"
MARKER = "workflow-modes-v1"


class WorkflowModesHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.env = {**os.environ, "PLUGIN_DATA": self.temp_dir.name}
        self.session_id = "workflow-session"
        self.cwd = Path(self.temp_dir.name)
        self.record = self.cwd / "discussion" / "tracker.md"

    def run_hook(self, event: str, **fields: object) -> dict[str, object] | None:
        payload = {
            "session_id": self.session_id,
            "cwd": str(self.cwd),
            "hook_event_name": event,
            **fields,
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def control(self, *args: str) -> dict[str, object] | None:
        command = " ".join(
            [sys.executable, f'"{CONTROL}"', *args, "--marker", MARKER]
        )
        return self.run_hook(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": command},
        )

    def patch(self, *paths: str) -> dict[str, object] | None:
        command = "\n".join(f"*** Update File: {path}" for path in paths)
        return self.run_hook(
            "PreToolUse",
            tool_name="apply_patch",
            tool_input={"command": command},
        )

    def activate(self, mode: str) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        if mode == "discuss":
            content = "Mode: $discuss\nMode status: Active\nExecute mode: Inactive\n"
        elif mode == "execute":
            content = "Status: In progress\nExecute mode: Active\n"
        else:
            content = "Status: Draft\nExecute mode: Inactive\n"
        self.record.write_text(content, encoding="utf-8")
        output = self.control("activate", mode, "--record", str(self.record))
        self.assertIn("WORKFLOW_MODE_ACTIVE", json.dumps(output))

    def test_dormant_until_skill_activates_mode(self) -> None:
        self.assertIsNone(self.patch("app.py"))
        self.assertIsNone(self.run_hook("PostCompact"))

    def test_post_compact_restores_active_mode_and_record(self) -> None:
        self.activate("discuss")
        output = self.run_hook("PostCompact")
        self.assertIn("systemMessage", output)
        self.assertIn(str(self.record), json.dumps(output))
        self.assertIn("only plan or execute", json.dumps(output))

    def test_hook_schema_uses_system_message_for_post_compact(self) -> None:
        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
        self.assertNotIn("additionalContextLimit", hooks["PostCompact"][0]["hooks"][0])
        for event in ("UserPromptSubmit", "PreToolUse"):
            self.assertEqual(
                hooks[event][0]["hooks"][0]["additionalContextLimit"], 900
            )

    def test_discuss_blocks_mutation_without_action(self) -> None:
        self.activate("discuss")
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(blocked))

    def test_discuss_action_is_file_scoped_and_returns_to_discuss(self) -> None:
        self.activate("discuss")
        opened = self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))
        self.assertIsNone(self.patch("app.py"))
        denied = self.patch("other.py")
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(denied))
        closed = self.control("action-close", "--result", "completed")
        self.assertIn("full discuss guardrails restored", json.dumps(closed))
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(blocked))

    def test_discuss_action_requires_source_confirmation(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "non-source",
        )
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_SOURCE_CONFIRMATION_REQUIRED", json.dumps(blocked))

    def test_discuss_transitions_to_plan_then_execute(self) -> None:
        self.activate("discuss")
        self.record.write_text(
            "Mode: $discuss\nMode status: Exited\nExecute mode: Inactive\n",
            encoding="utf-8",
        )
        plan = self.control("transition", "plan", "--record", str(self.record))
        self.assertIn("mode=plan", json.dumps(plan))
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_PLAN_READ_ONLY", json.dumps(blocked))
        self.record.write_text(
            "Status: Approved plan, not yet implemented\nExecute mode: Ready\n",
            encoding="utf-8",
        )
        execute = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(execute))
        self.assertIsNone(self.patch("app.py"))

    def test_discuss_transitions_directly_to_execute(self) -> None:
        self.activate("discuss")
        self.record.write_text(
            "Mode: $discuss\nMode status: Exited\nExecution readiness: Ready\n"
            "Execute mode: Ready\n",
            encoding="utf-8",
        )
        output = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(output))
        compact = self.run_hook("PostCompact")
        self.assertIn("exits only on explicit request", json.dumps(compact))

    def test_discuss_and_plan_cannot_deactivate(self) -> None:
        self.activate("discuss")
        blocked = self.control("deactivate")
        self.assertIn("WORKFLOW_EXIT_DENIED", json.dumps(blocked))

    def test_transition_rejects_tracker_without_durable_markers(self) -> None:
        self.activate("discuss")
        blocked = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("WORKFLOW_HANDOFF_NOT_DURABLE", json.dumps(blocked))

    def test_execute_can_explicitly_deactivate(self) -> None:
        self.activate("execute")
        output = self.control("deactivate")
        self.assertIn("WORKFLOW_MODE_INACTIVE", json.dumps(output))
        self.assertIsNone(self.run_hook("PostCompact"))

    def test_stop_blocks_once_when_discuss_action_is_open(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        first = self.run_hook("Stop", stop_hook_active=False)
        self.assertEqual(first.get("decision"), "block")
        second = self.run_hook("Stop", stop_hook_active=True)
        self.assertIn("stop allowed", json.dumps(second))

    def test_control_script_accepts_expected_cli_shape(self) -> None:
        result = subprocess.run(
            [
                sys.executable, str(CONTROL), "activate", "discuss",
                "--record", str(self.record), "--marker", MARKER,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
