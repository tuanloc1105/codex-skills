"""Disposable checks of documented Git recipes, not assistant behavior."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class TargetEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.put('calc.py', 'def calc(x):\n    return x + 1\n')
        self.put('.gitignore', '*.ignored\n')
        self.commit()

    def git(self, *args, input=None, ok=(0,)):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        result = subprocess.run(['git', '-C', str(self.repo), *args],
                                input=input, text=True, capture_output=True, env=env)
        self.assertIn(result.returncode, ok, result.stderr)
        return result.stdout

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture')

    def feature(self):
        self.git('checkout', '-b', 'feature')
        self.put('calc.py', 'def calc(x):\n    return x / 0\n')
        self.commit()

    def test_T01_pushed_feature(self):
        self.feature()
        self.git('remote', 'add', 'origin', str(self.root / 'unused'))
        self.git('update-ref', 'refs/remotes/origin/feature', 'HEAD')
        self.git('update-ref', 'refs/remotes/origin/main', 'main')
        self.git('symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main')
        self.git('branch', '--set-upstream-to=origin/feature')
        before = self.git('show-ref')
        index = (self.repo / '.git/index').read_bytes()
        self.assertEqual(self.git('diff', '@{upstream}...HEAD'), '')
        default = self.git('symbolic-ref', 'refs/remotes/origin/HEAD').strip()
        base = self.git('merge-base', default, 'HEAD').strip()
        self.assertIn('-    return x + 1\n+    return x / 0\n', self.git('diff', base))
        self.assertEqual(self.git('show-ref'), before)
        self.assertEqual((self.repo / '.git/index').read_bytes(), index)

    def test_T02_explicit_endpoints(self):
        self.feature()
        self.git('checkout', 'main')
        self.put('destination.txt', 'destination only\n')
        self.commit()
        self.git('checkout', 'feature')
        two = self.git('diff', 'main..feature')
        three = self.git('diff', 'main...feature')
        self.assertIn('deleted file mode', two)
        self.assertNotIn('destination.txt', three)
        self.assertIn('+    return x / 0', three)
        self.assertEqual(three, self.git('diff', self.git('merge-base', 'main', 'feature').strip(), 'feature'))

    def test_T03_cancellation(self):
        self.feature()
        self.put('calc.py', 'def calc(x):\n    return x + 1\n')
        self.assertIn('+    return x / 0', self.git('diff', 'main...HEAD'))
        self.assertIn('-    return x / 0', self.git('diff', 'HEAD'))
        self.assertEqual(self.git('diff', self.git('merge-base', 'main', 'HEAD').strip()), '')

    def test_T04_snapshots(self):
        self.feature()
        self.put('calc.py', 'staged\n')
        self.git('add', 'calc.py')
        self.put('calc.py', 'final\n')
        self.assertIn('+staged\n', self.git('diff', '--cached', 'HEAD'))
        self.assertIn('-staged\n+final\n', self.git('diff'))
        worktree = self.git('diff', 'HEAD')
        self.assertIn('-    return x / 0\n+final\n', worktree)
        self.assertNotIn('return x + 1', worktree)

    def test_T05_untracked_filters_and_recreation(self):
        for name in ['new.py', 'secret.ignored', 'excluded.py']:
            self.put(name, 'new\n')
        names = self.git('ls-files', '--others', '--exclude-standard', '-z', '--', '.', ':(exclude)excluded.py').split('\0')
        self.assertEqual([n for n in names if n], ['new.py'])
        self.assertIn('+new\n', self.git('diff', '--no-index', '--', os.devnull, 'new.py', ok=(1,)))
        baseline = self.git('show', 'HEAD:calc.py')
        self.git('rm', '--cached', 'calc.py')
        self.assertIn('deleted file mode', self.git('diff', 'HEAD'))
        self.assertIn('calc.py', self.git('ls-files', '--others', '--exclude-standard'))
        old = self.root / 'baseline.py'
        old.write_text(baseline)
        self.assertEqual(self.git('diff', '--no-index', '--', str(old), 'calc.py'), '')

    def test_T06_metadata(self):
        self.put('remove.txt', 'remove\n')
        self.put('mode.sh', '#!/bin/sh\n')
        self.commit()
        self.git('mv', 'calc.py', 'renamed.py')
        (self.repo / 'remove.txt').unlink()
        (self.repo / 'mode.sh').chmod(0o755)
        self.git('config', 'core.filemode', 'true')
        patch = self.git('diff', '--find-renames', 'HEAD')
        self.assertIn('rename from calc.py\nrename to renamed.py', patch)
        self.assertIn('deleted file mode', patch)
        self.assertIn('old mode 100644\nnew mode 100755', patch)
        raw = self.git('diff', '--name-status', '-z', '--find-renames', 'HEAD')
        self.assertIn('R100\0calc.py\0renamed.py\0', raw)
        self.assertNotIn('@@', self.git('diff', 'HEAD', '--', 'mode.sh'))

    def test_T07_root_missing_and_shallow(self):
        empty = self.git('hash-object', '-t', 'tree', '--stdin', input='').strip()
        self.assertIn('new file mode', self.git('diff', empty, 'HEAD'))
        self.git('rev-parse', '--verify', 'HEAD^', ok=(128,))
        self.git('rev-parse', '--verify', 'missing-explicit', ok=(128,))
        self.feature()
        self.git('branch', '-D', 'main')
        self.assertIn('+    return x / 0', self.git('diff', 'HEAD^'))
        shallow = self.root / 'shallow'
        self.git('clone', '--depth=1', self.repo.as_uri(), str(shallow))
        self.repo = shallow
        self.assertEqual(self.git('rev-parse', '--is-shallow-repository').strip(), 'true')
        before = self.git('show-ref')
        self.git('rev-parse', '--verify', 'HEAD^', ok=(128,))
        self.assertEqual(before, self.git('show-ref'))


if __name__ == '__main__':
    unittest.main()
