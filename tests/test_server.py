# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
import importlib.util
import io
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import Mock, patch


with patch.object(Path, 'read_text', return_value='test'):
    spec = importlib.util.spec_from_file_location('davekvm_server', Path(__file__).resolve().parents[1] / 'server.py')
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)


def part(frame):
    return (b'--frame\r\nContent-type: image/jpeg\r\nContent-length: ' +
            str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')


class FramesTest(unittest.TestCase):
    def test_skips_corrupt_first_frame(self):
        valid = b'\xff\xd8image\xff\xd9'
        self.assertEqual(server.first_valid_frame(io.BytesIO(part(b'broken') + part(valid))), part(valid))

    def test_rejects_incomplete_frame(self):
        with self.assertRaises(EOFError):
            server.first_valid_frame(io.BytesIO(b'--frame\r\nContent-length: 20\r\n\r\nshort'))


class WebEncoderTest(unittest.TestCase):
    def test_encoder_settings_are_validated_and_passed_as_arguments(self):
        options = server.web_encoder_options('preset=superfast&crf=18&bitrate=4500')
        command = server.web_encoder_command('remote-video0', options)
        self.assertEqual(command[command.index('-preset') + 1], 'superfast')
        self.assertEqual(command[command.index('-crf') + 1], '18')
        self.assertEqual(command[command.index('-maxrate') + 1], '4500k')
        self.assertEqual(command[command.index('-bufsize') + 1], '562k')

    def test_encoder_settings_reject_unknown_duplicate_and_out_of_range_values(self):
        for query in ('preset=evil', 'crf=-1', 'crf=0', 'crf=31', 'bitrate=0',
                      'bitrate=30001', 'crf=12&crf=13', 'codec=h265', 'bitrate=8000k'):
            with self.subTest(query=query), self.assertRaises(ValueError):
                server.web_encoder_options(query)

    def test_qsv_uses_existing_video_access_and_low_latency_settings(self):
        for encoder in ('h264_qsv', 'hevc_qsv'):
            with self.subTest(encoder=encoder):
                options = server.web_encoder_options('encoder=' + encoder + '&bitrate=4000')
                command = server.web_encoder_command('remote-video0', options)
                self.assertIn('vaapi=va:/dev/dri/card0', command)
                self.assertEqual(command[command.index('-c:v') + 1], encoder)
                self.assertEqual(command[command.index('-b:v') + 1], '4000k')
                self.assertEqual(command[command.index('-async_depth') + 1], '1')
                self.assertEqual(command[command.index('-bf') + 1], '0')
                self.assertEqual('-tag:v' in command, encoder == 'hevc_qsv')

    def test_input_rate_follows_existing_capture_configuration(self):
        for device, expected in [('remote-video0', '30'), ('video0', '60')]:
            command = server.web_encoder_command(device)
            self.assertEqual(command[command.index('-r') + 1], expected)
            self.assertEqual(command[command.index('-c:v') + 1], 'libx264')
            self.assertEqual(command[command.index('-bf') + 1], '0')

    def test_feeder_uses_sequence_from_source_and_closes_pipe(self):
        read_fd, write_fd = os.pipe()
        proc = Mock()
        proc.poll.return_value = None
        proc.stdin = os.fdopen(write_fd, 'wb', buffering=0)
        capture = Mock()
        capture.get.side_effect = [(9, b'first'), (14, b'latest'), RuntimeError('ended')]
        try:
            server.feed_web_encoder(capture, proc, threading.Event())
            self.assertEqual(os.read(read_fd, 64), b'firstlatest')
            self.assertEqual([c.args[0] for c in capture.get.call_args_list], [-1, 9, 14])
            self.assertTrue(proc.stdin.closed)
        finally:
            os.close(read_fd)

    def test_qsv_quality_modes_and_profiles(self):
        for encoder in ('h264_qsv', 'hevc_qsv'):
            for mode in ('icq', 'cqp', 'cbr', 'vbr'):
                with self.subTest(encoder=encoder, mode=mode):
                    options = server.web_encoder_options(
                        'encoder=' + encoder + '&qsv_profile=main&qsv_preset=medium'
                        '&qsv_mode=' + mode + '&qsv_quality=18&qsv_gop=60&bitrate=4000')
                    command = server.web_encoder_command('remote-video0', options)
                    self.assertEqual(command[command.index('-preset') + 1], 'medium')
                    self.assertEqual(command[command.index('-profile:v') + 1], 'main')
                    self.assertEqual(command[command.index('-g') + 1], '60')
                    self.assertEqual('-global_quality' in command, mode in ('icq', 'cqp'))
                    self.assertEqual('-qscale:v' in command, mode == 'cqp')
                    self.assertEqual('-maxrate' in command, mode in ('cbr', 'vbr'))
                    if mode == 'vbr':
                        self.assertEqual(command[command.index('-maxrate') + 1], '8000k')

    def test_qsv_rejects_invalid_controls(self):
        for query in ('qsv_mode=bad', 'qsv_quality=0', 'qsv_quality=52',
                      'qsv_gop=14', 'qsv_gop=301', 'qsv_preset=bad',
                      'encoder=hevc_qsv&qsv_profile=high', 'qsv_mode=vbr&bitrate=30000'):
            with self.subTest(query=query), self.assertRaises(ValueError):
                server.web_encoder_options(query)

    def test_encoder_start_failure_releases_capture_and_slot(self):
        handler = Mock()
        capture = Mock()
        slots = threading.BoundedSemaphore(1)
        with patch.object(server, 'web_encoder_slots', slots), \
             patch.object(server, 'get_capture', return_value=capture), \
             patch.object(server.subprocess, 'Popen', side_effect=OSError('missing')):
            server.Handler.web_h264(handler, 'remote-video0')
        capture.acquire.assert_called_once()
        capture.release.assert_called_once()
        handler.send_error.assert_called_once_with(503)
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()

    def test_busy_encoder_does_not_acquire_capture(self):
        handler = Mock()
        slots = threading.BoundedSemaphore(1)
        slots.acquire()
        with patch.object(server, 'web_encoder_slots', slots), \
             patch.object(server, 'get_capture') as get_capture:
            server.Handler.web_h264(handler, 'remote-video0')
        get_capture.assert_not_called()
        handler.send_error.assert_called_once_with(503, 'H264 encoder busy')
        slots.release()

    def test_slow_client_timeout_stops_encoder_and_releases_capture(self):
        handler = Mock()
        handler.wfile.write.side_effect = [None, TimeoutError('slow client')]
        capture = Mock()
        proc = Mock()
        proc.poll.return_value = None
        slots = threading.BoundedSemaphore(1)
        feeder = Mock()
        with patch.object(server, 'web_encoder_slots', slots), \
             patch.object(server, 'get_capture', return_value=capture), \
             patch.object(server.subprocess, 'Popen', return_value=proc), \
             patch.object(server.threading, 'Thread', return_value=feeder), \
             patch.object(server.select, 'select', return_value=([proc.stdout], [], [])), \
             patch.object(server.os, 'read', side_effect=[b'header', b'fragment']):
            server.Handler.web_h264(handler, 'remote-video0')
        proc.terminate.assert_called_once()
        feeder.join.assert_called_once_with(timeout=2)
        capture.release.assert_called_once()
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()

    def test_thread_start_failure_releases_capture_and_slot(self):
        handler = Mock()
        capture = Mock()
        proc = Mock()
        proc.poll.return_value = None
        feeder = Mock()
        feeder.start.side_effect = RuntimeError('cannot start thread')
        slots = threading.BoundedSemaphore(1)
        with patch.object(server, 'web_encoder_slots', slots), \
             patch.object(server, 'get_capture', return_value=capture), \
             patch.object(server.subprocess, 'Popen', return_value=proc), \
             patch.object(server.threading, 'Thread', return_value=feeder):
            server.Handler.web_h264(handler, 'remote-video0')
        feeder.join.assert_not_called()
        proc.terminate.assert_called_once()
        proc.stdout.close.assert_called_once()
        capture.release.assert_called_once()
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()

    def test_encoder_exit_during_termination_releases_capture_and_slot(self):
        handler = Mock()
        capture = Mock()
        proc = Mock()
        proc.poll.return_value = None
        proc.terminate.side_effect = ProcessLookupError()
        slots = threading.BoundedSemaphore(1)
        with patch.object(server, 'web_encoder_slots', slots), \
             patch.object(server, 'get_capture', return_value=capture), \
             patch.object(server.subprocess, 'Popen', return_value=proc), \
             patch.object(server.threading, 'Thread'), \
             patch.object(server.select, 'select', return_value=([], [], [])):
            server.Handler.web_h264(handler, 'remote-video0')
        proc.wait.assert_called_once_with(timeout=3)
        capture.release.assert_called_once()
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()


if __name__ == '__main__':
    unittest.main()
