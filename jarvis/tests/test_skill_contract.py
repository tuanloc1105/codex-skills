from pathlib import Path
import unittest


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "jarvis" / "SKILL.md"


class JarvisSkillContractTests(unittest.TestCase):
    def test_main_thread_discloses_each_supervisor_interaction(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("Immediately before contacting Jarvis", skill)
        self.assertIn("After Jarvis responds", skill)
        self.assertIn("baseline review and every later checkpoint", skill)
        self.assertIn("using the user's language", skill)

    def test_review_block_has_stable_user_visible_contract(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("Every completed block must identify the checkpoint", skill)
        for field in ("`Main → Jarvis`", "`Jarvis`", "`Reason`", "`Next`"):
            with self.subTest(field=field):
                self.assertIn(field, skill)
        self.assertIn("keep the verdict token unchanged", skill)

    def test_review_block_preserves_supervisor_privacy_boundary(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("Do not paste the full supervisor exchange", skill)
        self.assertIn("expose hidden reasoning", skill)
        self.assertIn("Do not leave supervisor calls visible only as subagent", skill)


if __name__ == "__main__":
    unittest.main()
