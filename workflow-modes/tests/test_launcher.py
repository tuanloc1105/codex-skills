from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'plugin with spaces'
        shutil.copytree(ROOT / 'scripts', self.root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        self.env = {**os.environ, 'PLUGIN_ROOT': str(self.root), 'PLUGIN_DATA': str(Path(self.temp.name) / 'state')}
        self.hooks = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']

    def invoke(self, event='PreToolUse', raw=None, launcher=False, env=None):
        if raw is None:
            raw = json.dumps({'hook_event_name': event, 'session_id': 'launcher-test',
                              'tool_name': 'exec_command', 'tool_input': {'cmd': 'pwd'}})
        if launcher:
            handler = self.hooks[event][0]['hooks'][0]
            command = [os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/s', '/c', handler['commandWindows']] if os.name == 'nt' else ['/bin/sh', '-c', handler['command']]
        else:
            command = [sys.executable, str(self.root / 'scripts/workflow_modes_supervisor.py'), event]
        return subprocess.run(command, input=raw, capture_output=True, text=True, env=env or self.env, timeout=8)

    def assert_failure_policy(self, code, *, raw=None, launcher=False):
        tool = self.invoke('PreToolUse', raw, launcher)
        self.assertEqual(tool.returncode, 2, tool.stdout + tool.stderr)
        self.assertIn(code, tool.stderr)
        self.assertIn('Next:', tool.stderr)
        self.assertFalse(tool.stdout)
        stop_raw = raw
        if raw and raw.startswith('{'):
            try:
                payload = json.loads(raw)
                payload['hook_event_name'] = 'Stop'
                stop_raw = json.dumps(payload)
            except ValueError:
                pass
        stop = self.invoke('Stop', stop_raw, launcher)
        self.assertEqual(stop.returncode, 0, stop.stdout + stop.stderr)
        self.assertIn(code, stop.stderr)
        self.assertTrue(stop.stdout, "Nonblocking infrastructure failure must still surface a warning")
        self.assertNotEqual(json.loads(stop.stdout).get('decision'), 'block')
        self.assertNotIn('Traceback', tool.stderr + stop.stderr)

    def test_healthy_launch_is_dormant(self):
        for event in self.hooks:
            result = self.invoke(event, launcher=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(result.stderr, '')

    def test_input_failures(self):
        for raw in ('{', '[]', '', '{}', '{"session_id":42}'):
            with self.subTest(raw=raw):
                self.assert_failure_policy('WORKFLOW_HOOK_INPUT_INVALID', raw=raw)

    def test_event_mismatch_blocks_tools(self):
        result = self.invoke(raw=json.dumps({'hook_event_name': 'Stop', 'session_id': 'test'}))
        self.assertEqual(result.returncode, 2)
        self.assertIn('WORKFLOW_HOOK_INPUT_INVALID', result.stderr)

    def test_state_path_is_file(self):
        Path(self.env['PLUGIN_DATA']).write_text('preserve')
        self.assert_failure_policy('WORKFLOW_HOOK_FILESYSTEM_FAILED')
        self.assertEqual(Path(self.env['PLUGIN_DATA']).read_text(), 'preserve')

    def test_corrupt_database_is_not_reset(self):
        root = Path(self.env['PLUGIN_DATA']); root.mkdir()
        database = root / 'workflow-modes.sqlite3'; database.write_bytes(b'not sqlite')
        self.assert_failure_policy('WORKFLOW_HOOK_STORAGE_FAILED')
        self.assertEqual(database.read_bytes(), b'not sqlite')

    def test_locked_database_produces_guidance(self):
        self.invoke()
        database = Path(self.env['PLUGIN_DATA']) / 'workflow-modes.sqlite3'
        connection = sqlite3.connect(database)
        self.addCleanup(connection.close)
        connection.execute('BEGIN IMMEDIATE')
        payload = {'hook_event_name': 'UserPromptSubmit', 'session_id': 'launcher-test'}
        # SessionEnd always writes; its shorter watchdog still yields actionable
        # infrastructure diagnostics instead of asking the model to continue.
        result = self.invoke('SessionEnd', raw=json.dumps({**payload, 'hook_event_name': 'SessionEnd'}))
        self.assertEqual(result.returncode, 0)
        self.assertIn('WORKFLOW_HOOK_TIMEOUT', result.stderr)
        connection.rollback()

    def test_hook_script_missing(self):
        (self.root / 'scripts/workflow_modes_hook.py').unlink()
        self.assert_failure_policy('WORKFLOW_HOOK_SCRIPT_MISSING', launcher=True)

    def test_hook_import_failure_does_not_expose_traceback(self):
        (self.root / 'scripts/workflow_modes_record.py').unlink()
        self.assert_failure_policy('WORKFLOW_HOOK_CHILD_FAILED', launcher=True)

    def test_supervisor_missing(self):
        (self.root / 'scripts/workflow_modes_supervisor.py').unlink()
        self.assert_failure_policy('WORKFLOW_HOOK_LAUNCH_FAILED', launcher=True)

    def test_whole_bundle_missing_uses_inline_fallback(self):
        shutil.rmtree(self.root)
        self.assert_failure_policy('WORKFLOW_HOOK_LAUNCHER_MISSING', launcher=True)

    @unittest.skipIf(os.name == 'nt', 'POSIX interpreter discovery; Windows launcher is covered on Windows')
    def test_python_missing(self):
        empty_path = Path(self.temp.name) / 'empty-path'; empty_path.mkdir()
        self.env['PATH'] = str(empty_path)
        self.assert_failure_policy('WORKFLOW_HOOK_LAUNCH_FAILED', launcher=True)

    def test_timeout(self):
        (self.root / 'scripts/workflow_modes_hook.py').write_text('import time\ntime.sleep(10)\n')
        self.assert_failure_policy('WORKFLOW_HOOK_TIMEOUT')

    def test_child_output_validation(self):
        for code in ('print("garbage")', 'print("[]")', 'print("null")', 'print(\'{"continue":false}\')',
                     'print(\'{"hookSpecificOutput":{"hookEventName":"Other"}}\')',
                     'import sys\nprint("{}")\nprint("raw error", file=sys.stderr)'):
            with self.subTest(code=code):
                (self.root / 'scripts/workflow_modes_hook.py').write_text(code)
                result = self.invoke()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(result.stdout)
                self.assertIn('WORKFLOW_HOOK_OUTPUT_INVALID', result.stderr)

    def test_unhashable_decision_is_diagnosed_without_traceback(self):
        script = self.root / 'scripts/workflow_modes_hook.py'
        script.write_text('import json\nprint(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":[]}}))\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertIn('WORKFLOW_HOOK_OUTPUT_INVALID', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_valid_policy_block_is_preserved(self):
        script = self.root / 'scripts/workflow_modes_hook.py'
        script.write_text('import json\nprint(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"WORKFLOW_TEST: do something"}}))\n')
        tool = self.invoke()
        self.assertEqual(tool.returncode, 0)
        self.assertEqual(json.loads(tool.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')
        script.write_text('import json\nprint(json.dumps({"decision":"block","reason":"WORKFLOW_TEST: finish action"}))\n')
        stop = self.invoke('Stop')
        self.assertEqual(json.loads(stop.stdout)['decision'], 'block')

    def test_every_runtime_file_is_required_by_installer(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        self.addCleanup(sys.path.remove, str(ROOT / 'scripts'))
        import install
        for file in install.REQUIRED_PATHS:
            if not str(file).startswith('scripts/'):
                continue
            with self.subTest(file=file):
                copy = self.root / file
                backup = copy.read_bytes()
                copy.unlink()
                # Fill the non-script required files for this isolated bundle.
                for relative in ('.codex-plugin/plugin.json', 'hooks/hooks.json'):
                    target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / relative, target)
                with self.assertRaises(install.InstallError):
                    install.validate_bundle(self.root)
                copy.write_bytes(backup)


if __name__ == '__main__':
    unittest.main()
