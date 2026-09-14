import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "jira_completion_cases.json").read_text()
)


def jira_duration_seconds(value: str) -> int:
    units = {"w": 5 * 8 * 3600, "d": 8 * 3600, "h": 3600, "m": 60}
    tokens = re.findall(r"(\d+)\s*([wdhm])", value)
    if not tokens or "".join(f"{amount}{unit}" for amount, unit in tokens) != re.sub(r"\s+", "", value):
        raise ValueError(f"unsupported Jira duration: {value}")
    return sum(int(amount) * units[unit] for amount, unit in tokens)


def atomic_payload(case: dict) -> dict:
    if jira_duration_seconds(case["originalEstimate"]) != case["timeoriginalestimate"]:
        raise ValueError("canonical duration does not match raw Original Estimate seconds")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{4}", case["started"]):
        raise ValueError("started must match Jira yyyy-MM-dd'T'HH:mm:ss.SSSZ")
    return {
        "transition": {"id": case["transitionId"]},
        "update": {
            "worklog": [
                {
                    "add": {
                        "timeSpent": case["originalEstimate"],
                        "started": case["started"],
                    }
                }
            ]
        },
    }


def next_actions_after_mutation(result: str) -> list[str]:
    if result in {"rejected", "uncertain"}:
        return ["read_status", "read_timespent", "read_complete_worklogs", "stop"]
    return ["verify_status", "verify_timespent", "verify_complete_worklogs"]


class JiraCompletionPolicyTest(unittest.TestCase):
    def test_canonical_three_hours_and_atomic_payload(self):
        case = FIXTURES["canonical_three_hours"]
        self.assertEqual(jira_duration_seconds(case["originalEstimate"]), 10800)

        payload = atomic_payload(case)
        operations = payload["update"]["worklog"]
        self.assertEqual(len(operations), 1)
        self.assertEqual(
            operations[0],
            {"add": {"timeSpent": "3h", "started": case["started"]}},
        )
        self.assertNotIn("timeSpentSeconds", operations[0]["add"])
        self.assertNotIn("timespent", payload)

    def test_mismatched_duration_is_rejected(self):
        case = {**FIXTURES["mismatched_duration"], "started": "2026-09-14T10:15:30.000+0700", "transitionId": "3"}
        with self.assertRaisesRegex(ValueError, "does not match"):
            atomic_payload(case)

    def test_colonized_offset_is_rejected(self):
        case = {**FIXTURES["canonical_three_hours"], "started": "2026-09-14T10:15:30.000+07:00"}
        with self.assertRaisesRegex(ValueError, "must match Jira"):
            atomic_payload(case)

    def test_missing_milliseconds_is_rejected(self):
        case = {**FIXTURES["canonical_three_hours"], "started": "2026-09-14T10:15:30+0700"}
        with self.assertRaisesRegex(ValueError, "must match Jira"):
            atomic_payload(case)

    def test_rejection_and_uncertainty_cannot_retry(self):
        expected = ["read_status", "read_timespent", "read_complete_worklogs", "stop"]
        self.assertEqual(next_actions_after_mutation("rejected"), expected)
        self.assertEqual(next_actions_after_mutation("uncertain"), expected)
        self.assertNotIn("retry", expected)

    def test_success_verifies_count_duration_and_time_spent(self):
        case = FIXTURES["canonical_three_hours"]
        result = FIXTURES["successful_post_read"]
        self.assertEqual(result["status"], "Done")
        self.assertEqual(len(result["afterWorklogs"]) - result["beforeWorklogCount"], 1)
        self.assertEqual(result["afterWorklogs"][-1]["timeSpentSeconds"], case["timeoriginalestimate"])
        self.assertEqual(result["timespent"], result["afterWorklogs"][-1]["timeSpentSeconds"])

    def test_policy_documents_payload_and_no_retry_contract(self):
        policy = (SKILL_ROOT / "references" / "core-policy.md").read_text()
        self.assertIn('"timeSpent": "<canonical-original-estimate>"', policy)
        self.assertIn("date '+%Y-%m-%dT%H:%M:%S.000%z'", policy)
        self.assertIn('"started": "2026-09-14T14:59:33.000+0700"', policy)
        self.assertIn("exact count increase of one", policy)
        self.assertIn("Never automatically retry, switch payload variants", policy)


if __name__ == "__main__":
    unittest.main()
