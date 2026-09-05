from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK = PLUGIN_ROOT / "scripts" / "workflow_modes_hook.py"
CONTROL = PLUGIN_ROOT / "scripts" / "workflow_modes_control.py"
HOOKS = PLUGIN_ROOT / "hooks" / "hooks.json"
MARKER = "workflow-modes-v1"
MODE_REFERENCES = {
    "discuss": ("references/tracker.md", "references/actions.md"),
    "plan": ("references/plan-record.md", "references/phase-planning.md"),
    "execute": ("references/implementation.md", "references/completion.md"),
}


class WorkflowModesHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.env = {**os.environ, "PLUGIN_DATA": self.temp_dir.name}
        self.session_id = "workflow-session"
        self.cwd = Path(self.temp_dir.name)
        self.record = self.cwd / "discussion" / "test-record"
        self.index = self.record / "index.md"

    def run_hook(self, event: str, **fields: object) -> dict[str, object] | None:
        payload = {
            "session_id": self.session_id,
            "cwd": str(self.cwd),
            "hook_event_name": event,
            **fields,
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), text=True,
            capture_output=True, env=self.env, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def control(self, *args: str) -> dict[str, object] | None:
        command = " ".join([sys.executable, f'"{CONTROL}"', *args, "--marker", MARKER])
        return self.run_hook("PreToolUse", tool_name="exec_command", tool_input={"cmd": command})

    def patch(self, *paths: str) -> dict[str, object] | None:
        command = "\n".join(f"*** Update File: {path}" for path in paths)
        return self.run_hook("PreToolUse", tool_name="apply_patch", tool_input={"command": command})

    def index_content(
        self, mode: str, *, status: str | None = None,
        manifest: tuple[str, ...] | None = None,
    ) -> str:
        kind = "discuss" if mode == "discuss" else "plan"
        if manifest is None:
            manifest = (
                ("index.md", "context.md", "decisions.md", "actions.md", "evidence.md")
                if kind == "discuss"
                else ("index.md", "context.md", "decisions.md", "plan.md", "verification.md", "evidence.md")
            )
        profile = "Durable" if mode == "execute" else "Lightweight"
        if mode == "discuss":
            lifecycle = "Mode: $discuss\nMode status: Active\nExecute mode: Inactive\n"
        elif mode == "execute":
            lifecycle = "Status: In progress\nExecute mode: Active\n"
        else:
            lifecycle = f"Status: {status or 'Draft'}\nPlan mode: Active\nExecute mode: Inactive\n"
        return (
            f"<!-- workflow-record version:4 kind:{kind} tracker-id:TEST-TRACKER -->\n"
            + lifecycle + "Active action: None\n"
            + "<!-- workflow-active-snapshot:start version:2 -->\n"
            + f"Profile: {profile}\nRequired references: {', '.join(MODE_REFERENCES[mode])}\n"
            + "Goal: Test workflow\nCurrent state: Active\nAccepted decisions: None\n"
            + "Open items: None\nNext safe action: Continue\n"
            + "<!-- workflow-active-snapshot:end -->\n"
            + "<!-- workflow-manifest:start -->\n" + "\n".join(manifest)
            + "\n<!-- workflow-manifest:end -->\n"
        )

    def create_bundle(self, mode: str = "discuss", **kwargs: object) -> None:
        self.record.mkdir(parents=True, exist_ok=True)
        content = self.index_content(mode, **kwargs)
        self.index.write_text(content, encoding="utf-8")
        start = content.index("<!-- workflow-manifest:start -->") + len("<!-- workflow-manifest:start -->")
        end = content.index("<!-- workflow-manifest:end -->", start)
        for entry in (line.strip() for line in content[start:end].splitlines() if line.strip()):
            path = self.record / entry
            if path == self.index:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.stem.title()}\n", encoding="utf-8")

    def activate(self, mode: str) -> None:
        self.create_bundle(mode)
        self.assertIn(
            "WORKFLOW_MODE_ACTIVE",
            json.dumps(self.control("activate", mode, "--record", str(self.record))),
        )
        self.assertIn(
            "WORKFLOW_RECORD_SYNCED",
            json.dumps(self.control("sync", "--record", str(self.index))),
        )
        arguments = tuple(
            item for reference in MODE_REFERENCES[mode] for item in ("--reference", reference)
        )
        self.assertIn(
            "WORKFLOW_RULES_SYNCED",
            json.dumps(self.control("rules-sync", "--record", str(self.record), *arguments)),
        )

    def revision(self) -> str:
        digest = hashlib.sha256()
        files = {
            path.relative_to(self.record).as_posix(): path.read_text(encoding="utf-8")
            for path in self.record.rglob("*.md")
        }
        for name in sorted(files):
            digest.update(name.encode("utf-8")); digest.update(b"\0")
            digest.update(hashlib.sha256(files[name].encode("utf-8")).digest())
        return "sha256:" + digest.hexdigest()

    def write_open(self, *extra_paths: Path) -> dict[str, object] | None:
        args = ["write-open", "--record", str(self.record), "--previous-revision", self.revision()]
        for path in extra_paths:
            args.extend(("--path", str(path)))
        return self.control(*args)

    def test_help_through_hook_and_cli_preserves_all_session_state(self) -> None:
        def state():
            database = self.cwd / "workflow-modes.sqlite3"
            if not database.exists():
                return []
            with sqlite3.connect(database) as connection:
                return connection.execute("SELECT * FROM sessions").fetchall()

        commands = ("activate", "transition", "plan-init", "plan-cancel", "suspend",
                    "recover", "action-open", "action-close", "action-abort", "sync",
                    "rules-sync", "write-open", "write-close", "checkpoint", "snapshot", "deactivate")
        for mode in ("inactive", "active", "suspended"):
            if mode == "active":
                self.activate("execute")
            elif mode == "suspended":
                self.control("suspend", "--record", str(self.record), "--reason", "user-stop")
            before = state()
            for command in (None, *commands):
                for flag in ("--help", "-h"):
                    args = [flag] if command is None else [command, flag]
                    with self.subTest(mode=mode, args=args):
                        self.assertIn("WORKFLOW_CONTROL_HELP", json.dumps(self.control(*args)))
                        result = subprocess.run(
                            [sys.executable, str(CONTROL), *args, "--marker", MARKER],
                            capture_output=True, text=True, env=self.env,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("usage:", result.stdout)
                        self.assertEqual(state(), before)
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.patch("app.py")))

    def test_help_does_not_exempt_unsafe_commands(self) -> None:
        fake = self.cwd / "workflow_modes_control.py"
        fake.write_text("print('untrusted')")
        for command in (
            f'{sys.executable} "{fake}" --help --marker {MARKER}',
            f'bash "{CONTROL}" --help --marker {MARKER}',
            f'{sys.executable} "{CONTROL}" --help --marker {MARKER}; touch bad',
            f'{sys.executable} "{CONTROL}" --help --marker {MARKER} > bad',
        ):
            with self.subTest(command=command):
                output = self.run_hook("PreToolUse", tool_name="exec_command", tool_input={"cmd": command})
                self.assertIn("WORKFLOW_CONTROL_AMBIGUOUS", json.dumps(output))
        for args in (("nonexistent", "--help"), ("--help", "activate")):
            self.assertIn("WORKFLOW_CONTROL_INVALID", json.dumps(self.control(*args)))

    def test_dormant_until_activation(self) -> None:
        self.assertIsNone(self.patch("app.py"))
        self.assertIsNone(self.run_hook("PostCompact"))

    def test_activation_accepts_bundle_or_index_path(self) -> None:
        self.create_bundle("discuss")
        output = self.control("activate", "discuss", "--record", str(self.index))
        self.assertIn(str(self.record), json.dumps(output))
        self.assertIn(
            "WORKFLOW_RECORD_SYNCED",
            json.dumps(self.control("sync", "--record", str(self.record))),
        )

    def test_activation_rejects_single_file_v3(self) -> None:
        legacy = self.cwd / "tracker.md"
        legacy.write_text("<!-- workflow-record version:3 kind:discuss tracker-id:T -->\n", encoding="utf-8")
        denied = self.control("activate", "discuss", "--record", str(legacy))
        self.assertIn("WORKFLOW_RECORD_UNREADABLE", json.dumps(denied))

    def test_activation_rejects_missing_or_unsafe_manifest(self) -> None:
        self.record.mkdir(parents=True)
        self.index.write_text(
            "<!-- workflow-record version:4 kind:discuss tracker-id:T -->\n"
            "Mode: $discuss\nMode status: Active\n", encoding="utf-8",
        )
        denied = self.control("activate", "discuss", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_UNREADABLE", json.dumps(denied))
        outside = self.cwd / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        self.index.write_text(
            self.index.read_text(encoding="utf-8")
            + "<!-- workflow-manifest:start -->\nindex.md\n../outside.md\n<!-- workflow-manifest:end -->\n",
            encoding="utf-8",
        )
        denied = self.control("activate", "discuss", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_UNREADABLE", json.dumps(denied))

    def test_post_compact_requires_full_bundle_sync(self) -> None:
        self.activate("discuss")
        output = self.run_hook("PostCompact")
        self.assertIn("sync_status=record", json.dumps(output))
        denied = self.control("sync", "--record", str(self.record), "--scope", "snapshot")
        self.assertIn("currently required record scope", json.dumps(denied))
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch("app.py")))

    def test_post_compact_resume_to_checkpoint_in_all_modes(self) -> None:
        def accepted(expected: str, *args: str) -> None:
            self.assertIn(expected, json.dumps(self.control(*args)))
            result = subprocess.run(
                [sys.executable, str(CONTROL), *args, "--marker", MARKER],
                capture_output=True, text=True, env=self.env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

        def read_file(path: Path) -> str:
            # Exercise the read tool boundary, then actually read the fixture.
            output = self.run_hook(
                "PreToolUse", tool_name="exec_command",
                tool_input={"cmd": f'cat "{path}"'},
            )
            self.assertIsNone(output)
            return path.read_text(encoding="utf-8")

        for mode in ("discuss", "plan", "execute"):
            with self.subTest(mode=mode):
                self.session_id = f"compact-{mode}"
                self.record = self.cwd / mode / "record"
                self.index = self.record / "index.md"
                self.activate(mode)
                target = self.cwd / (f"{mode}.md" if mode == "discuss" else f"{mode}.py")
                evidence = self.record / "evidence.md"
                self.write_open()
                self.index.write_text(self.index.read_text().replace(
                    "Next safe action: Continue",
                    "Next safe action: Continue\nSupporting skills: surgical-coding — inspect changes",
                ), encoding="utf-8")
                if mode != "plan":
                    evidence.write_text(
                        "# Evidence\n<!-- workflow-action:A001 status:open -->\n", encoding="utf-8",
                    )
                    self.index.write_text(self.index.read_text().replace(
                        "Active action: None", "Active action: A001",
                    ), encoding="utf-8")
                accepted("WORKFLOW_WRITE_CLOSED", "write-close", "--record", str(self.record))
                if mode != "plan":
                    accepted("WORKFLOW_ACTION_OPEN", "action-open", "--record", str(self.record),
                             "--evidence-id", "A001", "--impact",
                             "non-source" if mode == "discuss" else "source-confirmed", "--path", str(target))

                output = self.run_hook("PostCompact")
                message = output["systemMessage"]
                for value in (f"mode={mode}", str(self.record), "sync_status=record", "SKILL.md",
                              *MODE_REFERENCES[mode]):
                    self.assertIn(value, message)
                self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch(str(target))))
                self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.run_hook("Stop")))
                self.assertIn("WORKFLOW_RECORD_SYNC_REQUIRED", json.dumps(
                    self.control("sync", "--record", str(self.record), "--scope", "snapshot")))

                skill = PLUGIN_ROOT.parent / mode
                read_file(skill / "SKILL.md")
                for reference in MODE_REFERENCES[mode]:
                    read_file(skill / reference)
                for path in sorted(self.record.rglob("*.md")):
                    read_file(path)
                accepted("WORKFLOW_RECORD_SYNCED", "sync", "--record", str(self.record))
                self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch(str(target))))
                references = tuple(item for ref in MODE_REFERENCES[mode] for item in ("--reference", ref))
                accepted("WORKFLOW_RULES_SYNCED", "rules-sync", "--record", str(self.record), *references)
                if mode == "plan":
                    self.assertIn("WORKFLOW_PLAN_READ_ONLY", json.dumps(self.patch(str(target))))
                else:
                    # No reactivation or second action-open: the original scope survived.
                    self.assertIsNone(self.patch(str(target)))
                    self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(
                        self.patch("other.md" if mode == "discuss" else "other.py")))
                    target.write_text("# resumed action\n", encoding="utf-8")
                self.write_open()
                self.assertIsNone(self.patch(str(evidence)))
                evidence.write_text(evidence.read_text().replace("status:open", "status:completed")
                                    + "\nResumed work verified.\n", encoding="utf-8")
                self.index.write_text(self.index.read_text().replace(
                    "Active action: A001", "Active action: None",
                ), encoding="utf-8")
                accepted("WORKFLOW_WRITE_CLOSED", "write-close", "--record", str(self.record))
                if mode != "plan":
                    accepted("WORKFLOW_ACTION_CLOSED", "action-close", "--result", "completed")
                accepted("WORKFLOW_TURN_CHECKPOINTED", "checkpoint", "--record", str(self.record))
                self.assertIsNone(self.run_hook("Stop"))

    def test_snapshot_only_change_requests_snapshot_sync(self) -> None:
        self.activate("discuss")
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Current state: Active", "Current state: Waiting"),
            encoding="utf-8",
        )
        prompt = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("sync_status=snapshot", json.dumps(prompt))
        synced = self.control("sync", "--record", str(self.record), "--scope", "snapshot")
        self.assertIn("WORKFLOW_RECORD_SYNCED", json.dumps(synced))

    def test_non_snapshot_file_change_requires_record_sync(self) -> None:
        self.activate("discuss")
        context = self.record / "context.md"
        context.write_text(context.read_text(encoding="utf-8") + "Changed\n", encoding="utf-8")
        prompt = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("sync_status=record", json.dumps(prompt))

    def test_record_write_requires_transaction(self) -> None:
        self.activate("discuss")
        denied = self.patch(str(self.record / "context.md"))
        self.assertIn("WORKFLOW_WRITE_OPEN_REQUIRED", json.dumps(denied))

    def test_multi_file_write_transaction_acknowledges_bundle(self) -> None:
        self.activate("discuss")
        self.assertIn("WORKFLOW_WRITE_OPEN", json.dumps(self.write_open()))
        self.assertIsNone(self.patch(str(self.index), str(self.record / "context.md")))
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Current state: Active", "Current state: Updated"),
            encoding="utf-8",
        )
        context = self.record / "context.md"
        context.write_text(context.read_text(encoding="utf-8") + "Updated\n", encoding="utf-8")
        self.assertIn(
            "WORKFLOW_WRITE_CLOSED",
            json.dumps(self.control("write-close", "--record", str(self.record))),
        )
        self.assertIn(
            "WORKFLOW_TURN_CHECKPOINTED",
            json.dumps(self.control("checkpoint", "--record", str(self.record))),
        )

    def test_write_transaction_allows_declared_phase_addition(self) -> None:
        self.activate("plan")
        phase = self.record / "phases" / "P01-implement.md"
        self.assertIn("WORKFLOW_WRITE_OPEN", json.dumps(self.write_open(phase)))
        self.assertIsNone(self.patch(str(self.index), str(phase)))
        phase.parent.mkdir(parents=True)
        phase.write_text(
            "# P01: Implement\n\nStatus: Pending\nDepends on: None\nWave: 1\n"
            "Subagent: Not eligible — test\nOwned scope: hook\nProduces: implementation\n",
            encoding="utf-8",
        )
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace(
                "evidence.md\n<!-- workflow-manifest:end -->",
                "evidence.md\nphases/P01-implement.md\n<!-- workflow-manifest:end -->",
            ), encoding="utf-8",
        )
        plan = self.record / "plan.md"
        plan.write_text(plan.read_text(encoding="utf-8") + "phases/P01-implement.md\n", encoding="utf-8")
        self.assertIn(
            "WORKFLOW_WRITE_CLOSED",
            json.dumps(self.control("write-close", "--record", str(self.record))),
        )

    def test_activation_rejects_phase_identity_and_dependency_cycles(self) -> None:
        manifest = (
            "index.md", "context.md", "decisions.md", "plan.md", "verification.md",
            "evidence.md", "phases/P01-first.md", "phases/P02-second.md",
        )
        self.create_bundle("plan", manifest=manifest)
        (self.record / "plan.md").write_text(
            "# Plan\nphases/P01-first.md\nphases/P02-second.md\n", encoding="utf-8",
        )
        (self.record / "phases/P01-first.md").write_text(
            "# P99: Wrong\nStatus: Pending\nDepends on: None\nWave: 1\n"
            "Subagent: Eligible\nOwned scope: first\nProduces: first\n", encoding="utf-8",
        )
        (self.record / "phases/P02-second.md").write_text(
            "# P02: Second\nStatus: Pending\nDepends on: P01\nWave: 2\n"
            "Subagent: Eligible\nOwned scope: second\nProduces: second\n", encoding="utf-8",
        )
        denied = self.control("activate", "plan", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_UNREADABLE", json.dumps(denied))
        (self.record / "phases/P01-first.md").write_text(
            "# P01: First\nStatus: Pending\nDepends on: P02\nWave: 2\n"
            "Subagent: Eligible\nOwned scope: first\nProduces: first\n", encoding="utf-8",
        )
        denied = self.control("activate", "plan", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_UNREADABLE", json.dumps(denied))

    def test_write_transaction_blocks_outside_mutation_and_stop(self) -> None:
        self.activate("discuss"); self.write_open()
        self.assertIn("WORKFLOW_WRITE_SCOPE_DENIED", json.dumps(self.patch("app.py")))
        self.assertIn("WORKFLOW_WRITE_CLOSE_REQUIRED", json.dumps(self.run_hook("Stop")))

    def test_invalid_partial_bundle_can_be_repaired(self) -> None:
        self.activate("discuss"); self.write_open()
        context = self.record / "context.md"
        self.assertIsNone(self.patch(str(context))); context.unlink()
        self.assertIn(
            "WORKFLOW_WRITE_CLOSE_INVALID",
            json.dumps(self.control("write-close", "--record", str(self.record))),
        )
        self.assertIsNone(self.patch(str(context)))
        context.write_text("# Context repaired\n", encoding="utf-8")
        self.assertIn(
            "WORKFLOW_WRITE_CLOSED",
            json.dumps(self.control("write-close", "--record", str(self.record))),
        )

    def test_discuss_mutation_requires_scoped_action(self) -> None:
        self.activate("discuss")
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(self.patch("notes.md")))
        opened = self.control(
            "action-open", "--record", str(self.record), "--impact", "non-source",
            "--path", str(self.cwd / "notes.md"),
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))
        self.assertIsNone(self.patch(str(self.cwd / "notes.md")))
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(self.patch(str(self.cwd / "other.md"))))

    def test_discuss_cannot_open_source_or_shell_actions(self) -> None:
        self.activate("discuss")
        for args in (
            ("--impact", "source-confirmed", "--path", "app.py"),
            ("--impact", "source-confirmed", "--path", "notes.md"),
            ("--impact", "non-source", "--path", "app.tsx"),
            ("--impact", "non-source", "--path", "generated/client.ts"),
            ("--impact", "non-source", "--unscoped", "shell"),
            ("--impact", "non-source", "--unscoped", "git"),
        ):
            with self.subTest(args=args):
                denied = self.control("action-open", "--record", str(self.record), *args)
                self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(denied))
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(self.patch("notes.md")))

    def test_discuss_external_action_does_not_unlock_source_or_wrappers(self) -> None:
        self.activate("discuss")
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(self.control(
            "action-open", "--record", str(self.record), "--impact", "non-source",
            "--unscoped", "external",
        )))
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="tickets.update_issue",
                                      tool_input={"issue_id": "TEST-1", "body": "Authorized note"}))
        for payload in (
            {"tool_name": "exec_command", "tool_input": {"cmd": "python3 change.py"}},
            {"tool_name": "exec_command", "tool_input": {"cmd": "git -C /repo commit -m change"}},
            {"tool_name": "Write", "tool_input": {"file_path": "app.py", "content": "change"}},
            {"tool_name": "functions.exec", "tool_input": {"code": "anything"}},
            {"tool_name": "write_stdin", "tool_input": {"chars": "change\n"}},
            {"tool_name": "apply_patch", "tool_input": "*** Update File: notes.md\n*** Move to: app.py\n"},
        ):
            with self.subTest(payload=payload):
                self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(
                    self.run_hook("PreToolUse", **payload)))
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="exec_command",
                                      tool_input={"cmd": "git diff"}))

    def test_legacy_discuss_source_action_can_close_but_cannot_mutate(self) -> None:
        self.activate("discuss")
        database = self.cwd / "workflow-modes.sqlite3"
        with closing(sqlite3.connect(database)) as connection, connection:
            key = hashlib.sha256(self.session_id.encode("utf-8")).hexdigest()
            row = connection.execute("SELECT state_json FROM sessions WHERE session_key = ?", (key,)).fetchone()
            state = json.loads(row[0])
            state["action"] = {"status": "authorized", "impact": "source-confirmed",
                               "paths": [str(self.cwd / "app.py")], "unscoped": ["shell", "git"]}
            connection.execute("UPDATE sessions SET state_json = ? WHERE session_key = ?", (json.dumps(state), key))
        self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(self.patch("app.py")))
        self.assertIn("WORKFLOW_WRITE_OPEN", json.dumps(self.write_open()))
        self.assertIsNone(self.patch(str(self.record / "actions.md")))
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_ACTION_CLOSED", json.dumps(self.control("action-close", "--result", "paused")))

    def test_discuss_source_detection_resolves_non_source_alias(self) -> None:
        self.activate("discuss")
        target = self.cwd / "app.py"
        target.write_text("# source\n", encoding="utf-8")
        alias = self.cwd / "notes.md"
        alias.symlink_to(target)
        self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(self.control(
            "action-open", "--record", str(self.record), "--impact", "non-source", "--path", str(alias))))
        self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(self.patch(str(alias))))

    def test_behavior_answer_does_not_unlock_source_or_execute_transition(self) -> None:
        self.activate("discuss")
        self.write_open()
        (self.record / "decisions.md").write_text(
            "# Decisions\nQ1: Metric scope\n1. Visible page\n2. Filtered results\nAccepted: 1\n",
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_DISCUSS_EXECUTE_REQUIRED", json.dumps(self.patch("app.py")))
        self.assertIn("WORKFLOW_HANDOFF_NOT_DURABLE", json.dumps(
            self.control("transition", "execute", "--record", str(self.record))))

    def test_execute_action_reconciles_evidence_file(self) -> None:
        self.activate("execute")
        evidence = self.record / "evidence.md"
        self.write_open(); self.assertIsNone(self.patch(str(evidence)))
        evidence.write_text("# Evidence\nA001\n<!-- workflow-action:A001 status:open -->\n", encoding="utf-8")
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Active action: None", "Active action: A001"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        opened = self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A001",
            "--impact", "source-confirmed", "--path", str(self.cwd / "app.py"),
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))
        self.assertIsNone(self.patch(str(self.cwd / "app.py")))
        self.write_open(); self.assertIsNone(self.patch(str(evidence)))
        evidence.write_text(
            evidence.read_text(encoding="utf-8").replace(
                "<!-- workflow-action:A001 status:open -->",
                "<!-- workflow-action:A001 status:completed -->",
            ), encoding="utf-8",
        )
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Active action: A001", "Active action: None"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        closed = self.control("action-close", "--result", "completed")
        self.assertIn("tracker evidence reconciled", json.dumps(closed))

    def test_discuss_transitions_to_separate_plan_bundle(self) -> None:
        self.activate("discuss"); self.write_open()
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Mode status: Active", "Mode status: Exited"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        transitioned = self.control("transition", "plan", "--record", str(self.record))
        self.assertIn("WORKFLOW_MODE_ACTIVE", json.dumps(transitioned))
        target = self.cwd / "plans" / "test-plan"
        denied = self.patch(str(target / "index.md"))
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(denied))
        initialized = self.control(
            "plan-init", "--record", str(self.record), "--target", str(target),
        )
        self.assertIn("WORKFLOW_PLAN_INIT_OPEN", json.dumps(initialized))
        self.assertIsNone(self.patch(str(target / "index.md"), str(target / "context.md")))
        self.assertIn(
            "WORKFLOW_PLAN_BOOTSTRAP_SCOPE_DENIED",
            json.dumps(self.patch(str(self.cwd / "outside.md"))),
        )
        self.assertIn(
            "WORKFLOW_PLAN_BOOTSTRAP_SCOPE_DENIED",
            json.dumps(self.patch(str(target / "assets" / "config.json"))),
        )
        self.assertIn(
            "WORKFLOW_PLAN_ACTIVATION_REQUIRED",
            json.dumps(self.run_hook("Stop")),
        )
        self.assertIn(
            "WORKFLOW_RECORD_UNREADABLE",
            json.dumps(self.control("activate", "plan", "--record", str(target))),
        )
        self.record = target; self.index = self.record / "index.md"
        self.create_bundle("plan")
        rebound = self.control("activate", "plan", "--record", str(self.record))
        self.assertIn(str(self.record), json.dumps(rebound))

    def test_plan_init_rejects_existing_or_nested_target(self) -> None:
        self.activate("discuss"); self.write_open()
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Mode status: Active", "Mode status: Exited"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        self.control("transition", "plan", "--record", str(self.record))
        existing = self.cwd / "plans" / "existing"
        existing.mkdir(parents=True)
        denied = self.control(
            "plan-init", "--record", str(self.record), "--target", str(existing),
        )
        self.assertIn("WORKFLOW_PLAN_TARGET_INVALID", json.dumps(denied))
        nested = self.record / "nested-plan"
        denied = self.control(
            "plan-init", "--record", str(self.record), "--target", str(nested),
        )
        self.assertIn("WORKFLOW_PLAN_TARGET_INVALID", json.dumps(denied))

    def test_action_path_named_control_script_is_not_ambiguous(self) -> None:
        self.activate("execute")
        evidence = self.record / "evidence.md"
        self.write_open(); self.assertIsNone(self.patch(str(evidence)))
        evidence.write_text("# Evidence\nA003\n<!-- workflow-action:A003 status:open -->\n", encoding="utf-8")
        self.index.write_text(
            self.index.read_text(encoding="utf-8").replace("Active action: None", "Active action: A003"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        target = self.cwd / "scripts" / "workflow_modes_control.py"
        opened = self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A003",
            "--impact", "source-confirmed", "--path", str(target),
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))

    def test_approved_plan_transition_to_execute_keeps_plan_bundle(self) -> None:
        self.activate("plan"); self.write_open()
        self.index.write_text(
            self.index.read_text(encoding="utf-8")
            .replace("Status: Draft", "Status: Approved plan, not yet implemented")
            .replace("Plan mode: Active", "Plan mode: Exited\nExecution readiness: Ready\nExecution authorization: Granted")
            .replace("Execute mode: Inactive", "Execute mode: Ready"),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        transitioned = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(transitioned))
        self.assertIn(str(self.record), json.dumps(transitioned))

    def test_direct_execute_transition_keeps_discussion_bundle(self) -> None:
        self.activate("discuss")
        plan = self.record / "plan.md"; verification = self.record / "verification.md"
        self.write_open(plan, verification)
        plan.write_text("# Plan\n", encoding="utf-8")
        verification.write_text("# Verification\n", encoding="utf-8")
        self.index.write_text(
            self.index.read_text(encoding="utf-8")
            .replace("Mode status: Active", "Mode status: Exited")
            .replace("Execute mode: Inactive", "Execution readiness: Ready\nExecution authorization: Granted\nExecute mode: Ready")
            .replace(", ".join(MODE_REFERENCES["discuss"]), "None")
            .replace(
                "evidence.md\n<!-- workflow-manifest:end -->",
                "evidence.md\nplan.md\nverification.md\n<!-- workflow-manifest:end -->",
            ),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        transitioned = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(transitioned))
        self.assertIn(str(self.record), json.dumps(transitioned))
        self.assertIn("WORKFLOW_RECORD_SYNCED", json.dumps(self.control("sync", "--record", str(self.record))))
        self.assertIn("WORKFLOW_RULES_SYNCED", json.dumps(self.control("rules-sync", "--record", str(self.record))))
        self.write_open()
        self.index.write_text(self.index.read_text().replace("Active action: None", "Active action: A001"), encoding="utf-8")
        (self.record / "evidence.md").write_text(
            "# Evidence\nUser requested implementation of the agreed scope.\n"
            "<!-- workflow-action:A001 status:open -->\n", encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A001",
            "--impact", "source-confirmed", "--path", str(self.cwd / "app.py"))))
        self.assertIsNone(self.patch("app.py"))

    def test_approval_alone_keeps_plan_active_and_revisable(self) -> None:
        self.activate("plan")
        self.write_open()
        self.index.write_text(self.index.read_text().replace("Status: Draft", "Status: Approved plan, not yet implemented") + "Execution readiness: Ready\n", encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_HANDOFF_NOT_DURABLE", json.dumps(self.control("transition", "execute", "--record", str(self.record))))
        self.assertIn("mode=plan", json.dumps(self.control("snapshot")))
        self.assertIn("WORKFLOW_WRITE_OPEN", json.dumps(self.write_open()))
        self.assertIsNone(self.patch(str(self.record / "plan.md")))

    def test_all_modes_can_exit_without_execute_handoff(self) -> None:
        for mode, field in (("discuss", "Mode status"), ("plan", "Plan mode"), ("execute", "Execute mode")):
            with self.subTest(mode=mode):
                self.session_id = "exit-" + mode
                self.record = self.cwd / mode
                self.index = self.record / "index.md"
                self.activate(mode)
                self.assertIn("WORKFLOW_EXIT_NOT_DURABLE", json.dumps(self.control("deactivate")))
                self.write_open()
                self.index.write_text(self.index.read_text().replace(field + ": Active", field + ": Exited"), encoding="utf-8")
                self.control("write-close", "--record", str(self.record))
                self.assertIn("WORKFLOW_MODE_INACTIVE", json.dumps(self.control("deactivate")))
                self.assertIsNone(self.patch("new-task.py"))

    def test_noop_write_can_close_without_fake_timestamp(self) -> None:
        self.activate("discuss")
        self.write_open()
        self.assertIn("WORKFLOW_WRITE_CLOSED", json.dumps(self.control("write-close", "--record", str(self.record))))
        self.assertIsNone(self.run_hook("Stop"))

    def test_activation_cannot_erase_open_write_or_action(self) -> None:
        self.activate("discuss")
        self.write_open()
        self.assertIn("WORKFLOW_RECONCILIATION_REQUIRED", json.dumps(self.control("activate", "discuss", "--record", str(self.record))))
        self.control("write-close", "--record", str(self.record))
        self.control("action-open", "--record", str(self.record), "--impact", "non-source", "--path", str(self.cwd / "notes.md"))
        self.assertIn("WORKFLOW_RECONCILIATION_REQUIRED", json.dumps(self.control("activate", "discuss", "--record", str(self.record))))
        self.assertIn("WORKFLOW_RECONCILIATION_REQUIRED", json.dumps(self.control("transition", "plan", "--record", str(self.record))))

    def test_action_cannot_open_inside_write(self) -> None:
        self.activate("discuss")
        self.write_open()
        denied = self.control("action-open", "--record", str(self.record), "--impact", "source-confirmed", "--path", "app.py")
        self.assertIn("WORKFLOW_WRITE_CLOSE_REQUIRED", json.dumps(denied))

    def test_repeat_stop_suspends_without_unlocking_mutation(self) -> None:
        self.activate("discuss")
        self.write_open()
        self.assertIn("WORKFLOW_WRITE_CLOSE_REQUIRED", json.dumps(self.run_hook("Stop")))
        self.assertIn("WORKFLOW_SUSPENDED", json.dumps(self.run_hook("Stop", stop_hook_active=True)))
        self.assertIn("deny", json.dumps(self.patch("outside.py")))
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.control("activate", "discuss", "--record", str(self.record))))
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECOVERED", json.dumps(self.control("recover", "--record", str(self.record))))
        self.assertIsNone(self.run_hook("Stop"))

    def test_unreadable_record_repairs_from_cached_manifest(self) -> None:
        self.activate("discuss")
        baseline = self.revision()
        context = self.record / "context.md"
        context.unlink()
        self.assertIn("WORKFLOW_SUSPENDED", json.dumps(self.control("suspend", "--record", str(self.record), "--reason", "persistence-failed")))
        self.assertIn("WORKFLOW_SUSPENDED", json.dumps(self.run_hook("Stop")))
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.patch("app.py")))
        self.assertIn("WORKFLOW_WRITE_OPEN", json.dumps(self.control("write-open", "--record", str(self.record), "--previous-revision", baseline)))
        self.assertIsNone(self.patch(str(context)))
        context.write_text("# Context repaired from evidence\n", encoding="utf-8")
        self.assertIn("WORKFLOW_WRITE_CLOSED", json.dumps(self.control("write-close", "--record", str(self.record))))
        self.assertIn("WORKFLOW_RECOVERED", json.dumps(self.control("recover", "--record", str(self.record))))

    def test_suspension_does_not_allow_nonrecord_writes_or_new_actions(self) -> None:
        self.activate("discuss")
        self.control("action-open", "--record", str(self.record), "--impact", "non-source", "--path", str(self.cwd / "notes.md"))
        self.control("suspend", "--record", str(self.record), "--reason", "user-stop")
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.patch(str(self.cwd / "app.py"))))
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.control("recover", "--record", str(self.record))))
        self.assertIn("WORKFLOW_ACTION_CLOSED", json.dumps(self.control("action-close", "--result", "paused")))
        self.assertIn("WORKFLOW_RECOVERED", json.dumps(self.control("recover", "--record", str(self.record))))

    def test_execute_pause_preserves_pending_work_and_terminal_evidence(self) -> None:
        self.activate("execute")
        evidence = self.record / "evidence.md"
        plan = self.record / "plan.md"
        self.write_open()
        evidence.write_text("# Evidence\n<!-- workflow-action:A001 status:open -->\n", encoding="utf-8")
        plan.write_text("# Plan\n- [ ] Unfinished work\n", encoding="utf-8")
        self.index.write_text(self.index.read_text().replace("Active action: None", "Active action: A001"), encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.control("action-open", "--record", str(self.record), "--evidence-id", "A001", "--impact", "source-confirmed", "--path", "app.py")
        self.assertIn("WORKFLOW_EVIDENCE_NOT_RECONCILED", json.dumps(self.control("action-close", "--result", "paused")))
        self.write_open()
        evidence.write_text(evidence.read_text().replace("status:open", "status:paused"), encoding="utf-8")
        self.index.write_text(self.index.read_text().replace("Active action: A001", "Active action: None").replace("Status: In progress", "Status: Paused").replace("Execute mode: Active", "Execute mode: Paused"), encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_ACTION_CLOSED", json.dumps(self.control("action-close", "--result", "paused")))
        self.assertIn("WORKFLOW_MODE_INACTIVE", json.dumps(self.control("deactivate")))
        self.assertIn("[ ] Unfinished work", plan.read_text())

    def test_scripts_and_new_file_adapters_respect_plan_boundary(self) -> None:
        self.activate("plan")
        for payload in (
            {"tool_name": "exec_command", "tool_input": {"cmd": "python3 change.py"}},
            {"tool_name": "exec_command", "tool_input": {"cmd": "git -C /repo commit -m change"}},
            {"tool_name": "Write", "tool_input": {"file_path": "app.py", "content": "change"}},
            {"tool_name": "functions.exec", "tool_input": {"code": "anything"}},
        ):
            with self.subTest(payload=payload):
                self.assertIn("WORKFLOW_PLAN_READ_ONLY", json.dumps(self.run_hook("PreToolUse", **payload)))

    def test_compound_control_never_exempts_other_commands(self) -> None:
        self.activate("plan")
        control = f'{sys.executable} "{CONTROL}" snapshot --marker {MARKER}'
        for command in (control + "; touch outside.py", "touch outside.py; " + control, control + "\ntouch outside.py", "echo " + control):
            with self.subTest(command=command):
                denied = self.run_hook("PreToolUse", tool_name="exec_command", tool_input={"cmd": command})
                self.assertIn("WORKFLOW_CONTROL_AMBIGUOUS", json.dumps(denied))

    def test_transition_cannot_switch_to_another_record(self) -> None:
        self.activate("discuss")
        other = self.cwd / "other"
        other.mkdir()
        for path in self.record.iterdir():
            (other / path.name).write_text(path.read_text().replace("Mode status: Active", "Mode status: Exited"), encoding="utf-8")
        denied = self.control("transition", "plan", "--record", str(other))
        self.assertIn("WORKFLOW_RECORD_MISMATCH", json.dumps(denied))

    def test_file_scope_resolves_symlink_target(self) -> None:
        self.activate("discuss")
        target = self.cwd / "inside.md"
        outside = self.cwd / "outside.md"
        target.write_text("", encoding="utf-8")
        outside.write_text("", encoding="utf-8")
        self.control("action-open", "--record", str(self.record), "--impact", "non-source", "--path", str(target))
        alias = self.cwd / "alias.md"
        alias.symlink_to(outside)
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(self.patch(str(alias))))

    def test_bootstrap_can_be_cancelled_without_deleting_target(self) -> None:
        self.activate("discuss")
        self.write_open()
        self.index.write_text(self.index.read_text().replace("Mode status: Active", "Mode status: Exited"), encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.control("transition", "plan", "--record", str(self.record))
        target = self.cwd / "plans" / "partial"
        self.control("plan-init", "--record", str(self.record), "--target", str(target))
        target.mkdir(parents=True)
        (target / "index.md").write_text("partial", encoding="utf-8")
        self.assertIn("WORKFLOW_PLAN_INIT_CANCELLED", json.dumps(self.control("plan-cancel", "--record", str(self.record))))
        self.control("sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_MODE_INACTIVE", json.dumps(self.control("deactivate")))
        self.assertEqual((target / "index.md").read_text(), "partial")

    def test_handoff_acknowledges_execute_rules_before_active_metadata(self) -> None:
        self.activate("plan")
        self.write_open()
        self.index.write_text(self.index.read_text().replace("Status: Draft", "Status: Approved plan, not yet implemented")
                              .replace("Plan mode: Active", "Plan mode: Exited\nExecution readiness: Ready\nExecution authorization: Granted")
                              .replace("Execute mode: Inactive", "Execute mode: Ready")
                              .replace(", ".join(MODE_REFERENCES["plan"]), "None"), encoding="utf-8")
        self.assertIn("WORKFLOW_WRITE_CLOSED", json.dumps(self.control("write-close", "--record", str(self.record))))
        self.assertIn("mode=execute", json.dumps(self.control("transition", "execute", "--record", str(self.record))))
        self.assertIn("WORKFLOW_RECORD_SYNCED", json.dumps(self.control("sync", "--record", str(self.record))))
        self.assertIn("WORKFLOW_RULES_SYNCED", json.dumps(self.control("rules-sync", "--record", str(self.record))))
        self.write_open()
        self.index.write_text(self.index.read_text().replace("Execute mode: Ready", "Execute mode: Active"), encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_TURN_CHECKPOINTED", json.dumps(self.control("checkpoint", "--record", str(self.record))))
        self.assertIsNone(self.run_hook("Stop"))

    def test_reactivation_preserves_prompt_checkpoint_requirement(self) -> None:
        self.activate("discuss")
        self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("existing state retained", json.dumps(self.control("activate", "discuss", "--record", str(self.record))))
        self.assertIn("WORKFLOW_TURN_CHECKPOINT_REQUIRED", json.dumps(self.run_hook("Stop")))

    def test_scope_requires_all_compound_mutation_classes(self) -> None:
        self.activate("execute")
        self.write_open()
        (self.record / "evidence.md").write_text(
            "# Evidence\n<!-- workflow-action:A001 status:open -->\n", encoding="utf-8")
        self.index.write_text(self.index.read_text().replace("Active action: None", "Active action: A001"), encoding="utf-8")
        self.control("write-close", "--record", str(self.record))
        self.control("action-open", "--record", str(self.record), "--evidence-id", "A001",
                     "--impact", "source-confirmed", "--unscoped", "git")
        git = {"cmd": "git -C /repo commit -m change"}
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="exec_command", tool_input=git))
        mixed = {"cmd": "git -C /repo commit -m change; python3 unrelated.py"}
        self.assertIn("WORKFLOW_ACTION_UNSCOPED_TOOL", json.dumps(self.run_hook("PreToolUse", tool_name="exec_command", tool_input=mixed)))

    def test_unready_discussion_cannot_activate_execute(self) -> None:
        self.create_bundle("discuss")
        self.index.write_text(self.index.read_text().replace("Execute mode: Inactive", "Execute mode: Active"), encoding="utf-8")
        self.assertIn("WORKFLOW_RECORD_NOT_ACTIVE", json.dumps(self.control("activate", "execute", "--record", str(self.record))))

    def test_phase_error_explains_which_field_needs_repair(self) -> None:
        self.activate("plan")
        phase = self.record / "phases" / "P01-first.md"
        self.write_open(phase)
        phase.parent.mkdir()
        phase.write_text("# P01: First\nStatus: Pending\nDepends on: None\nWave: 2\nSubagent: Eligible\nOwned scope: app.py\nProduces: result\n", encoding="utf-8")
        self.index.write_text(self.index.read_text().replace("evidence.md\n<!-- workflow-manifest:end -->", "evidence.md\nphases/P01-first.md\n<!-- workflow-manifest:end -->"), encoding="utf-8")
        (self.record / "plan.md").write_text("phases/P01-first.md\n", encoding="utf-8")
        denied = self.control("write-close", "--record", str(self.record))
        self.assertIn("WORKFLOW_WRITE_CLOSE_INVALID", json.dumps(denied))
        # Details must include new files declared in the open transaction too.
        self.assertIn("Wave must be 1", json.dumps(denied))

    def test_matching_source_control_works_with_versioned_hook_cache(self) -> None:
        self.activate("discuss")
        source = self.cwd / "marketplace" / "scripts" / "workflow_modes_control.py"
        source.parent.mkdir(parents=True)
        source.write_bytes(CONTROL.read_bytes())
        command = f'{sys.executable} "{source}" snapshot --marker {MARKER}'
        self.assertIn("WORKFLOW_MODE_SNAPSHOT", json.dumps(self.run_hook("PreToolUse", tool_name="exec_command", tool_input={"cmd": command})))
        source.write_text("print('unrelated program')\n", encoding="utf-8")
        self.assertIn("WORKFLOW_CONTROL_AMBIGUOUS", json.dumps(self.run_hook("PreToolUse", tool_name="exec_command", tool_input={"cmd": command})))

    def test_cached_recovery_scope_cannot_follow_replaced_symlink(self) -> None:
        self.activate("discuss")
        baseline = self.revision()
        context = self.record / "context.md"
        outside = self.cwd / "outside.md"
        outside.write_text("Unrelated data", encoding="utf-8")
        context.unlink()
        context.symlink_to(outside)
        self.control("suspend", "--record", str(self.record), "--reason", "persistence-failed")
        denied = self.control("write-open", "--record", str(self.record), "--previous-revision", baseline)
        self.assertIn("WORKFLOW_WRITE_PATH_INVALID", json.dumps(denied))
        self.assertEqual(outside.read_text(), "Unrelated data")

    def test_user_can_interrupt_owned_process_while_suspended(self) -> None:
        self.activate("discuss")
        self.control("suspend", "--record", str(self.record), "--reason", "user-stop")
        self.assertIsNone(self.run_hook("PreToolUse", tool_name="write_stdin", tool_input={"session_id": 42, "chars": "\x03"}))
        self.assertIn("WORKFLOW_RECOVERY_REQUIRED", json.dumps(self.run_hook("PreToolUse", tool_name="write_stdin", tool_input={"session_id": 42, "chars": "python3 change.py\n"})))

    def test_control_script_and_hook_schema(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CONTROL), "write-open", "--record", str(self.record),
             "--previous-revision", "sha256:test", "--path", str(self.index), "--marker", MARKER],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            [sys.executable, str(CONTROL), "plan-init", "--record", str(self.record),
             "--target", str(self.cwd / "plans" / "target"), "--marker", MARKER],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
        self.assertNotIn("additionalContextLimit", hooks["PostCompact"][0]["hooks"][0])


if __name__ == "__main__":
    unittest.main()
