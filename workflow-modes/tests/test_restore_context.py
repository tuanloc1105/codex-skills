from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import restore_context as restore
import workflow_modes_hook as hook

CONTROL = Path(hook.__file__).with_name('workflow_modes_control.py')


class ContextReadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.path = self.root / 'notes.md'
        self.path.write_text('a' * (restore.PAGE_CHARS + 10))
        self.state = {'epoch': 'E1', 'reads': {}}

    def response(self, offset=0):
        return {'exit_code': 0, 'output': json.dumps(restore.read_page(str(self.path), offset, 'E1'))}

    def test_consecutive_pages_required_and_only_hashes_offsets_stored(self):
        self.assertFalse(restore.accept_page(self.state, str(self.path), restore.PAGE_CHARS, self.response(restore.PAGE_CHARS)))
        self.assertTrue(restore.accept_page(self.state, str(self.path), 0, self.response()))
        self.assertEqual(restore.missing_reads(self.state, [str(self.path)])[0]['offset'], restore.PAGE_CHARS)
        self.assertTrue(restore.accept_page(self.state, str(self.path), restore.PAGE_CHARS, self.response(restore.PAGE_CHARS)))
        self.assertEqual(restore.missing_reads(self.state, [str(self.path)]), [])
        self.assertEqual(set(self.state['reads'][str(self.path)]), {'revision', 'offset'})
        self.assertNotIn('aaaa', json.dumps(self.state))

    def test_failed_truncated_running_incomplete_or_forged_output_never_counts(self):
        good = self.response()
        bad_page = json.loads(good['output'])
        bad_page['text'] = 'claimed content'
        for response in (
            {**good, 'exit_code': 1}, {**good, 'truncated': True}, {**good, 'session_id': 42},
            {**good, 'output': good['output'][:-1]}, {**good, 'output': json.dumps(bad_page)},
            {'output': good['output']}, {'content': [None]},
            {'exit_code': 0, 'output': json.dumps({**json.loads(good['output']), 'epoch': 'old'})},
        ):
            with self.subTest(response=response):
                self.assertFalse(restore.accept_page(self.state, str(self.path), 0, response))
                self.assertEqual(self.state['reads'], {})

    def test_changed_document_invalidates_prior_pages_and_stale_response(self):
        self.assertTrue(restore.accept_page(self.state, str(self.path), 0, self.response()))
        old = self.response(restore.PAGE_CHARS)
        self.path.write_text('b' + self.path.read_text()[1:])
        self.assertEqual(restore.missing_reads(self.state, [str(self.path)])[0]['offset'], 0)
        self.assertFalse(restore.accept_page(self.state, str(self.path), restore.PAGE_CHARS, old))
        self.assertFalse(restore.accept_page(self.state, str(self.path), restore.PAGE_CHARS, self.response(restore.PAGE_CHARS)))
        self.assertTrue(restore.accept_page(self.state, str(self.path), 0, self.response()))

    def test_empty_file_requires_delivery_and_mcp_wrapped_output_counts(self):
        self.path.write_text('')
        self.assertEqual(len(restore.missing_reads(self.state, [str(self.path)])), 1)
        response = {'content': [{'type': 'text', 'text': json.dumps(self.response())}]}
        self.assertTrue(restore.accept_page(self.state, str(self.path), 0, response))
        self.assertEqual(restore.missing_reads(self.state, [str(self.path)]), [])

    def test_native_orchestration_blocks_preserve_complete_shell_results(self):
        # Shape observed in the failing session; no private record contents retained.
        result = {**self.response(), 'chunk_id': 'test', 'wall_time_seconds': 0.002,
                  'original_token_count': 1000}
        blocks = [{'type': 'input_text', 'text': 'Script completed\nWall time 0.2 seconds\nOutput:\n'},
                  {'type': 'input_text', 'text': json.dumps(result)}]
        for response in (blocks, json.dumps(blocks), {'content': blocks}, blocks[1:]):
            with self.subTest(envelope=type(response).__name__):
                state = {'epoch': 'E1', 'reads': {}}
                self.assertTrue(restore.accept_page(state, str(self.path), 0, response))
                self.assertEqual(state['reads'][str(self.path)]['offset'], restore.PAGE_CHARS)

    def test_orchestration_headers_do_not_hide_failure_truncation_or_multiple_results(self):
        header = {'type': 'input_text', 'text': 'Script completed\nWall time 0.2 seconds\nOutput:\n'}
        result = {'type': 'input_text', 'text': json.dumps(self.response())}
        cases = (
            [{**header, 'text': 'Script running with cell ID 1'}, result],
            [{**header, 'text': 'Script failed\n'}, result],
            [{**header, 'text': header['text'] + 'Warning: truncated output'}, result],
            [header, {**result, 'truncated': True}],
            [header, {**result, 'text': result['text'][:-1]}],
            [header, {**result, 'text': json.dumps({**self.response(), 'exit_code': 1})}],
            [header, {**result, 'text': json.dumps({**self.response(), 'session_id': 42})}],
            [header, {**result, 'text': self.response()['output']}],
            [result, result], [header, result, result],
            {'content': [header, result], 'isError': True},
        )
        for response in cases:
            with self.subTest(response=response):
                self.assertFalse(restore.accept_page(self.state, str(self.path), 0, response))
                self.assertEqual(self.state['reads'], {})

    def test_literal_wrapper_only_and_record_repairs_have_bounded_paths(self):
        read = {'cmd': 'cat notes.md'}
        wrapped = {'tool_name': 'functions.exec', 'tool_input': 'text(await tools.exec_command(' + json.dumps(read) + '));'}
        self.assertEqual(restore.unwrap(wrapped)['tool_input'], read)
        for code in ('text(await tools.exec_command({cmd: "cat notes.md"}));',
                     wrapped['tool_input'] + ' await other();',
                     'text(await tools.exec_command(JSON.parse(secret)));'):
            payload = {**wrapped, 'tool_input': code}
            self.assertEqual(restore.unwrap(payload), payload)
        payload = {'tool_name': 'apply_patch', 'tool_input': f'*** Update File: {self.path}\n'}
        self.assertTrue(restore.safe_during_restore(payload, str(self.root)))
        self.assertFalse(restore.safe_during_restore({**payload, 'tool_input': payload['tool_input'] + '*** Move to: /outside.py\n'}, str(self.root)))
        outside = self.root.parent / 'outside.md'
        alias = self.root / 'alias.md'
        alias.symlink_to(outside)
        self.assertFalse(restore.safe_during_restore({**payload, 'tool_input': f'*** Update File: {alias}\n'}, str(self.root)))


class RestoreGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.record = self.root / 'record'
        self.record.mkdir()
        self.skill = self.root / 'mode'
        self.skill.mkdir()
        (self.skill / 'SKILL.md').write_text('Required instructions\n')
        entries = ['index.md', 'context.md', 'decisions.md', 'plan.md', 'verification.md', 'evidence.md']
        for entry in entries:
            (self.record / entry).write_text('# ' + entry + '\n')
        self.index = self.record / 'index.md'
        self.index.write_text('<!-- workflow-record version:4 kind:plan tracker-id:T1 -->\n'
                              'Execute mode: Active\nActive action: None\n'
                              '<!-- workflow-active-snapshot:start version:2 -->\nRequired references: None\n'
                              '<!-- workflow-active-snapshot:end -->\n'
                              '<!-- workflow-manifest:start -->\n' + '\n'.join(entries) + '\n<!-- workflow-manifest:end -->\n')
        self.env = patch.dict(os.environ, {'PLUGIN_DATA': str(self.root / 'data')})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.store = hook.StateStore()
        self.addCleanup(self.store.connection.close)
        self.key = 'test-key'
        self.store.mutate(self.key, lambda _old: {
            'mode': 'execute', 'record': str(self.record), 'tracker_id': 'T1', 'record_paths': entries,
            'restore': {'epoch': 'E1', 'reads': {}, 'skill_root': str(self.skill)},
        })

    def pre(self, name='apply_patch', value='*** Update File: app.py\n'):
        return hook.handle_pre_tool(self.store, self.key, {'tool_name': name, 'tool_input': value, 'cwd': str(self.root)})

    def control(self, *args):
        return self.pre('exec_command', {'cmd': shlex.join([sys.executable, str(CONTROL), *args, '--marker', hook.MARKER])})

    def deliver(self, path, *, wrapper=False, epoch=None):
        state = self.store.get(self.key)
        epoch = epoch or state['restore']['epoch']
        args = [sys.executable, str(CONTROL), 'restore-read', '--record', str(self.record),
                '--path', str(path), '--offset', '0', '--epoch', epoch, '--marker', hook.MARKER]
        payload = {'tool_name': 'exec_command', 'tool_input': {'cmd': shlex.join(args)}, 'cwd': str(self.root)}
        result = {'exit_code': 0, 'output': json.dumps(restore.read_page(str(path), 0, epoch))}
        if wrapper:
            payload = {**payload, 'tool_name': 'functions.exec', 'tool_input': 'text(await tools.exec_command(' + json.dumps(payload['tool_input']) + '));'}
            result = [{'type': 'input_text', 'text': 'Script completed\nWall time 0.2 seconds\nOutput:\n'},
                      {'type': 'input_text', 'text': json.dumps(result)}]
        return hook.handle_post_tool(self.store, self.key, {**payload, 'tool_response': result})

    def denied(self, output):
        self.assertEqual(output['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_only_reads_questions_interruption_and_record_repair_pass_before_restore(self):
        for name, value in (
            ('exec_command', {'cmd': 'cat app.py'}), ('read_file', {'path': 'app.py'}),
            ('request_user_input', {}), ('interrupt_agent', {}),
            ('write_stdin', {'chars': '\x03'}),
            ('apply_patch', f'*** Update File: {self.record / "context.md"}\n'),
        ):
            with self.subTest(name=name):
                output = self.pre(name, value)
                self.assertNotIn('permissionDecision', (output or {}).get('hookSpecificOutput', {}))
        for name, value in (
            ('exec_command', {'cmd': 'git push'}), ('tickets.update_issue', {}),
            ('spawn_agent', {}), ('followup_task', {}), ('send_message', {}),
            ('mystery_operation', {}), ('functions.exec', {'code': 'await work()'}),
        ):
            with self.subTest(name=name):
                self.denied(self.pre(name, value))
        self.assertNotIn('decision', hook.handle_stop(self.store, self.key, {}))

    def test_sync_rules_and_mode_controls_cannot_substitute_for_read_receipts(self):
        self.control('sync', '--record', str(self.record))
        self.control('rules-sync', '--record', str(self.record))
        self.denied(self.pre())
        before = deepcopy(self.store.get(self.key)['restore'])
        for args in (('activate', 'execute', '--record', str(self.record)), ('deactivate',),
                     ('transition', 'execute', '--record', str(self.record))):
            output = self.control(*args)
            self.assertIn('WORKFLOW_CONTROL_NOT_APPLIED', json.dumps(output))
            self.assertEqual(before, self.store.get(self.key)['restore'])
        for _ in range(3):
            self.assertNotIn('decision', hook.handle_stop(self.store, self.key, {}))
        self.assertEqual(before, self.store.get(self.key)['restore'])

    def test_all_current_documents_restore_advisory_mode_without_clearing_user_stop(self):
        state = self.store.get(self.key)
        state['recovery'] = {'reason': 'user-stop'}
        self.store.mutate(self.key, lambda _old: state)
        paths, valid = hook.restoration_scope(state)
        self.assertTrue(valid)
        for path in paths[:-1]:
            self.deliver(path, wrapper=True)
            self.denied(self.pre())
        output = self.deliver(paths[-1], wrapper=True)
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(output))
        self.assertNotIn('restore', self.store.get(self.key))
        self.assertEqual(self.store.get(self.key)['recovery'], {'reason': 'user-stop'})
        self.assertNotIn('permissionDecision', self.pre()['hookSpecificOutput'])

    def test_missing_skill_keeps_gate_pending_but_report_and_repair_remain_available(self):
        (self.skill / 'SKILL.md').unlink()
        for path in self.record.iterdir():
            self.deliver(path)
        self.denied(self.pre())
        self.assertIn('SKILL.md', json.dumps(self.control('restore-status')))
        self.assertNotIn('decision', hook.handle_stop(self.store, self.key, {}))
        output = self.pre('apply_patch', f'*** Update File: {self.index}\n')
        self.assertNotIn('permissionDecision', (output or {}).get('hookSpecificOutput', {}))

    def test_file_drift_manifest_changes_and_old_epochs_cannot_unlock(self):
        paths, _ = hook.restoration_scope(self.store.get(self.key))
        self.deliver(paths[0])
        context = self.record / 'context.md'
        self.deliver(context)
        context.write_text('new context\n')
        for path in paths[2:]:
            self.deliver(path)
        self.denied(self.pre())
        self.assertIn('context.md', json.dumps(self.control('restore-status')))
        state = self.store.get(self.key)
        state['restore']['epoch'] = 'E2'
        state['restore']['reads'] = {}
        self.store.mutate(self.key, lambda _old: state)
        self.assertIn('WORKFLOW_RESTORE_READ_NOT_OBSERVED', json.dumps(self.deliver(context, epoch='E1')))
        self.assertEqual(self.store.get(self.key)['restore']['reads'], {})
        new = self.record / 'new.md'
        new.write_text('new requirement\n')
        self.index.write_text(self.index.read_text().replace('evidence.md\n<!-- workflow-manifest:end', 'evidence.md\nnew.md\n<!-- workflow-manifest:end'))
        for path in paths:
            self.deliver(path)
        self.denied(self.pre())
        self.assertIn('new.md', json.dumps(self.control('restore-status')))
        self.deliver(new)
        self.assertNotIn('restore', self.store.get(self.key))

    def confirm(self, **overrides):
        values = {'record': str(self.record), 'epoch': 'E1',
                  'summary': 'Read checkpoint and mode rules: scoped fix, user stop retained, next step inspect tests.'}
        values.update(overrides)
        args = ['restore-confirm']
        for key, value in values.items():
            args.extend(['--' + key, value])
        return self.control(*args)

    def test_confirmation_accepts_ordinary_reads_and_preserves_task_record_and_stop(self):
        state = self.store.get(self.key)
        state.update(recovery={'reason': 'user-stop'}, action={'id': 'pending'},
                     checkpoint_required=True, rules_sync_required=True)
        self.store.mutate(self.key, lambda _old: state)
        before = {p.name: p.read_bytes() for p in self.record.iterdir()}
        self.pre('read_file', {'path': str(self.index)})
        self.assertEqual(self.store.get(self.key)['restore']['reads'], {})
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(self.confirm()))
        after = self.store.get(self.key)
        for key in ('recovery', 'action', 'checkpoint_required', 'rules_sync_required', 'record'):
            self.assertEqual(after[key], state[key])
        self.assertEqual(after['last_restoration']['basis'], 'agent-confirmed')
        self.assertNotIn('summary', after['last_restoration'])
        self.assertNotIn('restore', after)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.record.iterdir()})
        self.assertNotIn('permissionDecision', self.pre()['hookSpecificOutput'])

    def test_literal_wrapper_confirmation_works_in_every_mode_without_post_tool(self):
        for mode in ('discuss', 'plan', 'execute'):
            with self.subTest(mode=mode):
                state = self.store.get(self.key)
                state['mode'] = mode
                state['restore'] = {'epoch': 'E1', 'reads': {}, 'skill_root': str(self.skill)}
                self.store.mutate(self.key, lambda _old: state)
                args = [sys.executable, str(CONTROL), 'restore-confirm', '--record', str(self.record),
                        '--epoch', 'E1', '--summary', 'Read scope, stops and checkpoint for next scoped step.',
                        '--marker', hook.MARKER]
                literal = 'text(await tools.exec_command(' + json.dumps({'cmd': shlex.join(args)}) + '));'
                output = self.pre('functions.exec', literal)
                self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(output))
                self.assertNotIn('restore', self.store.get(self.key))

    def test_invalid_confirmations_leave_gate_pending(self):
        for changes in ({'record': str(self.root)}, {'epoch': 'old'}, {'summary': ''},
                        {'summary': '   '}, {'summary': 'x' * 2001}, {'unknown': 'value'}):
            with self.subTest(changes=changes):
                self.assertIn('WORKFLOW_RESTORE_CONFIRM_INVALID', json.dumps(self.confirm(**changes)))
                self.denied(self.pre())
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(self.confirm()))
        self.assertIn('WORKFLOW_RESTORE_CONFIRM_INVALID', json.dumps(self.confirm()))

    def test_unobserved_output_does_not_deadlock_honest_confirmation(self):
        args = [sys.executable, str(CONTROL), 'restore-read', '--record', str(self.record),
                '--path', str(self.index), '--epoch', 'E1', '--marker', hook.MARKER]
        payload = {'tool_name': 'exec_command', 'tool_input': {'cmd': shlex.join(args)},
                   'cwd': str(self.root), 'tool_response': {'unsupported': 'envelope'}}
        output = hook.handle_post_tool(self.store, self.key, payload)
        self.assertIn('WORKFLOW_RESTORE_READ_NOT_OBSERVED', json.dumps(output))
        self.assertIn('restore-confirm', json.dumps(output))
        self.assertEqual(self.store.get(self.key)['restore']['reads'], {})
        self.pre('read_file', {'path': str(self.index)})
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(self.confirm()))
        self.assertEqual(self.store.get(self.key)['last_restoration']['basis'], 'agent-confirmed')

    def test_catalog_gap_does_not_veto_scoped_confirmation(self):
        self.index.write_text(self.index.read_text().replace('evidence.md\n<!-- workflow-manifest:end',
                                                            'evidence.md\narchive.md\n<!-- workflow-manifest:end'))
        self.assertFalse(hook.restoration_scope(self.store.get(self.key))[1])
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(self.confirm(
            summary='Read checkpoint, scope and mode rules for current tests; unrelated archive missing, repair deferred.')))

    def test_new_compaction_requires_fresh_confirmation(self):
        self.confirm()
        state = self.store.get(self.key)
        hook.begin_restoration(state)
        self.store.mutate(self.key, lambda _old: state)
        self.assertIn('WORKFLOW_RESTORE_CONFIRM_INVALID', json.dumps(self.confirm()))
        self.denied(self.pre())
        self.assertIn('WORKFLOW_CONTEXT_RESTORED', json.dumps(self.confirm(epoch=state['restore']['epoch'])))

    def test_compound_control_and_wrapper_do_not_exempt_companion_mutations(self):
        command = shlex.join([sys.executable, str(CONTROL), 'restore-status', '--marker', hook.MARKER])
        self.denied(self.pre('exec_command', {'cmd': command + '; touch app.py'}))
        literal = 'text(await tools.exec_command(' + json.dumps({'cmd': command}) + '));'
        self.assertNotIn('permissionDecision', self.pre('functions.exec', literal)['hookSpecificOutput'])
        self.denied(self.pre('functions.exec', literal + ' await other();'))
        payload = {'tool_name': 'apply_patch', 'tool_input': f'*** Update File: {self.index}\n'}
        literal = 'text(await tools.apply_patch(' + json.dumps(payload['tool_input']) + '));'
        self.assertNotIn('permissionDecision', self.pre('functions.exec', literal)['hookSpecificOutput'])


if __name__ == '__main__':
    unittest.main()
