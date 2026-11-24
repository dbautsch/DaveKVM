# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Exercise HID report framing and lease safety without attached hardware."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('davekvm_keyboard_test', Path(__file__).resolve().parents[1] / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def acknowledgement(command):
    frame = bytes([0x57, 0xab, 0, command | 0x80, 1, 0])
    return frame + bytes([sum(frame) & 255])


class KeyboardTests(unittest.TestCase):
    def test_valid_report_and_invalid_acknowledgement(self):
        with patch.object(server.threading, 'Thread'):
            keyboard = server.Keyboard('video0')
        port = Mock()
        port.read.return_value = acknowledgement(2)
        keyboard.port = port
        keyboard.report(2, [4])
        frame = bytes([0x57, 0xab, 0, 2, 8, 2, 0, 4, 0, 0, 0, 0, 0])
        port.write.assert_called_once_with(frame + bytes([sum(frame) & 255]))
        port.read.return_value = b'bad'
        with self.assertRaises(server.KeyboardError):
            keyboard.report(0, [], force=True)

    def test_expired_lease_refuses_input_and_releases(self):
        with patch.object(server.threading, 'Thread'):
            keyboard = server.Keyboard('video0')
        keyboard.token = 'lease'
        keyboard.expiry = 1
        with patch.object(server.time, 'monotonic', return_value=2), \
             patch.object(keyboard, 'close') as close:
            with self.assertRaises(server.KeyboardError):
                keyboard.update('lease', 0, [])
        close.assert_called_once()

    def test_wrong_lease_cannot_send_input(self):
        with patch.object(server.threading, 'Thread'):
            keyboard = server.Keyboard('video0')
        keyboard.token = 'correct'
        with patch.object(keyboard, 'report') as report:
            with self.assertRaises(server.KeyboardError):
                keyboard.update('wrong', 0, [4])
        report.assert_not_called()


if __name__ == '__main__':
    unittest.main()
