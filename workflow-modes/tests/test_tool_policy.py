from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tool_policy import is_mutating_tool, mutation_classes, paths_for_tool


class ToolPolicyTests(unittest.TestCase):
    def shell(self, command: str) -> dict:
        return {"tool_name": "functions.exec_command", "tool_input": {"cmd": command}}

    def test_read_commands_and_git_options(self) -> None:
        for command in (
            "rg --files discuss plan", "git -C /repo status --short",
            "git --no-pager diff --check", "git worktree list --porcelain",
            "sed -n '10,30p' app.py", "cat index.md; git log -1", "git branch --show-current", "git config --get user.name",
            "gh pr view 1 --json body", "glab mr list", "acli jira workitem view EX-1",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_mutating_tool(self.shell(command)))

    def test_scripts_wrappers_and_unknown_commands_require_scope(self) -> None:
        for command in (
            "python3 script.py", "python3 -c 'print(1)'", "node script.js",
            "env MODE=test python3 script.py", "npm test", "make check",
            "sed -i 's/a/b/' app.py", "git -c alias.foo=commit foo",
            "rg --pre helper needle", "cat $(python3 change.py)",
        ):
            with self.subTest(command=command):
                self.assertTrue(is_mutating_tool(self.shell(command)))

    def test_git_mutation_with_options_is_classified_as_git(self) -> None:
        for command in ("git -C /repo commit -m change", "git --git-dir=/repo/.git reset", "git worktree add /task", "git remote add upstream url"):
            with self.subTest(command=command):
                self.assertEqual(mutation_classes(self.shell(command)), {"git"})

    def test_compound_commands_require_every_visible_class(self) -> None:
        self.assertEqual(mutation_classes(self.shell("git status; git commit -m change; gh pr create; python3 script.py")), {"git", "external", "shell"})
        self.assertEqual(mutation_classes(self.shell("git commit -m change\npython3 script.py")), {"git", "shell"})

    def test_patch_adapters_cover_raw_input_and_move_destination(self) -> None:
        patch = "*** Update File: old.py\n*** Move to: new.py\n"
        for tool_input in (patch, {"input": patch}, {"patch": patch}, {"command": patch}):
            self.assertEqual(paths_for_tool({"tool_name": "functions.apply_patch", "tool_input": tool_input}), {"old.py", "new.py"})

    def test_file_tool_adapters(self) -> None:
        self.assertEqual(paths_for_tool({"tool_name": "Write", "tool_input": {"file_path": "app.py"}}), {"app.py"})
        self.assertEqual(paths_for_tool({"tool_name": "mcp__files__move_file", "tool_input": {"source": "old.py", "destination": "new.py"}}), {"old.py", "new.py"})

    def test_opaque_evaluation_and_stdin_are_not_reads(self) -> None:
        for name in ("functions.exec", "mcp__cua_repl.js", "mcp__figma__use_figma"):
            self.assertTrue(is_mutating_tool({"tool_name": name, "tool_input": {"code": "anything"}}))
        self.assertFalse(is_mutating_tool({"tool_name": "write_stdin", "tool_input": {"chars": ""}}))
        self.assertTrue(is_mutating_tool({"tool_name": "write_stdin", "tool_input": {"chars": "run\n"}}))

    def test_flattened_names_keep_shell_and_patch_adapters(self) -> None:
        self.assertTrue(is_mutating_tool({"tool_name": "functions_exec_command", "tool_input": {"cmd": "python3 change.py"}}))
        self.assertEqual(paths_for_tool({"tool_name": "functions_apply_patch", "tool_input": "*** Update File: app.py\n"}), {"app.py"})
        self.assertFalse(is_mutating_tool({"tool_name": "functions_write_stdin", "tool_input": {"chars": "\x03"}}))

    def test_namespaced_coordination_stays_readonly(self) -> None:
        for name in ("collaboration.send_message", "functions.request_user_input_async", "functions.update_goal"):
            self.assertFalse(is_mutating_tool({"tool_name": name}))


if __name__ == "__main__":
    unittest.main()
