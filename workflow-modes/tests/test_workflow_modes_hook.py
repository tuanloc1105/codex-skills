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
        self.record = self.cwd / "discussion" / "tracker.md"

    def run_hook(self, event: str, **fields: object) -> dict[str, object] | None:
        payload = {
            "session_id": self.session_id,
            "cwd": str(self.cwd),
            "hook_event_name": event,
            **fields,
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def control(self, *args: str) -> dict[str, object] | None:
        command = " ".join(
            [sys.executable, f'"{CONTROL}"', *args, "--marker", MARKER]
        )
        return self.run_hook(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": command},
        )

    def patch(self, *paths: str) -> dict[str, object] | None:
        command = "\n".join(f"*** Update File: {path}" for path in paths)
        return self.run_hook(
            "PreToolUse",
            tool_name="apply_patch",
            tool_input={"command": command},
        )

    def mutate_shell(self, command: str) -> dict[str, object] | None:
        return self.run_hook(
            "PreToolUse",
            tool_name="exec_command",
            tool_input={"cmd": command},
        )

    def activate(self, mode: str) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        profile = "Durable" if mode == "execute" else "Lightweight"
        if mode == "discuss":
            content = (
                "<!-- workflow-record version:3 kind:discuss tracker-id:TEST-TRACKER -->\n"
                "Mode: $discuss\nMode status: Active\nExecute mode: Inactive\n"
            )
        elif mode == "execute":
            content = (
                "<!-- workflow-record version:3 kind:plan tracker-id:TEST-TRACKER -->\n"
                "Status: In progress\nExecute mode: Active\n"
            )
        else:
            content = (
                "<!-- workflow-record version:3 kind:plan tracker-id:TEST-TRACKER -->\n"
                "Status: Draft\nExecute mode: Inactive\n"
            )
        content += (
            "<!-- workflow-active-snapshot:start version:2 -->\n"
            f"Profile: {profile}\nRequired references: {', '.join(MODE_REFERENCES[mode])}\n"
            "Goal: Test workflow\nCurrent state: Active\n"
            "Accepted decisions: None\nOpen items: None\nNext safe action: Continue\n"
            "<!-- workflow-active-snapshot:end -->\n"
        )
        self.record.write_text(content, encoding="utf-8")
        output = self.control("activate", mode, "--record", str(self.record))
        self.assertIn("WORKFLOW_MODE_ACTIVE", json.dumps(output))
        synced = self.control("sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_SYNCED", json.dumps(synced))
        rules = self.control(
            "rules-sync", "--record", str(self.record),
            *(item for reference in MODE_REFERENCES[mode] for item in ("--reference", reference)),
        )
        self.assertIn("WORKFLOW_RULES_SYNCED", json.dumps(rules))

    def test_dormant_until_skill_activates_mode(self) -> None:
        self.assertIsNone(self.patch("app.py"))
        self.assertIsNone(self.run_hook("PostCompact"))

    def test_read_only_git_merge_base_is_not_classified_as_merge(self) -> None:
        self.activate("discuss")
        self.assertIsNone(self.mutate_shell("git merge-base origin/dev origin/main"))

    def test_post_compact_restores_active_mode_and_record(self) -> None:
        self.activate("discuss")
        output = self.run_hook("PostCompact")
        self.assertIn("systemMessage", output)
        self.assertIn(str(self.record), json.dumps(output))
        self.assertIn("only plan or execute", json.dumps(output))
        self.assertIn("sync_status=record", json.dumps(output))
        rejected = self.control(
            "sync", "--record", str(self.record), "--scope", "snapshot"
        )
        self.assertIn("currently required record scope", json.dumps(rejected))
        self.assertIn("Recovery order", json.dumps(output))
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch("app.py")))
        self.assertIn(
            "WORKFLOW_RULES_SYNC_REQUIRED",
            json.dumps(self.run_hook("Stop", stop_hook_active=False)),
        )

    def test_activation_requires_exact_rules_sync_before_mutation(self) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        self.record.write_text(
            "<!-- workflow-record version:3 kind:discuss tracker-id:T -->\n"
            "Mode: $discuss\nMode status: Active\n"
            "<!-- workflow-active-snapshot:start version:2 -->\n"
            "Profile: Lightweight\nRequired references: references/tracker.md\n"
            "<!-- workflow-active-snapshot:end -->\n",
            encoding="utf-8",
        )
        self.control("activate", "discuss", "--record", str(self.record))
        self.control("sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch("app.py")))
        missing = self.control("rules-sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_RULES_SYNC_INVALID", json.dumps(missing))
        extra = self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/tracker.md",
            "--reference", "references/actions.md",
        )
        self.assertIn("WORKFLOW_RULES_SYNC_INVALID", json.dumps(extra))
        accepted = self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/tracker.md",
        )
        self.assertIn("WORKFLOW_RULES_SYNCED", json.dumps(accepted))

    def test_invalid_mode_reference_is_never_accepted(self) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        self.record.write_text(
            "<!-- workflow-record version:3 kind:plan tracker-id:T -->\n"
            "Status: Draft\n<!-- workflow-active-snapshot:start version:2 -->\n"
            "Profile: Lightweight\nRequired references: references/tracker.md\n"
            "<!-- workflow-active-snapshot:end -->\n",
            encoding="utf-8",
        )
        self.control("activate", "plan", "--record", str(self.record))
        self.control("sync", "--record", str(self.record))
        denied = self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/plan-record.md",
            "--reference", "references/phase-planning.md",
        )
        self.assertIn("WORKFLOW_RULES_SYNC_INVALID", json.dumps(denied))

    def test_reference_set_change_reopens_rules_gate(self) -> None:
        self.activate("discuss")
        text = self.record.read_text(encoding="utf-8")
        self.record.write_text(
            text.replace(
                "Required references: references/tracker.md, references/actions.md",
                "Required references: references/tracker.md",
            ),
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record), "--scope", "snapshot")
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch("app.py")))

    def test_ack_write_reference_change_reopens_rules_gate(self) -> None:
        self.activate("discuss")
        previous = "sha256:" + hashlib.sha256(self.record.read_bytes()).hexdigest()
        self.assertIsNone(self.patch(str(self.record)))
        self.record.write_text(
            self.record.read_text(encoding="utf-8").replace(
                "Required references: references/tracker.md, references/actions.md",
                "Required references: references/tracker.md",
            ),
            encoding="utf-8",
        )
        acknowledged = self.control(
            "ack-write", "--record", str(self.record),
            "--previous-revision", previous,
        )
        self.assertIn("WORKFLOW_WRITE_ACKNOWLEDGED", json.dumps(acknowledged))
        self.assertIn("WORKFLOW_RULES_SYNC_REQUIRED", json.dumps(self.patch("app.py")))

    def test_ordinary_prompt_does_not_reopen_rules_gate(self) -> None:
        self.activate("discuss")
        output = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("rules_sync_required=false", json.dumps(output))

    def test_user_prompt_keeps_unchanged_record_synced_and_requires_checkpoint(self) -> None:
        self.activate("discuss")
        output = self.run_hook("UserPromptSubmit", prompt="Continue")
        rendered = json.dumps(output)
        self.assertIn("workflow-anchor", rendered)
        self.assertIn("sync_status=current", rendered)
        blocked = self.patch(str(self.cwd / "app.py"))
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(blocked))
        stop = self.run_hook("Stop", stop_hook_active=False)
        self.assertIn("WORKFLOW_TURN_CHECKPOINT_REQUIRED", json.dumps(stop))
        unchanged = self.control("checkpoint", "--record", str(self.record))
        self.assertIn("WORKFLOW_CHECKPOINT_CHANGE_REQUIRED", json.dumps(unchanged))
        checked = self.control(
            "checkpoint", "--record", str(self.record), "--no-change"
        )
        self.assertIn("WORKFLOW_TURN_CHECKPOINTED", json.dumps(checked))
        self.assertIsNone(self.run_hook("Stop", stop_hook_active=False))

    def test_legacy_record_uses_audited_prompt_sync(self) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        self.record.write_text(
            "<!-- workflow-record version:2 kind:discuss tracker-id:TEST-TRACKER -->\n"
            "Mode: $discuss\nMode status: Active\nExecute mode: Inactive\n",
            encoding="utf-8",
        )
        self.control("activate", "discuss", "--record", str(self.record))
        self.control("sync", "--record", str(self.record))
        output = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("profile=audited", json.dumps(output))
        self.assertIn("sync_status=record", json.dumps(output))

    def test_snapshot_v1_uses_full_mode_reference_fallback(self) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        self.record.write_text(
            "<!-- workflow-record version:3 kind:discuss tracker-id:T -->\n"
            "Mode: $discuss\nMode status: Active\n"
            "<!-- workflow-active-snapshot:start version:1 -->\n"
            "Profile: Lightweight\n<!-- workflow-active-snapshot:end -->\n",
            encoding="utf-8",
        )
        self.control("activate", "discuss", "--record", str(self.record))
        self.control("sync", "--record", str(self.record))
        accepted = self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/tracker.md",
            "--reference", "references/actions.md",
        )
        self.assertIn("WORKFLOW_RULES_SYNCED", json.dumps(accepted))

    def test_snapshot_only_change_requests_snapshot_sync(self) -> None:
        self.activate("discuss")
        text = self.record.read_text(encoding="utf-8")
        self.record.write_text(
            text.replace("Current state: Active", "Current state: Awaiting decision"),
            encoding="utf-8",
        )
        output = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("sync_status=snapshot", json.dumps(output))
        synced = self.control(
            "sync", "--record", str(self.record), "--scope", "snapshot"
        )
        self.assertIn("scope=snapshot", json.dumps(synced))

    def test_ack_write_accepts_owned_delta_without_reread(self) -> None:
        self.activate("plan")
        previous = "sha256:" + hashlib.sha256(self.record.read_bytes()).hexdigest()
        self.assertIsNone(self.patch(str(self.record)))
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "Decision: accepted\n",
            encoding="utf-8",
        )
        acknowledged = self.control(
            "ack-write", "--record", str(self.record),
            "--previous-revision", previous,
        )
        self.assertIn("WORKFLOW_WRITE_ACKNOWLEDGED", json.dumps(acknowledged))
        output = self.run_hook("UserPromptSubmit", prompt="Continue")
        self.assertIn("sync_status=current", json.dumps(output))

    def test_ack_write_rejects_stale_previous_revision(self) -> None:
        self.activate("plan")
        self.assertIsNone(self.patch(str(self.record)))
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "Decision: accepted\n",
            encoding="utf-8",
        )
        rejected = self.control(
            "ack-write", "--record", str(self.record),
            "--previous-revision", "sha256:stale",
        )
        self.assertIn("WORKFLOW_ACK_WRITE_STALE", json.dumps(rejected))

    def test_ack_write_rejects_unobserved_external_change(self) -> None:
        self.activate("plan")
        previous = "sha256:" + hashlib.sha256(self.record.read_bytes()).hexdigest()
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "External change\n",
            encoding="utf-8",
        )
        rejected = self.control(
            "ack-write", "--record", str(self.record),
            "--previous-revision", previous,
        )
        self.assertIn("WORKFLOW_ACK_WRITE_STALE", json.dumps(rejected))

    def test_record_change_invalidates_previous_sync(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "External change\n",
            encoding="utf-8",
        )
        blocked = self.patch(str(self.cwd / "app.py"))
        self.assertIn("WORKFLOW_RECORD_SYNC_REQUIRED", json.dumps(blocked))
        synced = self.control("sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_SYNCED", json.dumps(synced))
        blocked_for_action = self.patch(str(self.cwd / "app.py"))
        self.assertIn("WORKFLOW_EXECUTE_ACTION_REQUIRED", json.dumps(blocked_for_action))

    def test_sync_rejects_record_identity_replacement(self) -> None:
        self.activate("execute")
        replacement = self.record.read_text(encoding="utf-8").replace(
            "tracker-id:TEST-TRACKER", "tracker-id:OTHER-TRACKER"
        )
        self.record.write_text(replacement, encoding="utf-8")
        blocked = self.control("sync", "--record", str(self.record))
        self.assertIn("WORKFLOW_RECORD_IDENTITY_MISMATCH", json.dumps(blocked))

    def test_checkpoint_accepts_a_changed_and_synced_record(self) -> None:
        self.activate("plan")
        self.run_hook("UserPromptSubmit", prompt="Revise the plan")
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "Decision: accepted\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        checked = self.control("checkpoint", "--record", str(self.record))
        self.assertIn("changed=true", json.dumps(checked))

    def test_checkpoint_rejects_an_unacknowledged_tracker_write(self) -> None:
        self.activate("plan")
        self.run_hook("UserPromptSubmit", prompt="Revise the plan")
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "Decision: accepted\n",
            encoding="utf-8",
        )
        blocked = self.control("checkpoint", "--record", str(self.record))
        self.assertIn("revision was not acknowledged", json.dumps(blocked))

    def test_hook_schema_uses_system_message_for_post_compact(self) -> None:
        hooks = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
        self.assertNotIn("additionalContextLimit", hooks["PostCompact"][0]["hooks"][0])
        for event in ("UserPromptSubmit", "PreToolUse"):
            self.assertEqual(
                hooks[event][0]["hooks"][0]["additionalContextLimit"], 900
            )

    def test_discuss_blocks_mutation_without_action(self) -> None:
        self.activate("discuss")
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(blocked))

    def test_discuss_action_is_file_scoped_and_returns_to_discuss(self) -> None:
        self.activate("discuss")
        opened = self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        self.assertIn("WORKFLOW_ACTION_OPEN", json.dumps(opened))
        self.assertIsNone(self.patch("app.py"))
        denied = self.patch("other.py")
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(denied))
        closed = self.control("action-close", "--result", "completed")
        self.assertIn("full discuss guardrails restored", json.dumps(closed))
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_DISCUSS_ACTION_REQUIRED", json.dumps(blocked))

    def test_discuss_action_requires_source_confirmation(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "non-source",
        )
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_SOURCE_CONFIRMATION_REQUIRED", json.dumps(blocked))

    def test_discuss_action_allows_only_explicit_unscoped_mutation_class(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd), "--unscoped", "git",
            "--impact", "source-confirmed",
        )
        self.assertIsNone(self.mutate_shell("git merge --no-commit origin/main"))
        denied_shell = self.mutate_shell("rm generated.txt")
        self.assertIn("WORKFLOW_ACTION_UNSCOPED_TOOL", json.dumps(denied_shell))

    def test_discuss_non_source_action_rejects_unscoped_git_mutation(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd), "--unscoped", "git",
            "--impact", "non-source",
        )
        blocked = self.mutate_shell("git merge --no-commit origin/main")
        self.assertIn("WORKFLOW_SOURCE_CONFIRMATION_REQUIRED", json.dumps(blocked))

    def test_discuss_transitions_to_plan_then_execute(self) -> None:
        self.activate("discuss")
        self.record.write_text(
            "Mode: $discuss\nMode status: Exited\nExecute mode: Inactive\n",
            encoding="utf-8",
        )
        plan = self.control("transition", "plan", "--record", str(self.record))
        self.assertIn("mode=plan", json.dumps(plan))
        self.control("sync", "--record", str(self.record))
        self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/plan-record.md",
            "--reference", "references/phase-planning.md",
        )
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_PLAN_READ_ONLY", json.dumps(blocked))
        self.record.write_text(
            "Status: Approved plan, not yet implemented\nExecute mode: Ready\n",
            encoding="utf-8",
        )
        execute = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(execute))
        self.control("sync", "--record", str(self.record))
        self.control(
            "rules-sync", "--record", str(self.record),
            "--reference", "references/implementation.md",
            "--reference", "references/completion.md",
        )
        blocked = self.patch("app.py")
        self.assertIn("WORKFLOW_EXECUTE_ACTION_REQUIRED", json.dumps(blocked))

    def test_discuss_transitions_directly_to_execute(self) -> None:
        self.activate("discuss")
        self.record.write_text(
            "Mode: $discuss\nMode status: Exited\nExecution readiness: Ready\n"
            "Execute mode: Ready\n",
            encoding="utf-8",
        )
        output = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("mode=execute", json.dumps(output))
        compact = self.run_hook("PostCompact")
        self.assertIn("exit=explicit request only", json.dumps(compact))

    def test_discuss_and_plan_cannot_deactivate(self) -> None:
        self.activate("discuss")
        blocked = self.control("deactivate")
        self.assertIn("WORKFLOW_EXIT_DENIED", json.dumps(blocked))

    def test_transition_rejects_tracker_without_durable_markers(self) -> None:
        self.activate("discuss")
        blocked = self.control("transition", "execute", "--record", str(self.record))
        self.assertIn("WORKFLOW_HANDOFF_NOT_DURABLE", json.dumps(blocked))

    def test_execute_can_explicitly_deactivate(self) -> None:
        self.activate("execute")
        output = self.control("deactivate")
        self.assertIn("WORKFLOW_MODE_INACTIVE", json.dumps(output))
        self.assertIsNone(self.run_hook("PostCompact"))

    def test_execute_allows_tracker_update_without_action(self) -> None:
        self.activate("execute")
        self.assertIsNone(self.patch(str(self.record)))
        blocked = self.patch(str(self.cwd / "app.py"))
        self.assertIn("WORKFLOW_EXECUTE_ACTION_REQUIRED", json.dumps(blocked))

    def test_execute_action_requires_persisted_evidence_id(self) -> None:
        self.activate("execute")
        missing_id = self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        self.assertIn("WORKFLOW_EVIDENCE_ID_REQUIRED", json.dumps(missing_id))
        missing_record = self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A001",
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        self.assertIn("WORKFLOW_EVIDENCE_NOT_PERSISTED", json.dumps(missing_record))
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "A001 pending action\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        missing_marker = self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A001",
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        self.assertIn("WORKFLOW_ACTION_MARKER_REQUIRED", json.dumps(missing_marker))

    def test_execute_action_requires_terminal_record_update_before_close(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8")
            + "A001 pending action\n<!-- workflow-action:A001 status:open -->\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        opened = self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A001",
            "--path", str(self.cwd / "app.py"), "--unscoped", "git",
            "--impact", "source-confirmed",
        )
        self.assertIn("bounded execute action authorized", json.dumps(opened))
        self.assertIsNone(self.patch(str(self.cwd / "app.py")))
        denied_path = self.patch(str(self.cwd / "other.py"))
        self.assertIn("WORKFLOW_ACTION_SCOPE_DENIED", json.dumps(denied_path))
        denied_shell = self.mutate_shell("rm other.py")
        self.assertIn("WORKFLOW_ACTION_UNSCOPED_TOOL", json.dumps(denied_shell))
        self.assertIsNone(self.mutate_shell("git push origin feature/test"))
        stale_close = self.control("action-close", "--result", "completed")
        self.assertIn("WORKFLOW_EVIDENCE_NOT_RECONCILED", json.dumps(stale_close))
        self.record.write_text(
            self.record.read_text(encoding="utf-8") + "Unrelated tracker update\n",
            encoding="utf-8",
        )
        unrelated_close = self.control("action-close", "--result", "completed")
        self.assertIn("WORKFLOW_EVIDENCE_NOT_RECONCILED", json.dumps(unrelated_close))
        terminal_record = self.record.read_text(encoding="utf-8").replace(
            "<!-- workflow-action:A001 status:open -->",
            "<!-- workflow-action:A001 status:completed -->",
        )
        self.record.write_text(
            terminal_record + "A001 completed with commit abc123\n", encoding="utf-8"
        )
        closed = self.control("action-close", "--result", "completed")
        self.assertIn("tracker evidence reconciled", json.dumps(closed))
        self.control("sync", "--record", str(self.record))
        blocked_again = self.patch(str(self.cwd / "app.py"))
        self.assertIn("WORKFLOW_EXECUTE_ACTION_REQUIRED", json.dumps(blocked_again))

    def test_execute_action_blocks_stop_and_deactivation_until_reconciled(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8")
            + "A002 pending action\n<!-- workflow-action:A002 status:open -->\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A002",
            "--impact", "non-source",
        )
        stop = self.run_hook("Stop", stop_hook_active=True)
        self.assertEqual(stop.get("decision"), "block")
        self.assertIn("WORKFLOW_EXECUTE_RECONCILIATION_REQUIRED", json.dumps(stop))
        deactivate = self.control("deactivate")
        self.assertIn("WORKFLOW_ACTION_CLOSE_REQUIRED", json.dumps(deactivate))

    def test_execute_action_rejects_invalid_close_result(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8")
            + "A004 pending action\n<!-- workflow-action:A004 status:open -->\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A004",
            "--impact", "non-source",
        )
        invalid = self.control("action-close", "--result", "typo")
        self.assertIn("WORKFLOW_ACTION_RESULT_INVALID", json.dumps(invalid))
        stop = self.run_hook("Stop", stop_hook_active=False)
        self.assertEqual(stop.get("decision"), "block")

    def test_execute_action_can_abort_only_when_record_is_unreadable(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8")
            + "A005 pending action\n<!-- workflow-action:A005 status:open -->\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A005",
            "--impact", "non-source",
        )
        denied = self.control("action-abort", "--reason", "record-unreadable")
        self.assertIn("WORKFLOW_ACTION_ABORT_DENIED", json.dumps(denied))
        self.record.unlink()
        aborted = self.control("action-abort", "--reason", "record-unreadable")
        self.assertIn("WORKFLOW_ACTION_ABORTED", json.dumps(aborted))
        self.assertIsNone(self.run_hook("Stop", stop_hook_active=False))

    def test_execute_non_source_action_cannot_mutate_git_history(self) -> None:
        self.activate("execute")
        self.record.write_text(
            self.record.read_text(encoding="utf-8")
            + "A003 pending Jira update\n<!-- workflow-action:A003 status:open -->\n",
            encoding="utf-8",
        )
        self.control("sync", "--record", str(self.record))
        self.control(
            "action-open", "--record", str(self.record), "--evidence-id", "A003",
            "--unscoped", "external", "--impact", "non-source",
        )
        blocked = self.mutate_shell("git push origin feature/test")
        self.assertIn("WORKFLOW_SOURCE_CONFIRMATION_REQUIRED", json.dumps(blocked))
        self.assertIsNone(self.mutate_shell("glab mr create --title test"))

    def test_git_platform_cli_mutations_require_execute_action(self) -> None:
        self.activate("execute")
        for command in (
            "glab mr create --title test",
            "gh --repo owner/repo pr merge 12",
            "gh pr merge 12",
            "tea pulls create",
            "acli jira workitem transition --key ABC-1",
        ):
            with self.subTest(command=command):
                blocked = self.mutate_shell(command)
                self.assertIn("WORKFLOW_EXECUTE_ACTION_REQUIRED", json.dumps(blocked))

    def test_stop_blocks_once_when_discuss_action_is_open(self) -> None:
        self.activate("discuss")
        self.control(
            "action-open", "--record", str(self.record),
            "--path", str(self.cwd / "app.py"), "--impact", "source-confirmed",
        )
        first = self.run_hook("Stop", stop_hook_active=False)
        self.assertEqual(first.get("decision"), "block")
        second = self.run_hook("Stop", stop_hook_active=True)
        self.assertIn("stop allowed", json.dumps(second))

    def test_control_script_accepts_expected_cli_shape(self) -> None:
        result = subprocess.run(
            [
                sys.executable, str(CONTROL), "activate", "discuss",
                "--record", str(self.record), "--marker", MARKER,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_probe_does_not_corrupt_following_control_request(self) -> None:
        self.record.parent.mkdir(parents=True, exist_ok=True)
        self.record.write_text(
            "Status: In progress\nExecute mode: Active\n", encoding="utf-8"
        )
        command = (
            f'{sys.executable} "{CONTROL}" activate --help && '
            f'{sys.executable} "{CONTROL}" activate execute '
            f'--record "{self.record}" --marker {MARKER}'
        )
        output = self.run_hook(
            "PreToolUse", tool_name="exec_command", tool_input={"cmd": command}
        )
        self.assertIn("mode=execute", json.dumps(output))

    def test_multiple_marker_backed_controls_are_rejected(self) -> None:
        command = (
            f'{sys.executable} "{CONTROL}" activate plan --marker {MARKER}; '
            f'{sys.executable} "{CONTROL}" snapshot --marker {MARKER}'
        )
        output = self.run_hook(
            "PreToolUse", tool_name="exec_command", tool_input={"cmd": command}
        )
        self.assertIn("WORKFLOW_CONTROL_AMBIGUOUS", json.dumps(output))
        self.assertIsNone(self.run_hook("PostCompact"))


if __name__ == "__main__":
    unittest.main()
