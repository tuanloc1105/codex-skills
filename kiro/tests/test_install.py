from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


KIRO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_PATH = KIRO_ROOT / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("kiro_workflow_install", INSTALL_PATH)
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALL
SPEC.loader.exec_module(INSTALL)


class KiroInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def source_copy(self) -> Path:
        target = self.root / f"source-{len(list(self.root.glob('source-*')))}"
        shutil.copytree(KIRO_ROOT, target)
        return target

    def test_repository_distribution_is_complete(self) -> None:
        manifest = INSTALL.validate_source(KIRO_ROOT)
        self.assertEqual("1.0.0", manifest["version"])
        self.assertEqual(4, manifest["recordVersion"])
        self.assertEqual(3, len(manifest["skills"]))

    def test_cross_platform_command_rendering(self) -> None:
        global_root = Path("/opt/kiro home")
        linux = INSTALL.render_command("global", global_root, "linux")
        darwin = INSTALL.render_command("project", Path("/unused"), "darwin")
        windows = INSTALL.render_command("global", Path("C:/Users/Test/.kiro"), "win32")
        self.assertEqual(
            'KIRO_WORKFLOW_SCOPE=global python3 "/opt/kiro home/workflow-modes/scripts/workflow_modes_hook.py"',
            linux,
        )
        self.assertEqual(
            'KIRO_WORKFLOW_SCOPE=project python3 ".kiro/workflow-modes/scripts/workflow_modes_hook.py"',
            darwin,
        )
        self.assertIn("set KIRO_WORKFLOW_SCOPE=global&& py -3", windows)
        self.assertIn("workflow_modes_hook.py", windows)

    def test_global_install_is_complete_idempotent_and_preserving(self) -> None:
        kiro_home = self.root / "global" / ".kiro"
        unrelated = kiro_home / "skills" / "unrelated" / "SKILL.md"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("unrelated\n")
        first = INSTALL.install_distribution(KIRO_ROOT, kiro_home, scope="global")
        second = INSTALL.install_distribution(KIRO_ROOT, kiro_home, scope="global")
        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        self.assertEqual("unrelated\n", unrelated.read_text())
        self.assertTrue((kiro_home / "skills/workflow-execute/SKILL.md").is_file())
        self.assertTrue((kiro_home / "workflow-modes/scripts/workflow_modes_hook.py").is_file())
        hook = (kiro_home / "hooks/workflow-modes.json").read_text()
        self.assertIn("KIRO_WORKFLOW_SCOPE=global", hook)
        self.assertNotIn("{{WORKFLOW_MODES_COMMAND}}", hook)

    def test_project_export_uses_only_project_owned_paths(self) -> None:
        project = self.root / "project"
        project.mkdir()
        unrelated = project / ".kiro" / "settings" / "mcp.json"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('{"keep": true}\n')
        result = INSTALL.install_distribution(
            KIRO_ROOT, project / ".kiro", scope="project"
        )
        self.assertTrue(result.changed)
        self.assertEqual('{"keep": true}\n', unrelated.read_text())
        self.assertEqual(
            "workflow-modes-v1\n",
            (project / ".kiro/workflow-modes/project-owned").read_text(),
        )
        hook = (project / ".kiro/hooks/workflow-modes.json").read_text()
        self.assertIn("KIRO_WORKFLOW_SCOPE=project", hook)
        command = json.loads(hook)["hooks"][0]["action"]["command"]
        self.assertIn('python3 ".kiro/workflow-modes/scripts/', command)

    def test_same_version_drift_is_rejected_and_forceable(self) -> None:
        target = self.root / "drift"
        INSTALL.install_distribution(KIRO_ROOT, target, scope="global")
        hook = target / "hooks/workflow-modes.json"
        hook.write_text(hook.read_text() + "\n")
        with self.assertRaisesRegex(INSTALL.InstallError, "same-version"):
            INSTALL.install_distribution(KIRO_ROOT, target, scope="global")
        forced = INSTALL.install_distribution(
            KIRO_ROOT, target, scope="global", force_drift=True
        )
        self.assertTrue(forced.changed)
        self.assertIsNotNone(forced.backup)

    def test_dry_run_does_not_create_target(self) -> None:
        target = self.root / "missing" / ".kiro"
        result = INSTALL.install_distribution(
            KIRO_ROOT, target, scope="global", dry_run=True
        )
        self.assertTrue(result.changed)
        self.assertFalse(target.exists())

    def test_changed_version_creates_backup_and_rollback_restores(self) -> None:
        source = self.source_copy()
        target = self.root / "rollback-target"
        INSTALL.install_distribution(source, target, scope="global")
        manifest_path = source / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "1.1.0"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        upgraded = INSTALL.install_distribution(source, target, scope="global")
        self.assertIsNotNone(upgraded.backup)
        installed = json.loads((target / "workflow-modes/manifest.json").read_text())
        self.assertEqual("1.1.0", installed["version"])
        INSTALL.rollback(upgraded.backup, target)
        restored = json.loads((target / "workflow-modes/manifest.json").read_text())
        self.assertEqual("1.0.0", restored["version"])

    def test_partial_failure_rolls_back_without_collateral_changes(self) -> None:
        target = self.root / "failure-target"
        target.mkdir()
        unrelated = target / "settings.json"
        unrelated.write_text("keep\n")
        original_replace = os.replace
        stage_replacements = 0

        def fail_second_stage(source: object, destination: object) -> None:
            nonlocal stage_replacements
            if "kiro-workflow-stage-" in os.fspath(source):
                stage_replacements += 1
                if stage_replacements == 2:
                    raise OSError("injected replacement failure")
            original_replace(source, destination)

        with mock.patch.object(INSTALL.os, "replace", side_effect=fail_second_stage):
            with self.assertRaisesRegex(OSError, "injected"):
                INSTALL.install_distribution(KIRO_ROOT, target, scope="global")
        self.assertEqual("keep\n", unrelated.read_text())
        self.assertFalse((target / "workflow-modes/manifest.json").exists())
        self.assertFalse((target / "hooks/workflow-modes.json").exists())

    def test_cli_defaults_to_kiro_home_override(self) -> None:
        target = self.root / "cli-home"
        result = INSTALL.main(["install", "--kiro-home", str(target), "--dry-run"])
        self.assertEqual(0, result)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
