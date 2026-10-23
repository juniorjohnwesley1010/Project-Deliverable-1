"""Pseudo-terminal tests exercise real POSIX foreground groups and signal control."""
from pathlib import Path
import re
import sys
import tempfile
import time
import unittest

try:
    import pexpect
except ImportError:
    pexpect = None

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(pexpect is None, 'pexpect is only needed for PTY tests')
class InteractiveJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.child = pexpect.spawn(sys.executable, [str(ROOT / 'main.py')],
                                   cwd=self.temp.name, encoding='utf-8', timeout=8)
        self.child.expect_exact('CustomOS> ')

    def tearDown(self):
        if self.child.isalive():
            self.child.sendline('exit')
            self.child.expect(pexpect.EOF, timeout=5)
        self.child.close(force=True)
        self.temp.cleanup()

    def test_background_then_foreground(self):
        self.child.sendline('sleep 1 &')
        self.child.expect(r'\[1\] \d+')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('jobs')
        self.child.expect(r'\[1\] Running')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('fg 1')
        self.child.expect_exact('CustomOS> ', timeout=5)
        self.child.sendline('jobs')
        self.child.expect_exact('No jobs.')
        self.child.expect_exact('CustomOS> ')

    def test_ctrl_z_bg_fg_ctrl_c(self):
        self.child.sendline('sleep 30')
        time.sleep(0.3)
        self.child.sendcontrol('z')
        self.child.expect(r'\[1\] Stopped')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('bg 1')
        self.child.expect(r'\[1\] Running')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('jobs')
        self.child.expect(r'\[1\] Running')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('fg 1')
        time.sleep(0.3)
        self.child.sendcontrol('c')
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('jobs')
        self.child.expect_exact('No jobs.')
        self.child.expect_exact('CustomOS> ')

    def test_kill_background_process(self):
        self.child.sendline('sleep 30 &')
        self.child.expect(r'\[1\] (\d+)')
        pid = self.child.match.group(1)
        self.child.expect_exact('CustomOS> ')
        self.child.sendline('kill ' + pid)
        self.child.expect('Sent SIGTERM to PID')
        self.child.expect_exact('CustomOS> ')
        time.sleep(0.25)
        self.child.sendline('jobs')
        self.child.expect(r'\[1\] Terminated')
        self.child.expect_exact('CustomOS> ')


if __name__ == '__main__':
    unittest.main()
