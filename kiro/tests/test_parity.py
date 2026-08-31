from __future__ import annotations

import difflib
import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAIRS = {
    ROOT / "discuss": ROOT / "kiro/skills/workflow-discuss",
    ROOT / "plan": ROOT / "kiro/skills/workflow-plan",
    ROOT / "execute": ROOT / "kiro/skills/workflow-execute",
}
EXPECTED = {
    "discuss": {"SKILL.md", "references/tracker.md", "references/actions.md"},
    "plan": {"SKILL.md", "references/plan-record.md", "references/phase-planning.md"},
    "execute": {"SKILL.md", "references/implementation.md", "references/completion.md"},
}


@dataclass(frozen=True)
class Drift:
    path: str
    category: str
    line: str


def normalize(text: str) -> str:
    for target, source in (
        ("/workflow-discuss", "$discuss"),
        ("/workflow-plan", "$plan"),
        ("/workflow-execute", "$execute"),
        ("Kiro", "Codex"),
        ("an incremental teaching workflow", "$teach-for-understanding"),
        ("the required simplification review", "$simplify"),
        ("the repository agent-documentation workflow", "$update-agent-docs"),
        ("a focused security review", "$security-review"),
    ):
        text = text.replace(target, source)
    return text


def without_runtime(text: str) -> str:
    return re.sub(
        r"## Workflow Modes Hook\n.*?(?=\n## Reference Routing)",
        "## Workflow Modes Hook\n<RUNTIME-ADAPTATION>\n",
        text,
        flags=re.DOTALL,
    )


def classify_line(line: str) -> str:
    if line.startswith(("--- ", "+++ ", "@@", " ")):
        return "metadata"
    if "name: workflow-" in line or re.search(r"name: (discuss|plan|execute)", line):
        return "namespace"
    if any(
        token in line
        for token in (
            "/workflow-",
            "$discuss",
            "$plan",
            "$execute",
            "Kiro",
            "Codex",
            ".kiro/workflow-modes",
            "recovery anchor",
            "warning-only",
        )
    ):
        return "runtime"
    if any(
        token in line
        for token in (
            "$simplify",
            "$update-agent-docs",
            "$security-review",
            "$teach-for-understanding",
            "simplification review",
            "agent-documentation workflow",
            "security review",
            "teaching workflow",
        )
    ):
        return "capability"
    return "unexpected"


def report_skill_drift() -> list[Drift]:
    report: list[Drift] = []
    for source_root, target_root in PAIRS.items():
        expected = EXPECTED[source_root.name]
        actual = {
            path.relative_to(target_root).as_posix()
            for path in target_root.rglob("*")
            if path.is_file()
        }
        if actual != expected:
            report.append(Drift(source_root.name, "unexpected", repr(sorted(actual))))
        for relative in sorted(expected):
            source = without_runtime(normalize((source_root / relative).read_text()))
            target = without_runtime(normalize((target_root / relative).read_text()))
            for line in difflib.unified_diff(
                source.splitlines(), target.splitlines(), lineterm=""
            ):
                category = classify_line(line)
                if category != "metadata":
                    report.append(Drift(relative, category, line))
    return report


class KiroParityTests(unittest.TestCase):
    def test_current_drift_is_classified(self) -> None:
        self.assertEqual(
            [],
            [item for item in report_skill_drift() if item.category == "unexpected"],
        )

    def test_classifier_detects_unexpected_contract_drift(self) -> None:
        self.assertEqual("unexpected", classify_line("+silently weaken validation"))
        self.assertEqual("runtime", classify_line("+invoke /workflow-execute"))
        self.assertEqual("capability", classify_line("+run the simplification review"))

    def test_runtime_neutral_references_match(self) -> None:
        for source_root, target_root in PAIRS.items():
            for relative in EXPECTED[source_root.name] - {"SKILL.md"}:
                self.assertEqual(
                    normalize((source_root / relative).read_text()),
                    normalize((target_root / relative).read_text()),
                    relative,
                )


if __name__ == "__main__":
    unittest.main()
