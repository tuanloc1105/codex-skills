from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INSTALL_PATH = PLUGIN_ROOT / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("workflow_modes_install", INSTALL_PATH)
assert SPEC and SPEC.loader
INSTALL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALL
SPEC.loader.exec_module(INSTALL)


class WorkflowModesInstallerTests(unittest.TestCase):
    def test_repository_bundle_is_complete(self) -> None:
        INSTALL.validate_bundle(PLUGIN_ROOT)
        for name in INSTALL.SKILL_NAMES:
            INSTALL.validate_skill_bundle(PLUGIN_ROOT.parent / name, name)

    def test_marketplace_update_preserves_unrelated_entries(self) -> None:
        original = {
            "name": "personal",
            "interface": {"displayName": "My Plugins"},
            "plugins": [{"name": "other", "source": {"source": "local"}}],
            "custom": True,
        }
        updated = INSTALL.updated_marketplace(original)
        self.assertTrue(updated["custom"])
        self.assertEqual(updated["interface"]["displayName"], "My Plugins")
        self.assertEqual([entry["name"] for entry in updated["plugins"]], ["other", "workflow-modes"])

    def test_install_bundle_is_idempotent_for_identical_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "workflow-modes"
            first = INSTALL.install_bundle(PLUGIN_ROOT, destination)
            self.assertTrue(first.changed)
            second = INSTALL.install_bundle(PLUGIN_ROOT, destination)
            self.assertFalse(second.changed)

    def test_atomic_marketplace_write_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "marketplace.json"
            expected = INSTALL.updated_marketplace({"plugins": []})
            INSTALL.write_json_atomically(path, expected)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)

    def test_skill_install_is_complete_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for name in INSTALL.SKILL_NAMES:
                source = PLUGIN_ROOT.parent / name
                destination = Path(directory) / "skills" / name
                first = INSTALL.install_skill_bundle(source, destination, name)
                self.assertTrue(first.changed)
                INSTALL.validate_skill_bundle(destination, name)
                self.assertEqual(INSTALL.fingerprint(source), INSTALL.fingerprint(destination))
                second = INSTALL.install_skill_bundle(source, destination, name)
                self.assertFalse(second.changed)

    def test_skill_install_replaces_and_can_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills" / "discuss"
            destination.mkdir(parents=True)
            (destination / "legacy.txt").write_text("keep in backup", encoding="utf-8")
            result = INSTALL.install_skill_bundle(
                PLUGIN_ROOT.parent / "discuss", destination, "discuss"
            )
            self.assertTrue(result.changed)
            self.assertIsNotNone(result.backup)
            INSTALL.rollback_bundle(destination, result)
            self.assertEqual(
                (destination / "legacy.txt").read_text(encoding="utf-8"),
                "keep in backup",
            )


if __name__ == "__main__":
    unittest.main()
