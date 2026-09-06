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

    def test_shell_wrappers_and_delivery_do_not_need_action_permission(self):
        for payload in (
            {"tool_name": "exec_command", "tool_input": {"cmd": "python3 build.py"}},
            {"tool_name": "exec_command", "tool_input": {"cmd": "git push -u origin feature/task"}},
            {"tool_name": "exec_command", "tool_input": {"cmd": "gh pr create --title change --body result"}},
            {"tool_name": "functions.exec", "tool_input": {"code": 'text(await tools.exec_command({cmd: "git status"}));'}},
            {"tool_name": "tickets.update_issue", "tool_input": {}},
        ):
            with self.subTest(payload=payload):
                self.assert_advisory(self.run_policy(payload=payload))
        self.assertIsNone(self.run_policy({**self.state, "action": self.action},
                                         {"tool_name": "exec_command", "tool_input": {"cmd": "python3 build.py"}}))

    def test_agent_action_labels_do_not_revoke_delegation(self):
        for payload in (
            self.payload,
            {"tool_name": "exec_command", "tool_input": {"cmd": "git push"}},
            {"tool_name": "tickets.update_issue", "tool_input": {}},
        ):
            for impact in ("non-source", "source-confirmed"):
                state = {**self.state, "action": {**self.action, "impact": impact, "paths": []}}
                with self.subTest(payload=payload, impact=impact):
                    self.assert_advisory(self.run_policy(state, payload))

    def test_persistence_failure_does_not_revoke_delegation(self):
        state = {**self.state, "recovery": {"reason": "persistence-failed"}}
        for payload in (self.payload, {"tool_name": "functions.exec", "tool_input": {"code": "repair()"}}):
            self.assert_advisory(self.run_policy(state, payload))

    def test_user_stop_still_blocks_work_and_permits_scoped_record_repair(self):
        record_payload = {**self.payload, "tool_input": f"*** Update File: {self.record}\n"}
        state = {**self.state, "recovery": {"reason": "user-stop"}}
        for payload in (self.payload, record_payload,
                        {"tool_name": "functions.exec", "tool_input": {"code": "work()"}},
                        {"tool_name": "exec_command", "tool_input": {"cmd": "git push"}}):
            self.assertEqual(self.run_policy(state, payload)["hookSpecificOutput"]["permissionDecision"], "deny")
        state["write_transaction"] = {"paths": [self.record]}
        self.assertIsNone(self.run_policy(state, record_payload))
        self.assertEqual(self.run_policy(state)["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
