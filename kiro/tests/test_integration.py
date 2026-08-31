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


KIRO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SPEC = importlib.util.spec_from_file_location(
    "kiro_integration_install", KIRO_ROOT / "scripts" / "install.py"
)
assert INSTALL_SPEC and INSTALL_SPEC.loader
INSTALL = importlib.util.module_from_spec(INSTALL_SPEC)
sys.modules[INSTALL_SPEC.name] = INSTALL
INSTALL_SPEC.loader.exec_module(INSTALL)
MARKER = "workflow-modes-v1"
REFERENCES = {
    "discuss": ("references/tracker.md", "references/actions.md"),
    "plan": ("references/plan-record.md", "references/phase-planning.md"),
    "execute": ("references/implementation.md", "references/completion.md"),
}


class InstalledWorkflowHarness:
    def __init__(self, root: Path, *, scope: str = "global") -> None:
        self.root = root
        self.workspace = root / "workspace"
        self.workspace.mkdir(parents=True)
        self.config_root = root / ("global-kiro" if scope == "global" else "workspace/.kiro")
        INSTALL.install_distribution(KIRO_ROOT, self.config_root, scope=scope)
        self.hook = self.config_root / "workflow-modes/scripts/workflow_modes_hook.py"
        self.control_script = self.config_root / "workflow-modes/scripts/workflow_modes_control.py"
        self.session_id = f"installed-{scope}-session"
        self.scope = scope

    @property
    def environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "KIRO_HOME": str(self.config_root),
            "KIRO_WORKFLOW_SCOPE": self.scope,
        }

    def event(self, name: str, **fields: object) -> subprocess.CompletedProcess[str]:
        payload = {
            "hook_event_name": name,
            "session_id": self.session_id,
            "cwd": str(self.workspace),
            **fields,
        }
        return subprocess.run(
            [sys.executable, str(self.hook)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )

    def control(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = " ".join(
            [sys.executable, f'"{self.control_script}"', *args, "--marker", MARKER]
        )
        return self.event(
            "preToolUse",
            tool_name="exec_command",
            tool_input={"cmd": command},
        )

    def activate_and_sync(self, mode: str, record: Path) -> None:
        activated = self.control("activate", mode, "--record", str(record))
        assert activated.returncode == 0, activated.stderr
        assert "WORKFLOW_MODE_ACTIVE" in activated.stdout
        synced = self.control("sync", "--record", str(record))
        assert synced.returncode == 0, synced.stderr
        arguments = [
            item for reference in REFERENCES[mode] for item in ("--reference", reference)
        ]
        rules = self.control("rules-sync", "--record", str(record), *arguments)
        assert rules.returncode == 0, rules.stderr


class KiroInstalledIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def create_record(
        self,
        harness: InstalledWorkflowHarness,
        name: str,
        *,
        mode: str,
        direct_ready: bool = False,
        approved: bool = False,
        execute_active: bool = False,
    ) -> Path:
        record = harness.workspace / ("discussion" if mode == "discuss" else "plans") / name
        record.mkdir(parents=True)
        kind = "discuss" if mode == "discuss" else "plan"
        if kind == "discuss":
            manifest = ["index.md", "context.md", "decisions.md", "actions.md", "evidence.md"]
            lifecycle = (
                "Mode: /workflow-discuss\n"
                + ("Mode status: Exited\n" if direct_ready else "Mode status: Active\n")
                + ("Execution readiness: Ready\nExecute mode: Ready\n" if direct_ready else "Execution readiness: Not ready\nExecute mode: Inactive\n")
            )
            if direct_ready:
                manifest.extend(["plan.md", "verification.md"])
        else:
            manifest = [
                "index.md", "context.md", "decisions.md", "plan.md", "verification.md", "evidence.md"
            ]
            if execute_active:
                lifecycle = "Status: In progress\nExecute mode: Active\n"
            elif approved:
                lifecycle = "Status: Approved plan, not yet implemented\nExecute mode: Ready\n"
            else:
                lifecycle = "Status: Draft\nExecute mode: Inactive\n"
        reference_mode = "execute" if direct_ready or execute_active else mode
        index = (
            f"<!-- workflow-record version:4 kind:{kind} tracker-id:{name.upper()} -->\n"
            + lifecycle
            + "Active action: None\n"
            + "<!-- workflow-active-snapshot:start version:2 -->\n"
            + f"Profile: {'Durable' if reference_mode == 'execute' else 'Lightweight'}\n"
            + f"Required references: {', '.join(REFERENCES[reference_mode])}\n"
            + "Goal: Installed integration\nCurrent state: Active\nAccepted decisions: None\n"
            + "Open items: None\nNext safe action: Continue\n"
            + "<!-- workflow-active-snapshot:end -->\n"
            + "<!-- workflow-manifest:start -->\n"
            + "\n".join(manifest)
            + "\n<!-- workflow-manifest:end -->\n"
        )
        (record / "index.md").write_text(index)
        for entry in manifest[1:]:
            (record / entry).write_text(f"# {Path(entry).stem}\n")
        return record

    def revision(self, record: Path) -> str:
        digest = hashlib.sha256()
        files = {
            path.relative_to(record).as_posix(): path.read_text()
            for path in record.rglob("*.md")
        }
        for name in sorted(files):
            digest.update(name.encode())
            digest.update(b"\0")
            digest.update(hashlib.sha256(files[name].encode()).digest())
        return "sha256:" + digest.hexdigest()

    def test_installed_discuss_write_and_checkpoint(self) -> None:
        harness = InstalledWorkflowHarness(self.root)
        record = self.create_record(harness, "discuss-flow", mode="discuss")
        harness.activate_and_sync("discuss", record)
        prompt = harness.event("promptSubmit")
        self.assertEqual(0, prompt.returncode, prompt.stderr)
        self.assertIn("mode=discuss", prompt.stdout)
        opened = harness.control(
            "write-open", "--record", str(record),
            "--previous-revision", self.revision(record),
        )
        self.assertIn("WORKFLOW_WRITE_OPEN", opened.stdout)
        allowed = harness.event(
            "PreToolUse", tool_name="apply_patch",
            tool_input={"command": f"*** Update File: {record / 'context.md'}"},
        )
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        (record / "context.md").write_text("# Context\nUpdated\n")
        closed = harness.control("write-close", "--record", str(record))
        self.assertIn("WORKFLOW_WRITE_CLOSED", closed.stdout)
        checkpoint = harness.control("checkpoint", "--record", str(record))
        self.assertIn("WORKFLOW_TURN_CHECKPOINTED", checkpoint.stdout)

    def test_discuss_to_separate_plan_bootstrap(self) -> None:
        harness = InstalledWorkflowHarness(self.root)
        discussion = self.create_record(harness, "plan-source", mode="discuss")
        index = discussion / "index.md"
        index.write_text(index.read_text().replace("Mode status: Active", "Mode status: Exited"))
        activated = harness.control("activate", "discuss", "--record", str(discussion))
        self.assertIn("WORKFLOW_MODE_ACTIVE", activated.stdout)
        transitioned = harness.control("transition", "plan", "--record", str(discussion))
        self.assertIn("mode=plan", transitioned.stdout)
        target = harness.workspace / "plans" / "separate-plan"
        initialized = harness.control(
            "plan-init", "--record", str(discussion), "--target", str(target)
        )
        self.assertIn("WORKFLOW_PLAN_INIT_OPEN", initialized.stdout)
        target = self.create_record(harness, "separate-plan", mode="plan")
        activated_plan = harness.control("activate", "plan", "--record", str(target))
        self.assertIn(str(target), activated_plan.stdout)

    def test_direct_and_approved_plan_execute_handoffs(self) -> None:
        direct = InstalledWorkflowHarness(self.root / "direct")
        discussion = self.create_record(
            direct, "direct-execute", mode="discuss", direct_ready=True
        )
        self.assertIn(
            "WORKFLOW_MODE_ACTIVE",
            direct.control("activate", "discuss", "--record", str(discussion)).stdout,
        )
        direct_transition = direct.control(
            "transition", "execute", "--record", str(discussion)
        )
        self.assertIn("mode=execute", direct_transition.stdout)
        self.assertIn(str(discussion), direct_transition.stdout)

        approved = InstalledWorkflowHarness(self.root / "approved")
        plan = self.create_record(approved, "approved-plan", mode="plan", approved=True)
        self.assertIn(
            "WORKFLOW_MODE_ACTIVE",
            approved.control("activate", "plan", "--record", str(plan)).stdout,
        )
        plan_transition = approved.control(
            "transition", "execute", "--record", str(plan)
        )
        self.assertIn("mode=execute", plan_transition.stdout)
        self.assertIn(str(plan), plan_transition.stdout)

    def test_execute_scoped_action_and_stop_recovery(self) -> None:
        harness = InstalledWorkflowHarness(self.root)
        record = self.create_record(
            harness, "execute-action", mode="plan", execute_active=True
        )
        harness.activate_and_sync("execute", record)
        evidence = record / "evidence.md"
        evidence.write_text(
            "# Evidence\n<!-- workflow-action:INT100 status:open -->\nINT100\n"
        )
        index = record / "index.md"
        index.write_text(
            index.read_text().replace(
                "Active action: None",
                "Active action: INT100 — installed integration fixture",
            )
        )
        harness.control("sync", "--record", str(record))
        allowed_path = harness.workspace / "allowed.py"
        opened = harness.control(
            "action-open", "--record", str(record), "--evidence-id", "INT100",
            "--impact", "source-confirmed", "--path", str(allowed_path),
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", opened.stdout)
        allowed = harness.event(
            "preToolUse", toolName="apply_patch",
            toolInput={"command": f"*** Add File: {allowed_path}"},
        )
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        denied = harness.event(
            "preToolUse", toolName="apply_patch",
            toolInput={"command": f"*** Add File: {harness.workspace / 'outside.py'}"},
        )
        self.assertNotEqual(0, denied.returncode)
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", denied.stderr)
        evidence.write_text(
            "# Evidence\n<!-- workflow-action:INT100 status:completed -->\nINT100\n"
        )
        index.write_text(
            index.read_text().replace(
                "Active action: INT100 — installed integration fixture",
                "Active action: None",
            )
        )
        closed = harness.control("action-close", "--result", "completed")
        self.assertIn("WORKFLOW_ACTION_CLOSED", closed.stdout)
        harness.event("UserPromptSubmit")
        stop = harness.event("agentStop")
        self.assertIn("WORKFLOW_STOP_RECOVERY_PENDING", stop.stdout)
        mutation = harness.event(
            "preToolUse", toolName="apply_patch",
            toolInput={"command": f"*** Add File: {allowed_path}"},
        )
        self.assertNotEqual(0, mutation.returncode)
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", mutation.stderr)

    def test_project_precedence_and_skill_only_surfaces(self) -> None:
        global_harness = InstalledWorkflowHarness(self.root / "global", scope="global")
        project_harness = InstalledWorkflowHarness(self.root / "project", scope="project")
        marker = global_harness.workspace / ".kiro/workflow-modes/project-owned"
        marker.parent.mkdir(parents=True)
        marker.write_text("workflow-modes-v1\n")
        dormant = global_harness.event("preToolUse", toolName="write", toolInput={})
        self.assertEqual(0, dormant.returncode)
        self.assertEqual("", dormant.stdout)
        self.assertEqual("", dormant.stderr)
        for name in ("workflow-discuss", "workflow-plan", "workflow-execute"):
            self.assertTrue(
                (project_harness.config_root / "skills" / name / "SKILL.md").is_file()
            )
        manifest = json.loads((KIRO_ROOT / "manifest.json").read_text())
        self.assertEqual("skills-only", manifest["supported"]["web"])
        self.assertEqual("skills-only", manifest["supported"]["mobile"])


if __name__ == "__main__":
    unittest.main()
