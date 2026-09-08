from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_workflow_modes_hook as fixtures

sys.path.insert(0, str(fixtures.PLUGIN_ROOT / 'scripts'))
record_api = importlib.import_module('workflow_modes_record')
hook_api = importlib.import_module('workflow_modes_hook')
control_api = importlib.import_module('workflow_modes_control')
diagnostics = importlib.import_module('workflow_modes_diagnostics')


class RecoveryTests(unittest.TestCase):
    # Reuse fixture construction, not the base class's test methods.
    for name in ('setUp', 'run_hook', 'control', 'patch', 'index_content', 'create_bundle',
                 'activate', 'revision', 'write_open'):
        locals()[name] = getattr(fixtures.WorkflowModesHookTests, name)

    def snapshot(self):
        text = self.control('snapshot')['hookSpecificOutput']['additionalContext']
        return json.loads(text.split('\n', 1)[1])

    def diagnosis(self):
        result = subprocess.run([sys.executable, str(fixtures.CONTROL), 'diagnose', '--record',
                                 str(self.record), '--json'], env=self.env, text=True,
                                capture_output=True, check=False)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertFalse(result.stderr)
        return json.loads(result.stdout)

    def recover(self, previous=None, observed=None):
        return self.control('write-open', '--record', str(self.record), '--recover',
                            '--previous-revision', previous or self.snapshot()['acknowledged_revision'],
                            '--observed-revision', observed or self.diagnosis()['observed_revision'])

    def replace_state(self, transform):
        with sqlite3.connect(self.cwd / 'workflow-modes.sqlite3') as connection:
            state = json.loads(connection.execute('SELECT state_json FROM sessions').fetchone()[0])
            transform(state)
            connection.execute('UPDATE sessions SET state_json=?', (json.dumps(state),))

    def test_noop_close_preserves_action_and_checkpoint(self):
        self.activate('discuss')
        self.control('action-open', '--record', str(self.record), '--impact', 'non-source')
        self.run_hook('UserPromptSubmit')
        before = self.snapshot()
        self.write_open()
        result = self.control('write-close', '--record', str(self.record))
        self.assertIn('changed=false', json.dumps(result))
        after = self.snapshot()
        self.assertEqual(before['action'], after['action'])
        self.assertTrue(after['checkpoint_required'])
        self.assertIsNone(after['write_transaction'])

    def test_new_session_snapshot_and_execute_resume_preserve_progress(self):
        self.activate('execute')
        self.write_open()
        evidence = self.record / 'evidence.md'
        evidence.write_text('# Evidence\nPhase P001 completed and verified; P002 pending.\n')
        self.assertIn('WORKFLOW_WRITE_CLOSED', json.dumps(
            self.control('write-close', '--record', str(self.record))))
        previous_session = self.session_id
        previous_state = self.snapshot()
        before = {p: p.read_bytes() for p in self.record.rglob('*.md')}
        self.session_id = 'resume-session'
        inactive = self.snapshot()
        self.assertEqual(inactive, {'active': False, 'mode': None, 'record': None})
        self.assertIsNone(self.control('activate', '--help'))
        self.assertEqual(self.snapshot(), inactive)
        with sqlite3.connect(self.cwd / 'workflow-modes.sqlite3') as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 1)
        self.assertIn('WORKFLOW_MODE_ACTIVE', json.dumps(
            self.control('activate', 'execute', '--record', str(self.record))))
        self.assertIn('WORKFLOW_RECORD_SYNCED', json.dumps(
            self.control('sync', '--record', str(self.record))))
        references = tuple(item for ref in fixtures.MODE_REFERENCES['execute']
                           for item in ('--reference', ref))
        self.assertIn('WORKFLOW_RULES_SYNCED', json.dumps(
            self.control('rules-sync', '--record', str(self.record), *references)))
        self.assertEqual(self.snapshot()['record'], str(self.record))
        self.assertEqual(before, {p: p.read_bytes() for p in self.record.rglob('*.md')})
        self.session_id = previous_session
        self.assertEqual(self.snapshot(), previous_state)

    def test_inactive_controls_explain_bootstrap_without_activating(self):
        self.create_bundle('execute')
        for args in (('sync', '--record', str(self.record)),
                     ('transition', 'execute', '--record', str(self.record)),
                     ('write-open', '--record', str(self.record), '--previous-revision', self.revision())):
            denial = self.control(*args)['hookSpecificOutput']['permissionDecisionReason']
            self.assertIn('WORKFLOW_MODE_INACTIVE', denial)
            self.assertIn('Fresh-Session Bootstrap', denial)
            self.assertIn('activate execute', denial)
            self.assertIn('--help only displays usage', denial)
            self.assertFalse(self.snapshot()['active'])

    def test_exact_rollback_closes_without_fake_edit(self):
        self.activate('plan')
        original = self.index.read_bytes()
        self.write_open()
        self.index.write_bytes(original + b'temporary\n')
        self.index.write_bytes(original)
        self.assertIn('changed=false', json.dumps(self.control('write-close', '--record', str(self.record))))
        self.assertIsNone(self.run_hook('Stop'))

    def test_diagnose_does_not_create_database_or_modify_bundle(self):
        self.create_bundle('plan')
        before = {p: p.read_bytes() for p in self.record.rglob('*.md')}
        self.assertTrue(self.diagnosis()['valid'])
        self.assertFalse((self.cwd / 'workflow-modes.sqlite3').exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.record.rglob('*.md')})

    def test_missing_file_diagnostic_and_executable_recovery_guidance(self):
        self.activate('plan')
        context = self.record / 'context.md'
        original = context.read_text()
        context.unlink()
        report = self.diagnosis()
        self.assertEqual(report['issues'][0]['path'], 'context.md')
        denial = self.control('sync', '--record', str(self.record))['hookSpecificOutput']['permissionDecisionReason']
        self.assertIn('context.md', denial)
        command = next(line for line in denial.splitlines() if ' --recover ' in line)
        response = self.run_hook('PreToolUse', tool_name='exec_command', tool_input={'cmd': command})
        self.assertIn('WORKFLOW_RECOVERY_OPEN', json.dumps(response))
        cli = subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", command] if os.name == "nt" else shlex.split(command), capture_output=True, text=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertIsNone(self.patch(str(context)))
        context.write_text(original)
        self.assertIn('WORKFLOW_WRITE_CLOSED', json.dumps(self.control('write-close', '--record', str(self.record))))
        self.assertTrue(self.diagnosis()['valid'])

    def test_semantic_recovery_preserves_open_action(self):
        self.activate('execute')
        self.write_open()
        evidence = self.record / 'evidence.md'
        evidence.write_text('# Evidence\nA001\n<!-- workflow-action:A001 status:open -->\n')
        self.index.write_text(self.index.read_text().replace('Active action: None', 'Active action: A001'))
        self.control('write-close', '--record', str(self.record))
        self.control('action-open', '--record', str(self.record), '--impact', 'source-confirmed', '--evidence-id', 'A001')
        before = self.snapshot()['action']
        self.index.write_text(self.index.read_text().replace('Active action: A001', 'Active action: WRONG'))
        self.assertIn('WORKFLOW_RECOVERY_OPEN', json.dumps(self.recover()))
        self.assertIsNone(self.patch(str(self.index)))
        self.index.write_text(self.index.read_text().replace('Active action: WRONG', 'Active action: A001'))
        self.control('write-close', '--record', str(self.record))
        self.assertEqual(self.snapshot()['action'], before)
        self.assertIn('WORKFLOW_EXECUTE_RECONCILIATION_REQUIRED', json.dumps(self.run_hook('Stop')))

    def test_recovery_rejects_stale_observation(self):
        self.activate('plan')
        (self.record / 'context.md').unlink()
        observed = self.diagnosis()['observed_revision']
        self.index.write_text(self.index.read_text() + 'changed again\n')
        self.assertIn('Observed bundle changed', json.dumps(self.recover(observed=observed)))
        self.assertIsNone(self.snapshot()['write_transaction'])

    def test_recovery_rejects_stale_acknowledged_baseline(self):
        self.activate('plan')
        (self.record / 'context.md').unlink()
        self.assertIn('Acknowledged baseline changed', json.dumps(self.recover(previous='sha256:stale')))
        self.assertIsNone(self.snapshot()['write_transaction'])

    def test_recovery_rejects_missing_or_changed_identity(self):
        self.activate('plan')
        self.index.write_text(self.index.read_text().replace('TEST-TRACKER', 'OTHER-TRACKER'))
        (self.record / 'context.md').unlink()
        self.assertIn('identity is missing or changed', json.dumps(self.recover()))
        self.assertIsNone(self.snapshot()['write_transaction'])

    def test_legacy_state_requires_valid_sync_before_recovery(self):
        self.activate('plan')
        self.replace_state(lambda s: s.pop('baseline_metadata'))
        original = (self.record / 'context.md').read_bytes()
        (self.record / 'context.md').unlink()
        self.assertIn('No trusted baseline', json.dumps(self.recover()))
        (self.record / 'context.md').write_bytes(original)
        self.control('sync', '--record', str(self.record))
        self.assertTrue(self.snapshot()['baseline_metadata']['files'])
        (self.record / 'context.md').unlink()
        self.assertIn('WORKFLOW_RECOVERY_OPEN', json.dumps(self.recover()))

    def test_recovery_does_not_adopt_or_delete_extra_markdown(self):
        self.activate('plan')
        extra = self.record / 'someone-elses.md'
        extra.write_text('owned elsewhere')
        self.assertIn('Unacknowledged Markdown exists', json.dumps(self.recover()))
        self.assertEqual(extra.read_text(), 'owned elsewhere')
        self.assertIsNone(self.snapshot()['write_transaction'])

    def test_recovery_forbids_scope_expansion_deletion_and_rename(self):
        self.activate('plan')
        (self.record / 'context.md').unlink()
        self.recover()
        self.assertIn('WORKFLOW_WRITE_SCOPE_DENIED', json.dumps(self.patch(str(self.cwd / 'app.py'))))
        self.assertIn('WORKFLOW_WRITE_SCOPE_DENIED', json.dumps(self.patch(str(self.record / 'extra.md'))))
        for command in (f'*** Delete File: {self.index}', f'*** Update File: {self.index}\n*** Move to: {self.record / "context.md"}'):
            response = self.run_hook('PreToolUse', tool_name='apply_patch', tool_input={'command': command})
            self.assertIn('WORKFLOW_RECOVERY_SCOPE_DENIED', json.dumps(response))
        for action in ('sync', 'activate'):
            args = ('plan',) if action == 'activate' else ()
            self.assertIn('WORKFLOW_WRITE_CLOSE_REQUIRED', json.dumps(self.control(action, *args, '--record', str(self.record))))
        self.assertIn('WORKFLOW_WRITE_CLOSE_REQUIRED', json.dumps(self.run_hook('Stop')))

    def test_recovery_close_cannot_change_manifest(self):
        self.activate('plan')
        (self.record / 'context.md').unlink()
        self.recover()
        (self.record / 'context.md').write_text('restored')
        (self.record / 'extra.md').write_text('unauthorized external change')
        self.index.write_text(self.index.read_text().replace('evidence.md\n<!-- workflow-manifest:end -->', 'evidence.md\nextra.md\n<!-- workflow-manifest:end -->'))
        self.assertIn('WORKFLOW_RECOVERY_SCOPE_DENIED', json.dumps(self.control('write-close', '--record', str(self.record))))
        self.assertTrue(self.snapshot()['write_transaction'])

    def test_recovery_rechecks_paths_after_open(self):
        self.activate('plan')
        context = self.record / 'context.md'
        context.unlink()
        self.recover()
        outside = self.cwd / 'outside.md'
        outside.write_text('untouched')
        try:
            context.symlink_to(outside)
        except OSError:
            self.skipTest('Symlinks unavailable on this host')
        self.assertIn('WORKFLOW_RECOVERY_SCOPE_DENIED', json.dumps(self.patch(str(context))))
        self.assertEqual(outside.read_text(), 'untouched')

    def test_invalid_reference_repair_and_rules_sync(self):
        self.activate('plan')
        original = self.index.read_text()
        self.write_open()
        self.index.write_text(original.replace('references/phase-planning.md', 'references/typo.md'))
        denial = self.control('write-close', '--record', str(self.record))
        self.assertIn('Required references', json.dumps(denial))
        self.assertIn('WORKFLOW_WRITE_CLOSE_INVALID', json.dumps(denial))
        denied = self.control('rules-sync', '--record', str(self.record), '--reference', 'references/plan-record.md', '--reference', 'references/phase-planning.md')
        self.assertIn('WORKFLOW_RULES_RECORD_INVALID', json.dumps(denied))
        self.index.write_text(original)
        self.control('write-close', '--record', str(self.record))
        self.assertIn('WORKFLOW_RULES_SYNCED', json.dumps(self.control('rules-sync', '--record', str(self.record), '--reference', 'references/plan-record.md', '--reference', 'references/phase-planning.md')))

    def test_invalid_reference_outside_transaction_uses_recovery(self):
        self.activate('plan')
        self.index.write_text(self.index.read_text().replace('references/phase-planning.md', 'references/typo.md'))
        self.assertIn('WORKFLOW_RECOVERY_OPEN', json.dumps(self.recover()))

    def test_recovery_check_is_inside_database_transaction(self):
        self.activate('plan')
        (self.record / 'context.md').unlink()
        with patch.dict(os.environ, self.env):
            store = hook_api.StateStore()
            key = hook_api.session_key(self.session_id)
            current = store.get(key)
            control = dict(previous_revision=current['acknowledged_revision'], observed_revision=self.diagnosis()['observed_revision'])
            original = hook_api.recovery_observation
            def checked(state, request):
                self.assertTrue(store.connection.in_transaction)
                return original(state, request)
            with patch.object(hook_api, 'recovery_observation', side_effect=checked):
                self.assertIn('WORKFLOW_RECOVERY_OPEN', json.dumps(hook_api.open_recovery(store, key, current, control)))
            store.connection.close()

    def test_close_rejects_concurrent_session_change(self):
        self.activate('plan')
        self.write_open()
        with patch.dict(os.environ, self.env):
            store = hook_api.StateStore()
            key = hook_api.session_key(self.session_id)
            original = hook_api.remember_baseline
            def changed(state, revision):
                original(state, revision)
                self.replace_state(lambda latest: latest.update(checkpoint_required=True))
            with patch.object(hook_api, 'remember_baseline', side_effect=changed):
                result = hook_api.handle_control(store, key, {'cwd': str(self.cwd)}, {'action': 'write-close', 'record': str(self.record)})
            self.assertIn('WORKFLOW_STATE_CHANGED', json.dumps(result))
            self.assertTrue(store.get(key)['write_transaction'])
            self.assertTrue(store.get(key)['checkpoint_required'])
            store.connection.close()

    def test_parser_errors_and_help_do_not_change_state(self):
        self.activate('plan')
        before = self.snapshot()
        for args in (('activate', 'plan', '--bogus'), ('write-open', '--record', str(self.record)), ('activate', 'execute'), ('snapshot', '--mark', fixtures.MARKER)):
            result = self.control(*args)
            self.assertIn('WORKFLOW_CONTROL_ARGUMENT_INVALID', json.dumps(result))
            self.assertEqual(before, self.snapshot())
            cli = subprocess.run([sys.executable, str(fixtures.CONTROL), *args, '--marker', fixtures.MARKER], text=True, capture_output=True)
            self.assertEqual(cli.returncode, 2)
        self.assertIsNone(self.control('activate', '--help'))
        self.assertEqual(before, self.snapshot())

    def test_marker_can_precede_other_arguments_and_scope_path_can_name_control(self):
        self.activate('plan')
        command = diagnostics.control_command('sync', '--marker', fixtures.MARKER, '--record', str(self.record))
        self.assertIn('WORKFLOW_RECORD_SYNCED', json.dumps(self.run_hook('PreToolUse', tool_name='exec_command', tool_input={'cmd': command})))

    def test_mixed_commands_denied_before_state_change(self):
        self.activate('plan')
        before = self.snapshot()
        command = diagnostics.control_command('activate', 'plan')
        for suffix in ('; echo done', ' && echo done', ' | cat', ' > output.txt', '\necho done'):
            result = self.run_hook('PreToolUse', tool_name='exec_command', tool_input={'cmd': command + suffix})
            self.assertIn('WORKFLOW_CONTROL_AMBIGUOUS', json.dumps(result))
            self.assertEqual(before, self.snapshot())

    def test_diagnostic_commands_round_trip_with_spaces(self):
        self.record = self.cwd / 'bundle with spaces'
        self.index = self.record / 'index.md'
        self.create_bundle('plan')
        command = diagnostics.control_command('activate', 'plan', '--record', str(self.record))
        response = self.run_hook('PreToolUse', tool_name='exec_command', tool_input={'cmd': command})
        self.assertIn('WORKFLOW_MODE_ACTIVE', json.dumps(response))
        result = subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", command] if os.name == "nt" else shlex.split(command), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_literal_shell_characters_round_trip(self):
        self.record = self.cwd / "record with $dollar; (notes) and 'quote'"
        self.index = self.record / 'index.md'
        self.create_bundle('plan')
        command = diagnostics.control_command('activate', 'plan', '--record', str(self.record))
        response = self.run_hook('PreToolUse', tool_name='exec_command', tool_input={'cmd': command})
        self.assertIn('WORKFLOW_MODE_ACTIVE', json.dumps(response))
        self.assertEqual(control_api.shell_arguments(command, windows=os.name == 'nt')[-3:], [str(self.record), '--marker', fixtures.MARKER])

    def test_recovery_does_not_clear_action_through_abort(self):
        self.activate('execute')
        (self.record / 'context.md').unlink()
        self.recover()
        self.assertIn('WORKFLOW_WRITE_CLOSE_REQUIRED', json.dumps(self.control('action-abort', '--reason', 'record-unreadable')))

    def test_message_budget_does_not_cut_executable_commands(self):
        self.activate('plan')
        state = self.snapshot()
        state['record'] = '/long/' + 'x' * 4000
        reason = diagnostics.enrich_reason('WORKFLOW_RECORD_MISMATCH: wrong record', {'hook_event_name': 'PreToolUse'}, state)
        self.assertLessEqual(len(reason), 3000)
        self.assertNotIn('--record /long/', reason)


class BundleValidationTests(unittest.TestCase):
    def assert_issue(self, files, code):
        with self.assertRaises(record_api.BundleError) as caught:
            record_api.validate_contents(files, 'plan')
        self.assertEqual(caught.exception.code, code)
        self.assertTrue(caught.exception.path)
        self.assertTrue(caught.exception.next_step)

    def files(self):
        return {'index.md': '<!-- workflow-record version:4 kind:plan tracker-id:TEST -->\nActive action: None\n',
                'context.md': '', 'decisions.md': '', 'plan.md': '', 'verification.md': '', 'evidence.md': ''}

    def phase(self, id, dependency):
        return f'# {id}: Phase\nStatus: Pending\nDepends on: {dependency}\nWave: 1\nSubagent: No\nOwned scope: test\nProduces: test\n'

    def test_phase_failure_details(self):
        files = self.files()
        files['phases/P01-first.md'] = self.phase('P99', 'None')
        self.assert_issue(files, 'WORKFLOW_PHASE_ID_INVALID')
        files['phases/P01-first.md'] = self.phase('P01', 'None')
        self.assert_issue(files, 'WORKFLOW_PHASE_LINK_MISSING')
        files['plan.md'] = 'phases/P01-first.md\n'
        files['phases/P01-first.md'] = self.phase('P01', 'P02')
        self.assert_issue(files, 'WORKFLOW_PHASE_DEPENDENCY_UNKNOWN')
        files['phases/P02-second.md'] = self.phase('P02', 'P01')
        files['plan.md'] += 'phases/P02-second.md\n'
        self.assert_issue(files, 'WORKFLOW_PHASE_DEPENDENCY_CYCLE')

    def test_action_marker_mismatch_is_specific(self):
        files = self.files()
        files['evidence.md'] = '<!-- workflow-action:A001 status:open -->'
        self.assert_issue(files, 'WORKFLOW_ACTION_SUMMARY_MISMATCH')

    def test_duplicate_references_are_invalid(self):
        files = self.files()
        files['index.md'] += '<!-- workflow-active-snapshot:start version:2 -->\nRequired references: references/plan-record.md, references/plan-record.md\n<!-- workflow-active-snapshot:end -->'
        self.assert_issue(files, 'WORKFLOW_RULES_RECORD_INVALID')

    def test_windows_literal_argv_parser(self):
        command = "& 'C:\\Program Files\\Python\\python.exe' 'C:\\plugin\\workflow_modes_control.py' 'sync' '--record' 'C:\\it''s $literal; safe' '--marker' 'workflow-modes-v1'"
        argv = control_api.shell_arguments(command, windows=True)
        self.assertEqual(argv[0], r'C:\Program Files\Python\python.exe')
        self.assertEqual(argv[4], r"C:\it's $literal; safe")
        with self.assertRaises(control_api.ControlError):
            control_api.shell_arguments(command + '; Remove-Item example', windows=True)

    def test_reversed_markers_do_not_crash(self):
        self.assertIsNone(record_api.record_snapshot('<!-- workflow-active-snapshot:end --><!-- workflow-active-snapshot:start version:2 -->'))
        with self.assertRaises(record_api.BundleError):
            record_api.parse_manifest('<!-- workflow-manifest:end --><!-- workflow-manifest:start -->')


if __name__ == '__main__':
    unittest.main()
