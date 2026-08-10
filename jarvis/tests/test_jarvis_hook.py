from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "scripts" / "jarvis_hook.py"
CONTROL = PLUGIN_ROOT / "scripts" / "jarvis_control.py"
HOOKS_CONFIG = PLUGIN_ROOT / "hooks" / "hooks.json"
MARKER = "jarvis-explicit-v1"


class JarvisHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.env = {**os.environ, "PLUGIN_DATA": self.temp_dir.name}
        self.session_id = "session-test"

    def run_hook(self, event: str, **fields: object) -> dict[str, object] | None:
        payload = {
            "session_id": self.session_id,
            "cwd": str(PLUGIN_ROOT),
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

    def activate(self) -> None:
        output = self.run_hook("UserPromptSubmit", prompt="Use $jarvis for this task")
        self.assertIn("JARVIS_ACTIVE", json.dumps(output))

    def control_command(self, action: str, detail: str | None = None) -> str:
        middle = f" {detail}" if detail else ""
        return (
            f'{sys.executable} "{CONTROL}" {action}{middle} '
            f"--marker {MARKER}"
        )

    def checkpoint(self, detail: str) -> dict[str, object] | None:
        return self.run_hook(
            "PreToolUse",
            tool_name="Bash",
            tool_input={"command": self.control_command("checkpoint", detail)},
        )

    def exec_control(
        self, action: str, detail: str | None = None
    ) -> dict[str, object] | None:
        return self.run_hook(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": self.control_command(action, detail)},
        )

    def patch_payload(self, paths: list[str]) -> dict[str, object]:
        command = "\n".join(f"*** Update File: {path}" for path in paths)
        return {
            "tool_name": "apply_patch",
            "tool_input": {"command": command},
        }

    def test_dormant_until_explicit_invocation(self) -> None:
        output = self.run_hook("PreToolUse", **self.patch_payload(["a.py"]))
        self.assertIsNone(output)
        output = self.run_hook("UserPromptSubmit", prompt="Tell me about Jarvis")
        self.assertIsNone(output)

    def test_additional_context_limit_only_targets_supported_events(self) -> None:
        hooks = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))["hooks"]

        post_compact_command = hooks["PostCompact"][0]["hooks"][0]
        self.assertNotIn("additionalContextLimit", post_compact_command)

        for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse"):
            command = hooks[event][0]["hooks"][0]
            self.assertEqual(command["additionalContextLimit"], 800)

    def test_post_compact_restores_supervision_with_system_message(self) -> None:
        self.activate()

        output = self.run_hook("PostCompact")

        self.assertIn("systemMessage", output)
        self.assertNotIn("additionalContext", json.dumps(output))

    def test_baseline_checkpoint_gates_mutation(self) -> None:
        self.activate()
        blocked = self.run_hook("PreToolUse", **self.patch_payload(["a.py"]))
        self.assertIn("JARVIS_BASELINE_REQUIRED", json.dumps(blocked))
        checkpoint = self.checkpoint("baseline")
        self.assertIn("baseline checkpoint", json.dumps(checkpoint))
        allowed = self.run_hook("PreToolUse", **self.patch_payload(["a.py"]))
        self.assertIsNone(allowed)

    def test_exec_command_schema_records_lifecycle_controls(self) -> None:
        self.activate()
        checkpoint = self.exec_control("checkpoint", "baseline")
        self.assertIn("baseline checkpoint", json.dumps(checkpoint))
        approval = self.exec_control("approve-final")
        self.assertIn("final approval", json.dumps(approval))
        allowed = self.run_hook(
            "Stop", stop_hook_active=False, last_assistant_message="Done"
        )
        self.assertIsNone(allowed)

    def test_exec_command_schema_cannot_bypass_baseline_gate(self) -> None:
        self.activate()
        blocked = self.run_hook(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": "mkdir changed"},
        )
        self.assertIn("JARVIS_BASELINE_REQUIRED", json.dumps(blocked))

    def test_repeated_failures_trigger_rescue_gate(self) -> None:
        self.activate()
        self.checkpoint("baseline")
        first = self.run_hook(
            "PostToolUse",
            tool_name="Bash",
            tool_input={"command": "pytest tests/test_one.py"},
            tool_response={"exit_code": 1, "output": "one failed"},
        )
        self.assertIsNone(first)
        second = self.run_hook(
            "PostToolUse",
            tool_name="Bash",
            tool_input={"command": "pytest tests/test_one.py"},
            tool_response={"exit_code": 1, "output": "one failed"},
        )
        self.assertIn("JARVIS_STUCK", json.dumps(second))
        blocked = self.run_hook("PreToolUse", **self.patch_payload(["fix.py"]))
        self.assertIn("JARVIS_STUCK", json.dumps(blocked))
        rescue = self.checkpoint("rescue")
        self.assertIn("rescue checkpoint", json.dumps(rescue))
        allowed = self.run_hook("PreToolUse", **self.patch_payload(["fix.py"]))
        self.assertIsNone(allowed)

    def test_scope_expansion_requires_review(self) -> None:
        self.activate()
        self.checkpoint("baseline")
        paths = [f"file_{index}.py" for index in range(6)]
        blocked = self.run_hook("PreToolUse", **self.patch_payload(paths))
        self.assertIn("JARVIS_SCOPE_REVIEW", json.dumps(blocked))
        scope = self.checkpoint("scope")
        self.assertIn("scope checkpoint", json.dumps(scope))
        allowed = self.run_hook("PreToolUse", **self.patch_payload(paths))
        self.assertIsNone(allowed)

    def test_stop_requires_final_approval_then_cleans_state(self) -> None:
        self.activate()
        self.checkpoint("baseline")
        blocked = self.run_hook(
            "Stop", stop_hook_active=False, last_assistant_message="Done"
        )
        self.assertIn("JARVIS_FINAL_REVIEW_REQUIRED", json.dumps(blocked))
        approval = self.run_hook(
            "PreToolUse",
            tool_name="Bash",
            tool_input={"command": self.control_command("approve-final")},
        )
        self.assertIn("final approval", json.dumps(approval))
        allowed = self.run_hook(
            "Stop", stop_hook_active=True, last_assistant_message="Done"
        )
        self.assertIsNone(allowed)
        dormant = self.run_hook("PreToolUse", **self.patch_payload(["later.py"]))
        self.assertIsNone(dormant)

    def test_second_stop_avoids_infinite_loop(self) -> None:
        self.activate()
        first = self.run_hook(
            "Stop", stop_hook_active=False, last_assistant_message="Done"
        )
        self.assertIn("JARVIS_FINAL_REVIEW_REQUIRED", json.dumps(first))
        second = self.run_hook(
            "Stop", stop_hook_active=True, last_assistant_message="Done"
        )
        self.assertIn("infinite continuation loop", json.dumps(second))

    def test_control_script_validates_marker(self) -> None:
        valid = subprocess.run(
            [
                sys.executable,
                str(CONTROL),
                "activate",
                "--marker",
                MARKER,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        invalid = subprocess.run(
            [
                sys.executable,
                str(CONTROL),
                "activate",
                "--marker",
                "wrong",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main()
