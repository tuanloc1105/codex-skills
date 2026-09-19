from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "launch_reviewer.py"
SPEC = importlib.util.spec_from_file_location("launch_reviewer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LaunchReviewerTests(unittest.TestCase):
    def make_bundle(self, root: Path, tracker_id: str = "tracker-123") -> Path:
        bundle = root / "bundle"
        (bundle / "reviews").mkdir(parents=True)
        (bundle / "index.md").write_text(
            "\n".join(
                [
                    "# Test Bundle",
                    "",
                    f"<!-- workflow-record version:4 kind:plan tracker-id:{tracker_id} -->",
                    "",
                    "<!-- workflow-manifest:start -->",
                    "index.md",
                    "evidence.md",
                    "reviews/CR-001.md",
                    "<!-- workflow-manifest:end -->",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (bundle / "evidence.md").write_text(
            "<!-- workflow-action:CR-001 status:open -->\n", encoding="utf-8"
        )
        (bundle / "reviews" / "CR-001.md").write_text(
            "# Codex Review CR-001\n", encoding="utf-8"
        )
        return bundle

    def test_validate_bundle_accepts_predeclared_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = self.make_bundle(Path(temp_dir))
            artifact = MODULE.validate_bundle(bundle, "tracker-123", "CR-001")
            self.assertEqual(artifact, "reviews/CR-001.md")

    def test_validate_bundle_rejects_tracker_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = self.make_bundle(Path(temp_dir))
            with self.assertRaisesRegex(ValueError, "tracker ID mismatch"):
                MODULE.validate_bundle(bundle, "wrong-tracker", "CR-001")

    def test_validate_bundle_requires_open_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = self.make_bundle(Path(temp_dir))
            (bundle / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "open review action"):
                MODULE.validate_bundle(bundle, "tracker-123", "CR-001")

    def test_reviewer_command_keeps_bundle_as_only_workspace(self) -> None:
        command = MODULE.build_command(
            "codex",
            Path("/bundle"),
            "gpt-5.6-sol",
            "high",
            Path("/runtime/review-receipt.json"),
        )
        self.assertNotIn("--add-dir", command)
        self.assertNotIn("--ephemeral", command)
        self.assertEqual(command[command.index("-C") + 1], "/bundle")
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")

    def test_receipt_schema_is_valid_json(self) -> None:
        schema_path = SCRIPT.parents[1] / "references" / "review-receipt.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])

    def test_dry_run_builds_isolated_reviewer_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundle = self.make_bundle(root)
            runtime = root / "runtime"
            argv = [
                "launch_reviewer.py",
                "--bundle",
                str(bundle),
                "--tracker-id",
                "tracker-123",
                "--review-id",
                "CR-001",
                "--runtime-dir",
                str(runtime),
                "--dry-run",
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(MODULE, "validate_model"),
                mock.patch("builtins.print") as print_mock,
            ):
                self.assertEqual(MODULE.main(), 0)

            metadata = json.loads(print_mock.call_args.args[0])
            command = metadata["command"]
            self.assertEqual(metadata["review_artifact"], "reviews/CR-001.md")
            self.assertNotIn("--add-dir", command)
            self.assertEqual(command[command.index("-C") + 1], str(bundle.resolve()))
            self.assertEqual(
                command[command.index("--sandbox") + 1], "workspace-write"
            )


if __name__ == "__main__":
    unittest.main()
