# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Exercise the remote stream lifetime without a camera or network access."""
from pathlib import Path
import subprocess
import sys
import unittest


BRIDGE = Path(__file__).resolve().parents[1] / 'davekvm-bridge'
BOOTSTRAP = r'''
import os, re, select, sys, time, types
class FakeProcess:
    returncode = None
    def poll(self): return self.returncode
    def terminate(self):
        self.returncode = 0
        print('terminated', flush=True)
    def wait(self, timeout=None): return self.returncode
    def kill(self): self.returncode = -9
subprocess = types.SimpleNamespace(Popen=lambda *a, **k: FakeProcess(), TimeoutExpired=TimeoutError)
devices = lambda: [{'id': 'video0'}]
command = 'stream video0'
source = open(sys.argv[1]).read()
exec(source[source.index("match = re.fullmatch(r'stream "):], globals())
'''


class StreamWatchdogTests(unittest.TestCase):
    def start_bridge(self):
        return subprocess.Popen([sys.executable, '-c', BOOTSTRAP, str(BRIDGE)],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def test_stream_terminates_when_stdin_closes(self):
        process = self.start_bridge()
        try:
            process.stdin.write(b'\0')
            process.stdin.flush()
            process.stdin.close()
            self.assertEqual(process.wait(timeout=4), 0)
            self.assertEqual(process.stdout.read().strip(), b'terminated')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
            process.stderr.close()

    def test_stream_terminates_without_heartbeats(self):
        process = self.start_bridge()
        try:
            self.assertEqual(process.wait(timeout=13), 0)
            self.assertEqual(process.stdout.read().strip(), b'terminated')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()


if __name__ == '__main__':
    unittest.main()
