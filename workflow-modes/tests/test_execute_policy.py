from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import workflow_modes_hook as hook


class ExecutePolicyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.target = str(self.root / "app.py")
        self.record = str(self.root / "index.md")
        self.state = {"mode": "execute", "record": str(self.root), "action": None}
        self.action = {"impact": "source-confirmed", "paths": [self.target], "unscoped": []}
        self.payload = {"cwd": str(self.root), "tool_name": "apply_patch",
                        "tool_input": f"*** Update File: {self.target}\n"}

    def run_policy(self, state=None, payload=None, synced=True):
        with patch.object(hook, "record_is_synced", return_value=synced), patch.object(
            hook, "record_or_housekeeping_path", side_effect=lambda path, *_: path == self.record
        ):
            return hook.execute_mutation(deepcopy(state or self.state), payload or self.payload)

    def assert_advisory(self, output):
        self.assertIn("WORKFLOW_EXECUTE_ADVISORY", output["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("permissionDecision", output["hookSpecificOutput"])

    def test_file_bookkeeping_is_nonblocking(self):
        self.assert_advisory(self.run_policy())
        for changes in (
            {"rules_sync_required": True},
            {"write_transaction": {"paths": [self.record]}},
            {"action": {**self.action, "paths": []}},
        ):
            with self.subTest(changes=changes):
                self.assert_advisory(self.run_policy({**self.state, **changes}))
        self.assert_advisory(self.run_policy(synced=False))
        self.assertIsNone(self.run_policy({**self.state, "action": self.action}))

    def test_file_adapters_share_advisory_policy(self):
        for name, args in (
            ("Write", {"file_path": self.target}),
            ("mcp__files__move_file", {"source": self.target, "destination": str(self.root / "new.py")}),
        ):
            self.assert_advisory(self.run_policy(payload={"tool_name": name, "tool_input": args}))

    def test_shell_needs_action_but_not_separate_shell_class(self):
        payload = {"tool_name": "exec_command", "tool_input": {"cmd": "python3 build.py"}}
        self.assertEqual(self.run_policy(payload=payload)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(self.run_policy({**self.state, "action": self.action}, payload))

    def test_git_external_and_non_source_boundaries_remain(self):
        for payload in (
            {"tool_name": "exec_command", "tool_input": {"cmd": "git push"}},
            {"tool_name": "tickets.update_issue", "tool_input": {}},
        ):
            self.assertEqual(self.run_policy({**self.state, "action": self.action}, payload)["hookSpecificOutput"]["permissionDecision"], "deny")
        result = self.run_policy({**self.state, "action": {**self.action, "impact": "non-source"}})
        self.assertIn("WORKFLOW_SOURCE_CONFIRMATION_REQUIRED", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_suspension_only_allows_record_repair(self):
        record_payload = {**self.payload, "tool_input": f"*** Update File: {self.record}\n"}
        for reason in ("user-stop", "persistence-failed"):
            state = {**self.state, "recovery": {"reason": reason}}
            self.assertEqual(self.run_policy(state)["hookSpecificOutput"]["permissionDecision"], "deny")
            if reason == "persistence-failed":
                self.assert_advisory(self.run_policy(state, record_payload))
            else:
                self.assertEqual(self.run_policy(state, record_payload)["hookSpecificOutput"]["permissionDecision"], "deny")
            state["write_transaction"] = {"paths": [self.record]}
            self.assertIsNone(self.run_policy(state, record_payload))


if __name__ == "__main__":
    unittest.main()
