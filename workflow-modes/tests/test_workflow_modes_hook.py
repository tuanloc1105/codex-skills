from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
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
            lifecycle = f"Status: {status or 'Draft'}\nExecute mode: Inactive\n"
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
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(self.patch("app.py")))
        opened = self.control(
            "action-open", "--record", str(self.record), "--impact", "source-confirmed",
            "--path", str(self.cwd / "app.py"),
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))
        self.assertIsNone(self.patch(str(self.cwd / "app.py")))
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(self.patch(str(self.cwd / "other.py"))))

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
        self.record = self.cwd / "plans" / "test-plan"; self.index = self.record / "index.md"
        self.create_bundle("plan")
        rebound = self.control("activate", "plan", "--record", str(self.record))
        self.assertIn(str(self.record), json.dumps(rebound))

    def test_direct_execute_transition_keeps_discussion_bundle(self) -> None:
        self.activate("discuss")
        plan = self.record / "plan.md"; verification = self.record / "verification.md"
        self.write_open(plan, verification)
        plan.write_text("# Plan\n", encoding="utf-8")
        verification.write_text("# Verification\n", encoding="utf-8")
        self.index.write_text(
            self.index.read_text(encoding="utf-8")
            .replace("Mode status: Active", "Mode status: Exited")
            .replace("Execute mode: Inactive", "Execution readiness: Ready\nExecute mode: Ready")
            .replace(
                "evidence.md\n<!-- workflow-manifest:end -->",
                "evidence.md\nplan.md\nverification.md\n<!-- workflow-manifest:end -->",
            ),
            encoding="utf-8",
        )
        self.control("write-close", "--record", str(self.record))
        transitioned = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(transitioned))

    def test_control_script_and_hook_schema(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CONTROL), "write-open", "--record", str(self.record),
             "--previous-revision", "sha256:test", "--path", str(self.index), "--marker", MARKER],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
        self.assertNotIn("additionalContextLimit", hooks["PostCompact"][0]["hooks"][0])


if __name__ == "__main__":
    unittest.main()
