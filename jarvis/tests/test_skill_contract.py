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


if __name__ == "__main__":
    unittest.main()
