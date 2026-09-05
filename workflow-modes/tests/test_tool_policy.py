from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tool_policy import is_mutating_tool, mutation_classes, paths_for_tool, shell_segments


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

    def test_common_read_pipelines_and_labels(self) -> None:
        for command in (
            "printf '%s\\n' '--- labels ---'; rg -n needle apps | head -n 400; sed -n '1,280p' file.md",
            "rg --files apps | sort", "rg --files | sort -ru",
            "sort -k 2 -t ':' data.txt", "sort --unique data.txt", "sort -k2,2nr data.txt",
            "nl -ba app.ts | sed -n '45,70p;420,475p'",
            "sed -n '45,70p;420,475p' app.ts", "sed -n '1,$p' app.ts",
            "echo labels; rg --files", "printf -- '%s' '-v'",
            "rg --files apps\nsed -n '1,20p' app.ts",
            "rg --files \\\napps |\n sort",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_mutating_tool(self.shell(command)))

    def test_quoted_shell_characters_are_arguments(self) -> None:
        for command in (
            "rg -n 'a>b|c<d' app.ts", 'rg -n "a>b" app.ts',
            "rg -F '$(example)' app.ts", "rg -F '`example`' app.ts",
            r"rg 'a\b' app.ts", r"rg a\>b app.ts",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_mutating_tool(self.shell(command)))
        self.assertEqual(shell_segments("rg '|' app.ts | head"), [["rg", "|", "app.ts"], ["head"]])

    def test_read_variants_cannot_hide_writes_or_execution(self) -> None:
        for command in (
            "sort data.txt -o result.txt", "sort -oresult.txt data.txt",
            "sort -ro result.txt data.txt", "sort --output=result.txt data.txt",
            "sort --compress-program=helper data.txt",
            "printf -v variable '%s' value", "printf '%n' variable",
            "sed -n '1,20p' app.ts -i", "sed -n '1,20p' app.ts -i.bak",
            "sed -n '1,20p' app.ts -e 'w output'",
            "sed -n '1,20p' app.ts --expression='w output'",
            "sed -n '1,20p' app.ts -f program.sed", "sed -n '1,20p;w output' app.ts",
            "rg needle app.ts > output", "cat <(python3 change.py)",
            'rg "$(python3 change.py)" app.ts', 'rg "`change`" app.ts',
            'rg "${value:=changed}" app.ts', "rg $pattern app.ts",
            "rg needle app.ts\npython3 change.py", "echo ok; touch file",
            "rg 'unterminated", "rg --files # comment\ntouch file",
            "rg -nz needle app.ts", "file -C -m magic", "file -z archive.gz",
        ):
            with self.subTest(command=command):
                self.assertTrue(is_mutating_tool(self.shell(command)))

    def test_researched_read_utilities(self) -> None:
        for command in (
            "cut -d: -f1 data | sort | uniq -c", "tr -d '\\r' | wc -l",
            "paste a b", "join a b", "comm -12 a b", "cmp a b",
            "fold -w 80 data", "fmt -w 80 data", "expand data", "unexpand data",
            "tac data", "od -An -tx1 data", "cksum data", "shasum -a 256 data",
            "md5sum data", "sha1sum data", "sha224sum data", "sha256sum data",
            "sha384sum data", "sha512sum data", "base64 data", "base64 --decode data",
            "base32 -d data", "uniq -f1 data", "uniq --check-chars=3 data",
            "readlink -f path", "realpath path", "basename path", "dirname path",
            "du -sh .", "df -h", "id", "groups", "whoami", "uname -a", "arch",
            "nproc", "printenv LANG", "test -f data", "[ -d src ]", "seq 1 10",
            "ps -eo pid,comm", "uptime", "date -u +%FT%TZ", "date -r 0 +%s",
            "find . -maxdepth 2 -type f -name '*.py' -print",
            r"find -L src \( -name '*.py' -o -name '*.ts' \) -print0",
            "find . -path './.git' -prune -o -type f -printf '%p\\n'",
            "jq -r '.items[] | select(.value > 0)' data.json",
            "jq --arg name value --argjson n 1 '.[$name] = $n' data.json",
            "jq -n --slurpfile rows data.json '$rows | length'",
            "jq -f filter.jq data.json", "jq --indent 4 '.' data.json",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_mutating_tool(self.shell(command)))

    def test_researched_utilities_reject_output_and_action_variants(self) -> None:
        for command in (
            "uniq input output", "uniq -c input output", "uniq -- input output",
            "base64 -o output input", "base64 --output=output input",
            "date -s tomorrow", "date 090606002026", "date --set=tomorrow",
            "find . -delete", "find . -exec touch output ';'", "find . -execdir helper '+'",
            "find . -fprint output", "find . -fprintf output '%p'", "find . -fls output",
            "find . -ok helper ';'", "sort --unknown input", "uniq --unknown input",
            "jq --unknown '.' data.json", "jq --arg name", "sort -k",
            "awk '{print > \"output\"}' data", "awk 'BEGIN {system(\"helper\")}'",
            "yq -i '.a = 1' data.yml", "xargs touch", "tee output",
        ):
            with self.subTest(command=command):
                self.assertTrue(is_mutating_tool(self.shell(command)))

    def test_additional_git_read_forms_preserve_mutation_boundary(self) -> None:
        for command in (
            "git blame app.ts", "git annotate app.ts", "git shortlog -sn", "git describe --tags",
            "git rev-list --count HEAD", "git for-each-ref", "git count-objects -v",
            "git cat-file -p HEAD", "git diff-files", "git diff-index HEAD", "git diff-tree HEAD",
            "git stash list", "git stash show -p", "git tag --list 'v*'", "git symbolic-ref HEAD",
        ):
            with self.subTest(command=command):
                self.assertFalse(is_mutating_tool(self.shell(command)))
        for command in (
            "git branch --list --delete topic", "git config --get key --unset other",
            "git tag --list --delete v1", "git symbolic-ref HEAD refs/heads/main",
            "git cat-file --filters HEAD:file", "git stash drop", "git log --output=out",
        ):
            with self.subTest(command=command):
                self.assertTrue(is_mutating_tool(self.shell(command)))

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
