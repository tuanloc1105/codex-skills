from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("jarvis_installer", INSTALLER_PATH)
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class JarvisInstallerTests(unittest.TestCase):
    def make_bundle(self, root: Path) -> Path:
        bundle = root / "source" / "jarvis"
        for relative_path in installer.REQUIRED_PATHS:
            path = bundle / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative_path == Path(".codex-plugin/plugin.json"):
                path.write_text(
                    json.dumps({"name": "jarvis", "version": "0.1.0"}) + "\n",
                    encoding="utf-8",
                )
            else:
                path.write_text(f"fixture: {relative_path}\n", encoding="utf-8")
        return bundle

    def test_install_bundle_copies_complete_plugin_and_excludes_generated_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            (source / "tests" / "__pycache__").mkdir(parents=True)
            (source / "tests" / "__pycache__" / "test.pyc").write_bytes(b"cache")
            (source / ".DS_Store").write_bytes(b"metadata")
            destination = root / "home" / "plugins" / "jarvis"

            result = installer.install_bundle(source, destination)

            self.assertTrue(result.changed)
            self.assertIsNone(result.backup)
            installer.validate_bundle(destination)
            self.assertFalse((destination / "tests" / "__pycache__").exists())
            self.assertFalse((destination / ".DS_Store").exists())

    def test_install_bundle_replaces_existing_copy_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            destination = root / "home" / "plugins" / "jarvis"
            destination.mkdir(parents=True)
            (destination / "old.txt").write_text("old\n", encoding="utf-8")

            result = installer.install_bundle(source, destination)

            self.assertTrue(result.changed)
            self.assertIsNotNone(result.backup)
            assert result.backup is not None
            self.assertEqual(
                (result.backup / "old.txt").read_text(encoding="utf-8"), "old\n"
            )
            installer.validate_bundle(destination)
            self.assertFalse((destination / "old.txt").exists())

    def test_install_bundle_restores_existing_copy_when_swap_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            destination = root / "home" / "plugins" / "jarvis"
            destination.mkdir(parents=True)
            (destination / "old.txt").write_text("old\n", encoding="utf-8")
            original_replace = installer.os.replace
            calls = 0

            def fail_staged_swap(source_path, destination_path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated staged swap failure")
                return original_replace(source_path, destination_path)

            with mock.patch.object(installer.os, "replace", side_effect=fail_staged_swap):
                with self.assertRaises(OSError):
                    installer.install_bundle(source, destination)

            self.assertEqual(
                (destination / "old.txt").read_text(encoding="utf-8"), "old\n"
            )

    def test_validate_bundle_requires_explicit_only_config_and_supervisor_prompt(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)

            for relative_path in (
                Path("skills/jarvis/agents/openai.yaml"),
                Path("skills/jarvis/references/supervisor-prompt.md"),
            ):
                target = source / relative_path
                contents = target.read_text(encoding="utf-8")
                target.unlink()
                with self.assertRaises(installer.InstallError):
                    installer.validate_bundle(source)
                target.write_text(contents, encoding="utf-8")

    def test_validate_bundle_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            target = source / "real.txt"
            target.write_text("real\n", encoding="utf-8")
            link = source / "linked.txt"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            with self.assertRaises(installer.InstallError):
                installer.validate_bundle(source)

    def test_install_bundle_rejects_symlink_destination(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            actual_destination = root / "actual"
            actual_destination.mkdir()
            linked_destination = root / "jarvis"
            try:
                linked_destination.symlink_to(actual_destination, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            with self.assertRaises(installer.InstallError):
                installer.install_bundle(source, linked_destination)

    def test_marketplace_update_preserves_unrelated_content(self):
        original = {
            "name": "personal",
            "interface": {"displayName": "My Marketplace"},
            "custom": {"keep": True},
            "plugins": [
                {"name": "another-plugin", "source": {"source": "local"}},
                {"name": "jarvis", "obsolete": True},
            ],
        }

        updated = installer.update_marketplace_document(original)

        self.assertEqual(updated["interface"], original["interface"])
        self.assertEqual(updated["custom"], original["custom"])
        self.assertEqual(
            [entry["name"] for entry in updated["plugins"]],
            ["another-plugin", "jarvis"],
        )
        self.assertEqual(
            updated["plugins"][-1]["source"]["path"], "./plugins/jarvis"
        )
        self.assertNotIn("obsolete", updated["plugins"][-1])
        self.assertEqual(original["plugins"][-1], {"name": "jarvis", "obsolete": True})

    def test_load_marketplace_rejects_non_object_plugin_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "marketplace.json"
            path.write_text('{"plugins": ["invalid"]}\n', encoding="utf-8")

            with self.assertRaises(installer.InstallError):
                installer.load_marketplace(path)

    def test_atomic_json_write_round_trips_unicode(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / ".agents" / "plugins" / "marketplace.json"
            expected = {"name": "cá nhân", "plugins": []}

            installer.write_json_atomically(path, expected)

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_load_marketplace_seeds_personal_marketplace(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "missing.json"

            marketplace = installer.load_marketplace(path)

            self.assertEqual(marketplace["name"], "personal")
            self.assertEqual(marketplace["plugins"], [])

    def test_source_equal_to_destination_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self.make_bundle(Path(temporary_directory))

            result = installer.install_bundle(source, source)

            self.assertFalse(result.changed)
            installer.validate_bundle(source)

    def test_identical_versioned_bundle_is_an_idempotent_update(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            destination = root / "home" / "plugins" / "jarvis"
            first = installer.install_bundle(source, destination)

            second = installer.install_bundle(source, destination)

            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(
                list((destination.parent).glob("jarvis.backup-*")), []
            )

    def test_changed_bundle_with_same_version_requires_new_cachebuster(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = self.make_bundle(root)
            destination = root / "home" / "plugins" / "jarvis"
            installer.install_bundle(source, destination)
            (source / "hooks" / "hooks.json").write_text(
                "changed without version bump\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(installer.InstallError, "new cachebuster"):
                installer.install_bundle(source, destination)

    def test_add_plugin_uses_argument_list_without_shell(self):
        completed = mock.Mock(returncode=0)
        with mock.patch.object(installer.subprocess, "run", return_value=completed) as run:
            installer.add_plugin("codex.cmd", "personal")

        run.assert_called_once_with(
            ["codex.cmd", "plugin", "add", "jarvis@personal"], check=False
        )

    def test_add_plugin_reports_cli_failure(self):
        completed = mock.Mock(returncode=7)
        with mock.patch.object(installer.subprocess, "run", return_value=completed):
            with self.assertRaises(installer.InstallError):
                installer.add_plugin("codex", "personal")

    def test_main_dry_run_performs_no_mutations(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_home = Path(temporary_directory)
            with (
                mock.patch.object(installer.Path, "home", return_value=fake_home),
                mock.patch.object(
                    installer, "find_codex_cli", return_value="codex.cmd"
                ),
                mock.patch.object(installer, "install_bundle") as install_bundle,
                mock.patch.object(installer, "write_json_atomically") as write_json,
                mock.patch.object(installer, "add_plugin") as add_plugin,
            ):
                exit_code = installer.main(["--dry-run"])

            self.assertEqual(exit_code, 0)
            install_bundle.assert_not_called()
            write_json.assert_not_called()
            add_plugin.assert_not_called()
            self.assertFalse((fake_home / "plugins").exists())

    def test_main_updates_existing_installation_and_refreshes_codex(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_home = Path(temporary_directory)
            destination = fake_home / "plugins" / "jarvis"
            destination.mkdir(parents=True)
            manifest = destination / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({"name": "jarvis", "version": "0.0.1"}) + "\n",
                encoding="utf-8",
            )
            (destination / "obsolete.txt").write_text("old\n", encoding="utf-8")

            with (
                mock.patch.object(installer.Path, "home", return_value=fake_home),
                mock.patch.object(
                    installer, "find_codex_cli", return_value="codex.cmd"
                ),
                mock.patch.object(installer, "add_plugin") as add_plugin,
            ):
                exit_code = installer.main([])

            self.assertEqual(exit_code, 0)
            installer.validate_bundle(destination)
            self.assertFalse((destination / "obsolete.txt").exists())
            self.assertEqual(
                len(list((fake_home / "plugins").glob("jarvis.backup-*"))), 1
            )
            installed_hooks = json.loads(
                (destination / "hooks" / "hooks.json").read_text(encoding="utf-8")
            )["hooks"]
            self.assertNotIn(
                "additionalContextLimit",
                installed_hooks["PostCompact"][0]["hooks"][0],
            )
            add_plugin.assert_called_once_with("codex.cmd", "personal")


if __name__ == "__main__":
    unittest.main()
