from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "kiro" / "skills"
EXPECTED = {
    "workflow-discuss": {"SKILL.md", "references/tracker.md", "references/actions.md"},
    "workflow-plan": {"SKILL.md", "references/plan-record.md", "references/phase-planning.md"},
    "workflow-execute": {"SKILL.md", "references/implementation.md", "references/completion.md"},
}
PROHIBITED = (
    "$discuss",
    "$plan",
    "$execute",
    "PostCompact",
    "<user-home>/plugins/workflow-modes",
    ".codex/",
    "codex plugin",
)


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("missing YAML frontmatter")
    return dict(line.split(":", 1) for line in match.group(1).splitlines())


class KiroSkillBundleTests(unittest.TestCase):
    def test_complete_namespaced_bundles(self) -> None:
        self.assertEqual(set(EXPECTED), {path.name for path in SKILLS.iterdir()})
        for name, expected in EXPECTED.items():
            root = SKILLS / name
            actual = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(expected, actual)
            metadata = {
                key.strip(): value.strip()
                for key, value in frontmatter((root / "SKILL.md").read_text()).items()
            }
            self.assertEqual(name, metadata["name"])
            self.assertLessEqual(len(metadata["name"]), 64)
            self.assertLessEqual(len(metadata["description"]), 1024)

    def test_references_are_local_and_resolvable(self) -> None:
        pattern = re.compile(r"\[[^\]]+\]\((references/[^)]+\.md)\)")
        for name, expected in EXPECTED.items():
            root = SKILLS / name
            references = set(pattern.findall((root / "SKILL.md").read_text()))
            self.assertEqual(
                {path for path in expected if path.startswith("references/")},
                references,
            )
            for reference in references:
                self.assertTrue((root / reference).is_file())

    def test_operational_surface_is_kiro_native(self) -> None:
        for path in SKILLS.rglob("*.md"):
            text = path.read_text()
            for token in PROHIBITED:
                self.assertNotIn(token, text, f"{token!r} in {path}")
        for root in SKILLS.iterdir():
            text = (root / "SKILL.md").read_text()
            self.assertIn(f"/{root.name}", text)
            self.assertIn(".kiro/workflow-modes/scripts/", text)
            self.assertIn("warning-only", text)

    def test_record_v4_contract_survives(self) -> None:
        text = "\n".join(path.read_text() for path in SKILLS.rglob("*.md"))
        for token in (
            "workflow-record version:4",
            "workflow-active-snapshot:start version:2",
            "workflow-manifest:start",
            "write-open",
            "write-close",
            "rules-sync",
            "action-open",
            "checkpoint",
            "transition execute",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
