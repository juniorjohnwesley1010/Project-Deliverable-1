import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShellIntegrationTests(unittest.TestCase):
    def run_shell(self, script):
        with tempfile.TemporaryDirectory() as tempdir:
            done = subprocess.run(
                [sys.executable, str(ROOT / 'main.py')],
                input=script, text=True, cwd=tempdir, capture_output=True,
                timeout=15,
            )
            return done, Path(tempdir)

    def test_file_and_directory_commands(self):
        done, _ = self.run_shell('''pwd
mkdir workspace
cd workspace
touch example.txt
ls
cat example.txt
echo Hello OS!
rm example.txt
cd ..
rmdir workspace
exit
''')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('example.txt', done.stdout)
        self.assertIn('Hello OS!', done.stdout)
        self.assertNotIn('Error:', done.stdout)

    def test_external_foreground_execution(self):
        done, _ = self.run_shell('echo Running\npython3 -c "print(42)"\nexit\n')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('42', done.stdout)

    def test_error_handling(self):
        done, _ = self.run_shell('''bad_command_that_does_not_exist
cat missing.txt
rmdir missing_dir
kill abc
fg nope
bg 999
echo "unclosed
mkdir
ls | grep txt
exit
''')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertGreaterEqual(done.stdout.count('Error:'), 8)
        self.assertIn('command not found', done.stdout)
        self.assertIn('reserved for Deliverable 4', done.stdout)

    def test_background_list(self):
        done, _ = self.run_shell('sleep 2 &\njobs\nexit\n')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('[1]', done.stdout)
        self.assertIn('Running', done.stdout)


if __name__ == '__main__':
    unittest.main()
