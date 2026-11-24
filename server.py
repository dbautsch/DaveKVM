#!/usr/bin/env python3
# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
import base64, fcntl, glob, hmac, json, os, re, secrets, select, signal, socket, socketserver, struct, subprocess, threading, time, urllib.parse
import serial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from messages import message, normalize_language

# Configuration is supplied by the operator. No credentials or device mappings
# are embedded in the project; only loopback is bound by default.
def configured_integer(name, default, error_code):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        raise ValueError(message(error_code)) from None


BASE = Path(__file__).resolve().parent
PASSWORD = None
USERNAME = os.environ.get('DAVEKVM_USERNAME', 'davekvm')
HOST = os.environ.get('DAVEKVM_LISTEN', '127.0.0.1')
PORT = configured_integer('DAVEKVM_PORT', '8080', 'INVALID_PORT')
if not 1 <= PORT <= 65535:
    raise ValueError(message('INVALID_PORT'))
CAPTURE_SIZE = os.environ.get('DAVEKVM_CAPTURE_SIZE', '1280x720')
if not re.fullmatch(r'[1-9][0-9]{2,3}x[1-9][0-9]{2,3}', CAPTURE_SIZE):
    raise ValueError(message('INVALID_CAPTURE_DIMENSIONS'))
LOCAL_FPS = configured_integer('DAVEKVM_LOCAL_FPS', '60', 'INVALID_CAPTURE_RATE')
REMOTE_FPS = configured_integer('DAVEKVM_REMOTE_FPS', '30', 'INVALID_CAPTURE_RATE')
if not 1 <= LOCAL_FPS <= 120 or not 1 <= REMOTE_FPS <= 120:
    raise ValueError(message('INVALID_CAPTURE_RATE'))
ORIGIN = os.environ.get('DAVEKVM_ORIGIN', f'http://127.0.0.1:{PORT}').rstrip('/')
REMOTE_ALIAS = os.environ.get('DAVEKVM_REMOTE_SSH_ALIAS', '')
if REMOTE_ALIAS and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', REMOTE_ALIAS):
    raise ValueError(message('INVALID_SSH_ALIAS'))
SSH = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
       '-o', 'ConnectTimeout=3', '-o', 'ServerAliveInterval=10', '-o',
       'ServerAliveCountMax=3', REMOTE_ALIAS] if REMOTE_ALIAS else None
try:
    SERIAL_MAP = json.loads(os.environ.get('DAVEKVM_SERIAL_MAP', '{}'))
except (ValueError, TypeError):
    raise ValueError(message('INVALID_SERIAL_MAP')) from None
if not isinstance(SERIAL_MAP, dict):
    raise ValueError(message('INVALID_SERIAL_MAP'))
for device, target in SERIAL_MAP.items():
    if not isinstance(device, str) or not re.fullmatch(r'(?:remote-)?video[0-9]+', device):
        raise ValueError(message('INVALID_DEVICE_MAPPING'))
    if not isinstance(target, str):
        raise ValueError(message('INVALID_KEYBOARD_TARGET'))
    if device.startswith('remote-'):
        if not SSH or not re.fullmatch(r'ssh:video[0-9]+', target):
            raise ValueError(message('REMOTE_MAPPING_INVALID'))
    elif not (target.startswith('/dev/serial/by-id/') or target.startswith('/dev/serial/by-path/')):
        raise ValueError(message('SERIAL_PATH_INVALID'))


def validate_origin():
    origin = urllib.parse.urlsplit(ORIGIN)
    if origin.scheme not in ('http', 'https') or not origin.hostname or origin.username or origin.password or origin.path or origin.query or origin.fragment or not 1 <= PORT <= 65535:
        raise ValueError(message('INVALID_ORIGIN'))


def load_password():
    path = Path(os.environ.get('DAVEKVM_PASSWORD_FILE', str(Path.home() / '.config/davekvm/password')))
    try:
        secret = path.read_text(encoding='utf-8').strip()
    except (OSError, UnicodeError):
        raise ValueError(message('PASSWORD_FILE_ERROR')) from None
    if len(secret) < 16 or ':' in USERNAME or not USERNAME:
        raise ValueError(message('INVALID_CREDENTIALS_CONFIG'))
    return secret


def devices():
    result = []
    for path in sorted(glob.glob('/dev/video[0-9]*')):
        name = os.path.basename(path)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            try:
                cap = bytearray(104)
                fcntl.ioctl(fd, 0x80685600, cap, True)
            finally:
                os.close(fd)
            capabilities, device_caps = struct.unpack_from('II', cap, 84)
            effective = device_caps if capabilities & 0x80000000 else capabilities
            if not effective & 1: continue
            label = (Path('/sys/class/video4linux') / name / 'name').read_text().strip()
            result.append({'id': name, 'name': label})
        except (OSError, ValueError):
            continue
    return result

def all_devices():
    local = [{'id': d['id'], 'name': d['name'], 'control': d['id'] in SERIAL_MAP} for d in devices()]
    if not SSH:
        return local
    try:
        response = subprocess.run(SSH + ['list'], capture_output=True, timeout=4, check=True)
        remote = json.loads(response.stdout)
        if not isinstance(remote, list):
            return local
        for d in remote:
            if isinstance(d, dict) and isinstance(d.get('id'), str) and re.fullmatch(r'video[0-9]+', d['id']) and isinstance(d.get('name'), str):
                local.append({'id': 'remote-' + d['id'], 'name': 'Remote · ' + d['name'], 'control': 'remote-' + d['id'] in SERIAL_MAP})
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return local

def first_valid_frame(stream):
    """Discard incomplete initial camera frames before starting an HTTP stream."""
    for _ in range(30):
        boundary = stream.readline(128)
        if boundary != b'--frame\r\n':
            raise ValueError(message('INVALID_MULTIPART_BOUNDARY'))
        headers = []
        length = None
        while True:
            line = stream.readline(1024)
            if not line or len(headers) >= 16:
                raise ValueError(message('INVALID_MULTIPART_HEADERS'))
            headers.append(line)
            if line.lower().startswith(b'content-length:'):
                length = int(line.split(b':', 1)[1].strip())
            if line == b'\r\n':
                break
        if length is None or not 0 < length <= 8 * 1024 * 1024:
            raise ValueError(message('INVALID_FRAME_LENGTH'))
        chunks = []
        remaining = length
        while remaining:
            chunk = stream.read(remaining)
            if not chunk:
                raise EOFError(message('INCOMPLETE_FRAME'))
            chunks.append(chunk)
            remaining -= len(chunk)
        frame = b''.join(chunks)
        if stream.read(2) != b'\r\n':
            raise ValueError(message('INVALID_FRAME_TERMINATOR'))
        if frame.startswith(b'\xff\xd8') and frame.endswith(b'\xff\xd9'):
            return boundary + b''.join(headers) + frame + b'\r\n'
    raise ValueError(message('NO_VALID_FRAME'))

class Capture:
    """One reader per device; slow clients skip frames instead of building a queue."""
    def __init__(self, name):
        self.name = name
        self.condition = threading.Condition()
        self.clients = 0
        self.idle_since = time.monotonic()
        self.thread = None
        self.proc = None
        self.frame = None
        self.sequence = 0
        self.error = None

    def acquire(self):
        with self.condition:
            self.clients += 1
            if self.thread is None:
                self.frame = None
                self.error = None
                self.thread = threading.Thread(target=self.run, daemon=True)
                self.thread.start()

    def release(self):
        with self.condition:
            self.clients -= 1
            if self.clients == 0:
                self.idle_since = time.monotonic()

    def get(self, after, timeout=12):
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                if self.frame is not None and self.sequence > after:
                    return self.sequence, self.frame
                if self.error:
                    raise RuntimeError(self.error)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(message('FRAME_TIMEOUT'))
                self.condition.wait(remaining)

    def watch(self, proc, remote):
        while proc.poll() is None:
            time.sleep(1)
            if remote:
                try:
                    proc.stdin.write(b'\0')
                    proc.stdin.flush()
                except (OSError, ValueError):
                    return
            with self.condition:
                idle = self.clients == 0 and time.monotonic() - self.idle_since >= 5
                if idle:
                    # Keep acquisition serialized with the idle transition.
                    self.error = message('CAPTURE_STOPPED')
                    self.frame = None
                    self.condition.notify_all()
                    proc.terminate()
                    return

    def run(self):
        remote = self.name.startswith('remote-')
        device = self.name[7:] if remote else '/dev/' + self.name
        command = SSH + ['stream ' + device] if remote else ['/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'v4l2', '-input_format', 'mjpeg', '-video_size', CAPTURE_SIZE, '-framerate', str(LOCAL_FPS), '-i', device, '-an', '-c:v', 'copy', '-f', 'mpjpeg', '-boundary_tag', 'frame', 'pipe:1']
        proc = None
        try:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE if remote else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            with self.condition:
                self.proc = proc
            threading.Thread(target=self.watch, args=(proc, remote), daemon=True).start()
            ready_after = time.monotonic() + 1.5  # Capture devices can emit initial black frames while HDMI locks.
            while True:
                frame = first_valid_frame(proc.stdout)
                if time.monotonic() < ready_after:
                    continue
                with self.condition:
                    self.sequence += 1
                    self.frame = frame
                    self.condition.notify_all()
        except (OSError, EOFError, ValueError) as exc:
            with self.condition:
                self.error = str(exc) or message('STREAM_UNAVAILABLE')
                self.frame = None
                self.condition.notify_all()
        finally:
            if proc:
                if proc.stdin:
                    try: proc.stdin.close()
                    except OSError: pass
                if proc.poll() is None:
                    proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                proc.stdout.close()
            with self.condition:
                self.proc = None
                self.thread = None
                self.condition.notify_all()

captures = {}
captures_lock = threading.Lock()
def get_capture(name):
    with captures_lock:
        if name not in captures:
            captures[name] = Capture(name)
        return captures[name]

# Encoding is isolated from the capture reader and limited so web viewers
# cannot start an unbounded number of CPU-intensive encoders.
web_encoder_slots = threading.BoundedSemaphore(2)

def web_encoder_options(query):
    """Validate bounded per-viewer encoder settings without changing capture."""
    values = urllib.parse.parse_qs(query, keep_blank_values=True, strict_parsing=True) if query else {}
    defaults = {'encoder': 'x264', 'preset': 'ultrafast', 'crf': '12', 'bitrate': '8000',
                'qsv_preset': 'veryfast', 'qsv_profile': 'baseline', 'qsv_mode': 'cbr',
                'qsv_quality': '18', 'qsv_gop': '30'}
    if set(values) - set(defaults) or any(len(value) != 1 for value in values.values()):
        raise ValueError(message('INVALID_ENCODER_SETTINGS'))
    options = {name: values.get(name, [value])[0] for name, value in defaults.items()}
    if options['encoder'] not in ('x264', 'h264_qsv', 'hevc_qsv'):
        raise ValueError(message('INVALID_ENCODER'))
    if options['preset'] not in ('ultrafast', 'superfast', 'veryfast'):
        raise ValueError(message('INVALID_PRESET'))
    if not re.fullmatch(r'(?:[1-9]|[12][0-9]|30)', options['crf']):
        raise ValueError(message('INVALID_CRF'))
    if not re.fullmatch(r'[0-9]{4,5}', options['bitrate']) or not 1000 <= int(options['bitrate']) <= 30000:
        raise ValueError(message('INVALID_BITRATE'))
    if options['qsv_preset'] not in ('veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'):
        raise ValueError(message('INVALID_QSV_PRESET'))
    if options['qsv_profile'] not in ('baseline', 'main', 'high'):
        raise ValueError(message('INVALID_QSV_PROFILE'))
    if options['qsv_mode'] not in ('cbr', 'vbr', 'icq', 'cqp'):
        raise ValueError(message('INVALID_QSV_MODE'))
    if not re.fullmatch(r'(?:[1-9]|[1-4][0-9]|5[01])', options['qsv_quality']):
        raise ValueError(message('INVALID_QSV_QUALITY'))
    if not re.fullmatch(r'[0-9]{1,3}', options['qsv_gop']) or not 15 <= int(options['qsv_gop']) <= 300:
        raise ValueError(message('INVALID_KEYFRAME_INTERVAL'))
    if options['qsv_mode'] == 'vbr' and int(options['bitrate']) == 30000:
        raise ValueError(message('INVALID_VBR_BITRATE'))
    if options['encoder'] == 'hevc_qsv' and options['qsv_profile'] not in ('baseline', 'main'):
        raise ValueError(message('INVALID_HEVC_PROFILE'))
    return options


def web_encoder_command(name, options=None):
    """Encode individually flushed MP4 fragments without B frames."""
    if options is None:
        options = web_encoder_options('')
    # Remote and local capture pipelines may have different input rates.
    rate = str(REMOTE_FPS if name.startswith('remote-') else LOCAL_FPS)
    encoder = options['encoder']
    command = ['/usr/bin/nice', '-n', '10', '/usr/bin/ffmpeg', '-hide_banner', '-loglevel', 'error']
    if encoder != 'x264':
        command += ['-init_hw_device', 'vaapi=va:/dev/dri/card0', '-init_hw_device', 'qsv=qs@va']
    command += ['-probesize', '32', '-analyzeduration', '0', '-r', rate,
                '-f', 'mpjpeg', '-i', 'pipe:0', '-an', '-threads', '2']
    if encoder == 'x264':
        command += ['-c:v', 'libx264', '-preset', options['preset'], '-tune', 'zerolatency',
                    '-profile:v', 'baseline', '-pix_fmt', 'yuv420p', '-crf', options['crf']]
    else:
        command += ['-vf', 'format=nv12', '-c:v', encoder, '-preset', options['qsv_preset'],
                    '-async_depth', '1']
        command += (['-profile:v', options['qsv_profile']] if encoder == 'h264_qsv' else
                    ['-profile:v', 'main', '-tier', 'main', '-gpb', '0', '-tag:v', 'hvc1'])
        mode = options['qsv_mode']
        if mode in ('icq', 'cqp'):
            command += ['-global_quality', options['qsv_quality']]
            if mode == 'cqp':
                command += ['-qscale:v', '1']
        else:
            bitrate = int(options['bitrate'])
            maximum = bitrate if mode == 'cbr' else min(30000, bitrate * 2)
            if mode == 'vbr' and maximum == bitrate:
                raise ValueError(message('INVALID_VBR_BITRATE'))
            command += ['-b:v', str(bitrate) + 'k', '-maxrate', str(maximum) + 'k',
                        '-bufsize', str(maximum // 8) + 'k']
    if encoder == 'x264':
        command += ['-maxrate', options['bitrate'] + 'k',
                    '-bufsize', str(int(options['bitrate']) // 8) + 'k']
    command += ['-bf', '0', '-g', options['qsv_gop'] if encoder != 'x264' else '30', '-movflags',
                'empty_moov+default_base_moof+frag_every_frame', '-flush_packets',
                '1', '-f', 'mp4', 'pipe:1']
    return command

def feed_web_encoder(capture, proc, stopped):
    """Feed each encoder from the latest shared frame, never from a queue."""
    sequence = -1
    last_frame = time.monotonic()
    try:
        while not stopped.is_set() and proc.poll() is None:
            try:
                sequence, frame = capture.get(sequence, timeout=1)
            except TimeoutError:
                if time.monotonic() - last_frame >= 12:
                    return
                continue
            last_frame = time.monotonic()
            remaining = memoryview(frame)
            while remaining and not stopped.is_set():
                written = os.write(proc.stdin.fileno(), remaining)
                if not written:
                    return
                remaining = remaining[written:]
    except (OSError, RuntimeError, ValueError):
        pass
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass

from keyboard import Keyboard, KeyboardError

keyboards = {name: Keyboard(name, mapping, SSH) for name, mapping in SERIAL_MAP.items()}

def keyboard_for_token(token):
    for item in keyboards.values():
        if item.token and hmac.compare_digest(item.token, token): return item
    raise KeyboardError('CONTROL_EXPIRED_OR_BUSY')

class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def request_language(self):
        try:
            cookie = SimpleCookie()
            cookie.load(self.headers.get('Cookie', ''))
            if 'davekvm_language' in cookie:
                return normalize_language(cookie['davekvm_language'].value)
        except (CookieError, ValueError, TypeError):
            pass
        return normalize_language(self.headers.get('Accept-Language', '').split(',', 1)[0].split(';', 1)[0])

    def reply_error(self, status, code):
        payload = json.dumps({'error_code': code, 'error': message(code, self.request_language())},
                             ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def authenticate(self):
        try:
            scheme, encoded = self.headers.get('Authorization', '').split(' ', 1)
            decoded = base64.b64decode(encoded, validate=True).decode('utf-8')
            username, password = decoded.split(':', 1)
            ok = (scheme.lower() == 'basic' and hmac.compare_digest(username.encode('utf-8'), USERNAME.encode('utf-8'))
                  and PASSWORD is not None and hmac.compare_digest(password.encode('utf-8'), PASSWORD.encode('utf-8')))
        except (ValueError, UnicodeError): ok = False
        if not ok:
            self.send_response(401); self.send_header('WWW-Authenticate', 'Basic realm="DaveKVM", charset="UTF-8"'); self.send_header('Content-Length', '0'); self.end_headers()
        return ok

    def do_GET(self):
        if not self.authenticate(): return
        if self.headers.get('Host', '').lower() != urllib.parse.urlsplit(ORIGIN).netloc.lower():
            self.reply_error(403, 'FORBIDDEN'); return
        url = urllib.parse.urlsplit(self.path)
        path = url.path
        if path == '/grabber':
            self.send_response(302); self.send_header('Location', '/grabber/'); self.send_header('Content-Length', '0'); self.end_headers(); return
        if path == '/grabber/':
            data = (BASE / 'index.html').read_bytes(); self.reply(data, 'text/html; charset=utf-8'); return
        if path == '/grabber/api/devices':
            self.reply(json.dumps(all_devices()).encode(), 'application/json'); return
        if path == '/grabber/api/ping':
            self.reply(b'{}', 'application/json'); return
        if path == '/grabber/api/encoders':
            available = (os.access('/dev/dri/card0', os.R_OK | os.W_OK) and
                         Path('/usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so').is_file() and
                         Path('/usr/lib/x86_64-linux-gnu/libmfxhw64.so.1').is_file())
            self.reply(json.dumps({'qsv': available}).encode(), 'application/json'); return
        match = re.fullmatch(r'/grabber/(web-h264|web-video)/((?:remote-)?video[0-9]+)', path)
        if match:
            operation, name = match.groups()
            if name in {d['id'] for d in all_devices()}:
                try: options = web_encoder_options(url.query)
                except ValueError: self.reply_error(400, 'INVALID_ENCODER_SETTINGS'); return
                if operation == 'web-h264' and options['encoder'] == 'hevc_qsv':
                    self.reply_error(400, 'HEVC_REQUIRES_WEB_VIDEO'); return
                self.web_h264(name, options); return
        match = re.fullmatch(r'/grabber/(stream|snapshot)/((?:remote-)?video[0-9]+)(?:\.jpg)?', path)
        if match:
            operation, name = match.groups()
            if name in {d['id'] for d in all_devices()}:
                self.capture(name, operation == 'snapshot'); return
        self.reply_error(404, 'NOT_FOUND')
    def do_POST(self):
        if not self.authenticate(): return
        if self.headers.get('Host', '').lower() != urllib.parse.urlsplit(ORIGIN).netloc.lower() or self.headers.get('Origin', '') != ORIGIN:
            self.reply_error(403, 'FORBIDDEN'); return
        if self.headers.get('Sec-Fetch-Site', 'same-origin') != 'same-origin' or self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            self.reply_error(403, 'FORBIDDEN'); return
        self.connection.settimeout(5)
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if length < 0 or length > 2048: raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict): raise ValueError()
            action = urllib.parse.urlsplit(self.path).path
            if action == '/grabber/api/keyboard/acquire':
                device = data.get('device')
                if device not in keyboards: raise KeyboardError('NO_KEYBOARD_MAPPING')
                token = keyboards[device].acquire(device)
                result = {'token': token}
            elif action in ('/grabber/api/keyboard/state', '/grabber/api/keyboard/release', '/grabber/api/keyboard/mouse', '/grabber/api/keyboard/mouse-relative'):
                token = data.get('token')
                if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token): raise ValueError()
                keyboard = keyboard_for_token(token)
                if action.endswith('/release'):
                    keyboard.release(token)
                elif action.endswith('/mouse-relative'):
                    x, y, buttons, wheel = (data.get(k) for k in ('x', 'y', 'buttons', 'wheel'))
                    if any(type(v) is not int for v in (x, y, buttons, wheel)) or not (-127 <= x <= 127 and -127 <= y <= 127 and 0 <= buttons <= 7 and -127 <= wheel <= 127): raise ValueError()
                    keyboard.mouse(token, x, y, buttons, wheel, relative=True)
                elif action.endswith('/mouse'):
                    x, y, buttons, wheel = (data.get(k) for k in ('x', 'y', 'buttons', 'wheel'))
                    if any(type(v) is not int for v in (x, y, buttons, wheel)) or not (0 <= x <= 4095 and 0 <= y <= 4095 and 0 <= buttons <= 7 and -127 <= wheel <= 127): raise ValueError()
                    keyboard.mouse(token, x, y, buttons, wheel)
                else:
                    modifiers, keys = data.get('modifiers'), data.get('keys')
                    if type(modifiers) is not int or not 0 <= modifiers <= 255 or not isinstance(keys, list) or len(keys) > 6 or any(type(k) is not int or not 4 <= k <= 221 for k in keys) or len(set(keys)) != len(keys):
                        raise ValueError()
                    keyboard.update(token, modifiers, keys)
                result = {'ok': True}
            else:
                self.reply_error(404, 'NOT_FOUND'); return
            self.reply(json.dumps(result).encode(), 'application/json')
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self.reply_error(400, 'INVALID_REQUEST')
        except KeyboardError as exc:
            self.reply_error(409, exc.code)

    def reply(self, data, kind):
        self.send_response(200); self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(data))); self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff'); self.end_headers(); self.wfile.write(data)
    def web_h264(self, name, options=None):
        if not web_encoder_slots.acquire(blocking=False):
            self.reply_error(503, 'ENCODER_BUSY')
            return

        stopped = threading.Event()
        capture = None
        acquired = False
        proc = None
        feeder = None
        feeder_started = False
        started = False
        try:
            capture = get_capture(name)
            capture.acquire()
            acquired = True
            proc = subprocess.Popen(web_encoder_command(name, options), stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    bufsize=0)
            feeder = threading.Thread(target=feed_web_encoder,
                                      args=(capture, proc, stopped), daemon=True)
            feeder.start()
            feeder_started = True
            if not select.select([proc.stdout], [], [], 15)[0]:
                raise RuntimeError(message('ENCODER_TIMEOUT'))
            first = os.read(proc.stdout.fileno(), 16384)
            if not first:
                raise RuntimeError(message('ENCODER_START_FAILED'))
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            self.connection.settimeout(3)
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            started = True
            self.wfile.write(first)
            while True:
                chunk = os.read(proc.stdout.fileno(), 16384)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (OSError, RuntimeError):
            if not started:
                try: self.reply_error(503, 'ENCODER_UNAVAILABLE')
                except OSError: pass
        finally:
            stopped.set()
            try:
                if proc:
                    try:
                        if proc.poll() is None:
                            try: proc.terminate()
                            except ProcessLookupError: pass
                        try: proc.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            try: proc.kill()
                            except ProcessLookupError: pass
                            proc.wait()
                        if feeder_started:
                            feeder.join(timeout=2)
                    finally:
                        proc.stdout.close()
            finally:
                try:
                    if acquired:
                        capture.release()
                finally:
                    web_encoder_slots.release()

    def capture(self, name, snapshot):
        capture = get_capture(name)
        capture.acquire()
        started = False
        try:
            sequence, frame = capture.get(-1)
            if snapshot:
                image = frame.split(b'\r\n\r\n', 1)[1][:-2]
                self.reply(image, 'image/jpeg')
                return
            self.connection.settimeout(10)
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            started = True
            self.wfile.write(frame)
            while True:
                sequence, frame = capture.get(sequence)
                self.wfile.write(frame)
        except (BrokenPipeError, ConnectionResetError, TimeoutError, RuntimeError, OSError):
            if not started:
                try: self.reply_error(503, 'CAPTURE_UNAVAILABLE')
                except OSError: pass
        finally:
            capture.release()

def shutdown_keyboard(signum, frame):
    for keyboard in keyboards.values():
        if keyboard.token: keyboard.release(keyboard.token)
    raise SystemExit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, shutdown_keyboard)
    if HOST not in ('127.0.0.1', 'localhost') and os.environ.get('DAVEKVM_ALLOW_INSECURE_REMOTE') != '1':
        raise SystemExit(message('INSECURE_BIND'))
    validate_origin()
    PASSWORD = load_password()
    Server((HOST, PORT), Handler).serve_forever()
