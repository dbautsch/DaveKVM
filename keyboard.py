#!/usr/bin/env python3
# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""CH9329 keyboard and mouse reports with exclusive expiring leases."""
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import select
import subprocess
import threading
import time

import serial
from messages import message


class KeyboardError(Exception):
    """Keyboard failure with a stable, language-independent code."""
    def __init__(self, code):
        self.code = code
        super().__init__(message(code))

class RemotePort:
    def __init__(self, device, ssh):
        self.proc = subprocess.Popen(ssh + ['keyboard ' + device], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        self.is_open = True
        try: self.receive()
        except Exception:
            self.close()
            raise

    def receive(self):
        if not select.select([self.proc.stdout], [], [], 5)[0]: raise KeyboardError('BRIDGE_TIMEOUT')
        line = self.proc.stdout.readline(1024)
        try: result = json.loads(line)
        except (ValueError, UnicodeDecodeError): raise KeyboardError('BRIDGE_INVALID_RESPONSE')
        if result != {'ok': True}: raise KeyboardError('REMOTE_KEYBOARD_ERROR')

    def report(self, command, payload):
        if command == 2:
            report = {'modifiers': payload[0], 'keys': [k for k in payload[2:] if k]}
        elif command == 4:
            report = {'mouse': [payload[2] | payload[3] << 8, payload[4] | payload[5] << 8, payload[1], payload[6] if payload[6] < 128 else payload[6] - 256]}
        elif command == 5:
            signed = lambda v: v if v < 128 else v - 256
            report = {'mouse_relative': [signed(payload[2]), signed(payload[3]), payload[1], signed(payload[4])]}
        else: raise KeyboardError('UNSUPPORTED_COMMAND')
        self.proc.stdin.write((json.dumps(report) + '\n').encode())
        self.receive()

    def close(self):
        if not self.is_open: return
        self.is_open = False
        try: self.proc.stdin.close()
        except OSError: pass
        try: self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try: self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill(); self.proc.wait()
        self.proc.stdout.close()

class Keyboard:
    """One short-lived exclusive lease, with automatic release of held keys."""
    def __init__(self, device, mapping=None, ssh=None):
        self.device = device
        self.mapping = mapping
        self.ssh = ssh
        self.lock = threading.Lock()
        self.token = None
        self.expiry = 0
        self.port = None
        self.current = (0, ())
        threading.Thread(target=self.watch, daemon=True).start()

    def packet(self, command, payload):
        if isinstance(self.port, RemotePort):
            self.port.report(command, payload)
            return
        frame = bytes([0x57, 0xab, 0, command, len(payload)]) + bytes(payload)
        self.port.write(frame + bytes([sum(frame) & 255]))
        self.port.flush()
        reply = self.port.read(7)
        if len(reply) != 7 or reply[:5] != bytes([0x57, 0xab, 0, command | 0x80, 1]) or reply[5] != 0 or sum(reply[:-1]) & 255 != reply[-1]:
            raise KeyboardError('CH9329_INVALID_ACK')

    def report(self, modifiers, keys, force=False):
        state = (modifiers, tuple(keys))
        if force or state != self.current:
            self.packet(2, [modifiers, 0] + list(keys) + [0] * (6-len(keys)))
            self.current = state

    def close(self):
        try:
            if self.port and self.port.is_open:
                try:
                    try: self.report(0, [], force=True)
                    finally: self.packet(5, [1, 0, 0, 0, 0])
                finally: self.port.close()
        finally:
            self.port = None
            self.token = None
            self.expiry = 0
            self.current = (0, ())

    def acquire(self, device):
        if device != self.device:
            raise KeyboardError('NO_KEYBOARD_MAPPING')
        with self.lock:
            if self.token and time.monotonic() < self.expiry:
                raise KeyboardError('KEYBOARD_BUSY')
            if self.token:
                self.close()
            try:
                mapping = self.mapping
                if mapping.startswith('ssh:'):
                    self.port = RemotePort(mapping[4:], self.ssh)
                else:
                    port_path = mapping
                    tty = Path(os.path.realpath(port_path)).name
                    usb = (Path('/sys/class/tty') / tty / 'device').resolve().parent.parent
                    if not re.fullmatch(r'ttyUSB[0-9]+', tty) or (usb / 'idVendor').read_text().strip() != '1a86' or (usb / 'idProduct').read_text().strip() != '7523':
                        raise KeyboardError('CH340_NOT_FOUND')
                    self.port = serial.Serial(port_path, 9600, timeout=0.6, write_timeout=0.6, exclusive=True)
                    self.port.reset_input_buffer()
                self.report(0, [], force=True)
                self.token = secrets.token_urlsafe(32)
                self.expiry = time.monotonic() + 8
                return self.token
            except (OSError, serial.SerialException, KeyboardError):
                if self.port:
                    self.port.close()
                    self.port = None
                raise KeyboardError('KEYBOARD_CONNECT_FAILED')

    def update(self, token, modifiers, keys):
        with self.lock:
            if not self.token or not hmac.compare_digest(self.token, token):
                raise KeyboardError('CONTROL_EXPIRED_OR_BUSY')
            if time.monotonic() >= self.expiry:
                self.close()
                raise KeyboardError('CONTROL_EXPIRED')
            try:
                self.report(modifiers, keys, force=isinstance(self.port, RemotePort))
                self.expiry = time.monotonic() + 8
            except (OSError, serial.SerialException, KeyboardError):
                try: self.close()
                except Exception: pass
                raise KeyboardError('KEYBOARD_DISCONNECTED')

    def mouse(self, token, x, y, buttons, wheel, relative=False):
        with self.lock:
            if not self.token or not hmac.compare_digest(self.token, token) or time.monotonic() >= self.expiry:
                raise KeyboardError('CONTROL_EXPIRED_OR_BUSY')
            try:
                if relative:
                    self.packet(5, [1, buttons, x & 255, y & 255, wheel & 255])
                else:
                    self.packet(4, [2, buttons, x & 255, x >> 8, y & 255, y >> 8, wheel & 255])
                self.expiry = time.monotonic() + 8
            except (OSError, serial.SerialException, KeyboardError):
                try: self.close()
                except (OSError, serial.SerialException, KeyboardError): pass
                raise KeyboardError('KEYBOARD_DISCONNECTED')

    def release(self, token):
        with self.lock:
            if self.token and hmac.compare_digest(self.token, token):
                try: self.close()
                except (OSError, serial.SerialException, KeyboardError): pass

    def watch(self):
        while True:
            time.sleep(0.5)
            with self.lock:
                if self.token and time.monotonic() >= self.expiry:
                    try: self.close()
                    except (OSError, serial.SerialException, KeyboardError): pass
