from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from bundle_schema import phase_errors


def phase(identity: str, dependencies: str = "None", wave: int = 1) -> str:
    return (f"# {identity}: Phase\nStatus: Pending\nDepends on: {dependencies}\nWave: {wave}\n"
            "Subagent: Not eligible — shared work\nOwned scope: app.py\nProduces: behavior\n")


class BundleSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.files = {
            "plan.md": "| ID | Phase file |\n| --- | --- |\n| P01 | [P01](phases/P01-first.md) |\n| P02 | [P02](phases/P02-second.md) |\n",
            "phases/P01-first.md": phase("P01"),
            "phases/P02-second.md": phase("P02", "P01", 2),
        }

    def test_valid_index_uses_phase_metadata_once(self) -> None:
        self.assertEqual(phase_errors(self.files), [])
        self.assertEqual(phase_errors({"plan.md": "- [ ] One linear task\n"}), [])

    def test_both_directions_of_phase_links(self) -> None:
        for change in ("missing", "unlinked"):
            with self.subTest(change=change):
                files = dict(self.files)
                if change == "missing":
                    files["plan.md"] += "[P03](phases/P03-missing.md)\n"
                else:
                    files["phases/P03-other.md"] = phase("P03")
                self.assertIn("phase links differ", "; ".join(phase_errors(files)))

    def test_wrong_wave_unknown_dependency_and_cycle(self) -> None:
        for content, message in ((phase("P02", "P01", 1), "Wave must be 2"), (phase("P02", "P99", 2), "unknown Depends on"), (phase("P02", "P02", 2), "dependency cycle")):
            with self.subTest(message=message):
                files = {**self.files, "phases/P02-second.md": content}
                self.assertIn(message, "; ".join(phase_errors(files)))

    def test_empty_or_duplicate_metadata_rejected(self) -> None:
        for content in (phase("P01").replace("Owned scope: app.py", "Owned scope:"), phase("P01") + "Wave: 1\n"):
            files = {**self.files, "phases/P01-first.md": content}
            self.assertIn("must occur once with a value", "; ".join(phase_errors(files)))

    def test_legacy_table_must_match_phase_file(self) -> None:
        header = "| ID | Phase file | Depends on | Wave | Owned scope | Produces |\n| --- | --- | --- | --- | --- | --- |\n"
        rows = "| P01 | phases/P01-first.md | None | 1 | app.py | behavior |\n| P02 | phases/P02-second.md | P01 | 2 | app.py | behavior |\n"
        files = {**self.files, "plan.md": header + rows}
        self.assertEqual(phase_errors(files), [])
        for old, new, field in (("| P01 | 2", "| None | 2", "Depends on"), ("| app.py |", "| other.py |", "Owned scope"), ("| behavior |", "| different |", "Produces")):
            with self.subTest(field=field):
                files["plan.md"] = header + rows.replace(old, new)
                self.assertIn(field + " differs", "; ".join(phase_errors(files)))

    def test_table_declared_id_without_file_is_rejected(self) -> None:
        self.files["plan.md"] += "| P03 | TBD |\n"
        self.assertIn("P03 has no phase file", "; ".join(phase_errors(self.files)))

    def test_wrong_phase_link_for_existing_id(self) -> None:
        self.files["plan.md"] += "| P01 | phases/P02-second.md |\n"
        self.assertIn("wrong phase file", "; ".join(phase_errors(self.files)))


if __name__ == "__main__":
    unittest.main()
