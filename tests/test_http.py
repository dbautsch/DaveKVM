# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""HTTP security and integration tests with simulated devices only."""
import base64
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('davekvm_server', Path(__file__).resolve().parents[1] / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.Server(('127.0.0.1', 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        server.ORIGIN = f'http://127.0.0.1:{cls.port}'
        server.PASSWORD = 'local-test-password-not-secret'
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)

    def request(self, method, path, headers=None, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def auth(self):
        credentials = base64.b64encode((server.USERNAME + ':' + server.PASSWORD).encode()).decode()
        return {'Authorization': 'Basic ' + credentials}

    def test_authentication_and_device_inventory(self):
        self.assertEqual(self.request('GET', '/grabber/api/devices')[0], 401)
        with patch.object(server, 'devices', return_value=[{'id': 'video0', 'name': 'Demo'}]), \
             patch.object(server, 'SSH', None), patch.object(server, 'SERIAL_MAP', {'video0': '/dev/serial/by-id/example'}):
            status, payload = self.request('GET', '/grabber/api/devices', self.auth())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload), [{'id': 'video0', 'name': 'Demo', 'control': True}])
        headers = dict(self.auth(), Host='untrusted.example')
        self.assertEqual(self.request('GET', '/grabber/api/devices', headers)[0], 403)

    def test_state_change_requires_exact_origin_and_json(self):
        headers = dict(self.auth(), Origin='http://untrusted.example', **{'Content-Type':'application/json'})
        self.assertEqual(self.request('POST', '/grabber/api/keyboard/acquire', headers, b'{}')[0], 403)
        headers['Origin'] = server.ORIGIN
        headers['Content-Type'] = 'text/plain'
        self.assertEqual(self.request('POST', '/grabber/api/keyboard/acquire', headers, b'{}')[0], 403)
        headers['Content-Type'] = 'application/json'
        self.assertEqual(self.request('POST', '/grabber/api/keyboard/acquire', headers, b'{}')[0], 409)

    def test_capture_and_control_round_trip_without_hardware(self):
        capture = Mock()
        capture.get.return_value = (1, b'--frame\r\nContent-type: image/jpeg\r\n\r\n\xff\xd8demo\xff\xd9\r\n')
        keyboard = Mock()
        keyboard.acquire.return_value = 'a' * 43
        headers = dict(self.auth(), Origin=server.ORIGIN, **{'Content-Type': 'application/json'})
        with patch.object(server, 'devices', return_value=[{'id': 'video0', 'name': 'Demo'}]), \
             patch.object(server, 'SSH', None), patch.object(server, 'get_capture', return_value=capture), \
             patch.object(server, 'keyboards', {'video0': keyboard}), \
             patch.object(server, 'keyboard_for_token', return_value=keyboard):
            status, frame = self.request('GET', '/grabber/snapshot/video0.jpg', self.auth())
            self.assertEqual((status, frame), (200, b'\xff\xd8demo\xff\xd9'))
            status, result = self.request('POST', '/grabber/api/keyboard/acquire', headers,
                                          json.dumps({'device': 'video0'}).encode())
            self.assertEqual(status, 200)
            token = json.loads(result)['token']
            payload = {'token': token, 'modifiers': 0, 'keys': [4]}
            status, _ = self.request('POST', '/grabber/api/keyboard/state', headers,
                                     json.dumps(payload).encode())
            self.assertEqual(status, 200)
            status, _ = self.request('POST', '/grabber/api/keyboard/release', headers,
                                     json.dumps({'token': token}).encode())
            self.assertEqual(status, 200)
        capture.release.assert_called_once()
        keyboard.update.assert_called_once_with(token, 0, [4])
        keyboard.release.assert_called_once_with(token)


if __name__ == '__main__':
    unittest.main()
