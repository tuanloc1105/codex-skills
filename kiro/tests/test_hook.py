from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


KIRO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = KIRO_ROOT / "scripts" / "workflow_modes_hook.py"
CONTROL_PATH = KIRO_ROOT / "scripts" / "workflow_modes_control.py"
HOOKS_PATH = KIRO_ROOT / "hooks" / "workflow-modes.json"
MARKER = "workflow-modes-v1"
MODE_REFERENCES = {
    "discuss": ("references/tracker.md", "references/actions.md"),
    "plan": ("references/plan-record.md", "references/phase-planning.md"),
    "execute": ("references/implementation.md", "references/completion.md"),
}

SPEC = importlib.util.spec_from_file_location("kiro_workflow_modes_hook", HOOK_PATH)
assert SPEC and SPEC.loader
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class KiroWorkflowModesHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.state = self.root / "state"
        self.cwd = self.root / "workspace"
        self.cwd.mkdir()
        self.record = self.cwd / "discussion" / "record"
        self.index = self.record / "index.md"
        self.session_id = "kiro-test-session"
        self.environment = {
            "KIRO_WORKFLOW_STATE": str(self.state),
            "KIRO_HOME": str(self.root / "kiro-home"),
        }

    def payload(self, event: str, **fields: object) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "cwd": str(self.cwd),
            "hook_event_name": event,
            **fields,
        }

    def hook_event(self, event: str, **fields: object) -> dict[str, object] | None:
        with mock.patch.dict(os.environ, self.environment, clear=False):
            return HOOK.run(self.payload(event, **fields))

    def control(self, *args: str) -> dict[str, object] | None:
        command = " ".join(
            [sys.executable, f'"{CONTROL_PATH}"', *args, "--marker", MARKER]
        )
        return self.hook_event(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": command},
        )

    def message(self, output: object) -> str:
        return json.dumps(output, sort_keys=True)

    def index_content(self, mode: str, *, status: str | None = None) -> str:
        kind = "discuss" if mode == "discuss" else "plan"
        manifest = (
            ("index.md", "context.md", "decisions.md", "actions.md", "evidence.md")
            if kind == "discuss"
            else (
                "index.md",
                "context.md",
                "decisions.md",
                "plan.md",
                "verification.md",
                "evidence.md",
            )
        )
        profile = "Durable" if mode == "execute" else "Lightweight"
        lifecycle = {
            "discuss": "Mode: /workflow-discuss\nMode status: Active\nExecute mode: Inactive\n",
            "plan": (
                f"Status: {status or 'Draft'}\n"
                + (
                    "Execute mode: Ready\n"
                    if status == "Approved plan, not yet implemented"
                    else "Execute mode: Inactive\n"
                )
            ),
            "execute": "Status: In progress\nExecute mode: Active\n",
        }[mode]
        return (
            f"<!-- workflow-record version:4 kind:{kind} tracker-id:KIRO-TEST -->\n"
            + lifecycle
            + "Active action: None\n"
            + "<!-- workflow-active-snapshot:start version:2 -->\n"
            + f"Profile: {profile}\nRequired references: {', '.join(MODE_REFERENCES[mode])}\n"
            + "Goal: Test workflow\nCurrent state: Active\nAccepted decisions: None\n"
            + "Open items: None\nNext safe action: Continue\n"
            + "<!-- workflow-active-snapshot:end -->\n"
            + "<!-- workflow-manifest:start -->\n"
            + "\n".join(manifest)
            + "\n<!-- workflow-manifest:end -->\n"
        )

    def create_bundle(self, mode: str = "discuss", *, status: str | None = None) -> None:
        self.record.mkdir(parents=True, exist_ok=True)
        content = self.index_content(mode, status=status)
        self.index.write_text(content)
        start = content.index("<!-- workflow-manifest:start -->")
        end = content.index("<!-- workflow-manifest:end -->")
        for entry in content[start:end].splitlines()[1:]:
            entry = entry.strip()
            if not entry or entry == "index.md":
                continue
            path = self.record / entry
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.stem}\n")

    def revision(self) -> str:
        digest = hashlib.sha256()
        files = {
            path.relative_to(self.record).as_posix(): path.read_text()
            for path in self.record.rglob("*.md")
        }
        for name in sorted(files):
            digest.update(name.encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(files[name].encode()).digest())
        return "sha256:" + digest.hexdigest()

    def activate(self, mode: str) -> None:
        self.create_bundle(mode)
        self.assertIn(
            "WORKFLOW_MODE_ACTIVE",
            self.message(self.control("activate", mode, "--record", str(self.record))),
        )
        self.assertIn(
            "WORKFLOW_RECORD_SYNCED",
            self.message(self.control("sync", "--record", str(self.record))),
        )
        references = [
            item
            for reference in MODE_REFERENCES[mode]
            for item in ("--reference", reference)
        ]
        self.assertIn(
            "WORKFLOW_RULES_SYNCED",
            self.message(
                self.control("rules-sync", "--record", str(self.record), *references)
            ),
        )

    def test_v1_hook_schema_and_control_surface(self) -> None:
        hooks = json.loads(HOOKS_PATH.read_text())
        self.assertEqual("v1", hooks["version"])
        self.assertEqual(
            {"SessionStart", "UserPromptSubmit", "PreToolUse", "Stop"},
            {hook["trigger"] for hook in hooks["hooks"]},
        )
        for item in hooks["hooks"]:
            self.assertEqual("command", item["action"]["type"])
            self.assertEqual("{{WORKFLOW_MODES_COMMAND}}", item["action"]["command"])
        result = subprocess.run(
            [sys.executable, str(CONTROL_PATH), "activate", "discuss", "--marker", MARKER],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode)

    def test_dormant_and_payload_aliases(self) -> None:
        self.assertIsNone(self.hook_event("preToolUse", toolName="read", toolInput={}))
        self.create_bundle("discuss")
        command = " ".join(
            [
                sys.executable,
                f'"{CONTROL_PATH}"',
                "activate",
                "discuss",
                "--record",
                str(self.record),
                "--marker",
                MARKER,
            ]
        )
        payload = {
            "sessionId": self.session_id,
            "workingDirectory": str(self.cwd),
            "hookEventName": "preToolUse",
            "toolName": "exec_command",
            "toolInput": {"cmd": command},
        }
        with mock.patch.dict(os.environ, self.environment, clear=False):
            self.assertIn("WORKFLOW_MODE_ACTIVE", self.message(HOOK.run(payload)))

    def test_activation_sync_rules_and_bounded_anchor(self) -> None:
        self.activate("discuss")
        prompt = self.hook_event("promptSubmit")
        self.assertIn("workflow-anchor version", self.message(prompt))
        self.assertLess(len(self.message(prompt)), 1100)
        read_anchor = self.hook_event("preToolUse", toolName="read", toolInput={})
        self.assertIn("mode=discuss", self.message(read_anchor))

    def test_invalid_bundle_is_rejected(self) -> None:
        self.record.mkdir(parents=True)
        self.index.write_text("<!-- workflow-record version:3 kind:discuss tracker-id:X -->\n")
        result = self.control("activate", "discuss", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_VERSION_UNSUPPORTED", self.message(result))

    def test_write_transactions_and_scoped_actions(self) -> None:
        self.activate("discuss")
        opened = self.control(
            "write-open",
            "--record",
            str(self.record),
            "--previous-revision",
            self.revision(),
        )
        self.assertIn("WORKFLOW_WRITE_OPEN", self.message(opened))
        outside = self.hook_event(
            "PreToolUse",
            tool_name="apply_patch",
            tool_input={"command": "*** Update File: outside.py"},
        )
        self.assertIn("WORKFLOW_WRITE_SCOPE_DENIED", self.message(outside))

    def test_approved_plan_transition_keeps_bundle(self) -> None:
        self.create_bundle("plan", status="Approved plan, not yet implemented")
        self.assertIn(
            "WORKFLOW_MODE_ACTIVE",
            self.message(self.control("activate", "plan", "--record", str(self.record))),
        )
        result = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", self.message(result))
        self.assertIn(str(self.record), self.message(result))

    def test_stop_persists_recovery_and_denies_mutation(self) -> None:
        self.activate("execute")
        self.hook_event("UserPromptSubmit")
        stop = self.hook_event("agentStop")
        self.assertIn("WORKFLOW_STOP_RECOVERY_PENDING", self.message(stop))
        mutation = self.hook_event(
            "preToolUse",
            toolName="apply_patch",
            toolInput={"command": "*** Update File: app.py"},
        )
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", self.message(mutation))

    def test_global_scope_dormant_for_project_marker(self) -> None:
        marker = self.cwd / ".kiro" / "workflow-modes" / "project-owned"
        marker.parent.mkdir(parents=True)
        marker.write_text("workflow-modes-v1\n")
        self.create_bundle("discuss")
        with mock.patch.dict(
            os.environ,
            {**self.environment, "KIRO_WORKFLOW_SCOPE": "global"},
            clear=False,
        ):
            self.assertIsNone(
                HOOK.run(
                    self.payload(
                        "PreToolUse",
                        tool_name="exec_command",
                        tool_input={"cmd": "mkdir blocked"},
                    )
                )
            )

    def test_cli_stdout_stderr_and_exit_codes(self) -> None:
        self.create_bundle("discuss")
        env = {**os.environ, **self.environment}
        activate_command = " ".join(
            [
                sys.executable,
                f'"{CONTROL_PATH}"',
                "activate",
                "discuss",
                "--record",
                str(self.record),
                "--marker",
                MARKER,
            ]
        )
        activate = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(
                self.payload(
                    "PreToolUse",
                    tool_name="exec_command",
                    tool_input={"cmd": activate_command},
                )
            ),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(0, activate.returncode, activate.stderr)
        self.assertIn("WORKFLOW_MODE_ACTIVE", activate.stdout)
        denied = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(
                self.payload(
                    "preToolUse",
                    toolName="apply_patch",
                    toolInput={"command": "*** Update File: app.py"},
                )
            ),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(0, denied.returncode)
        self.assertEqual("", denied.stdout)
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", denied.stderr)


if __name__ == "__main__":
    unittest.main()
