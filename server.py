#!/usr/bin/env python3
"""TabTelly's bounded, authenticated LAN signaling relay (Python standard library).

Video and audio travel directly between browsers via encrypted WebRTC. HTTP
signaling is intended for a trusted local network; it does not provide TLS.
"""
import collections
import ipaddress
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

VERSION = '0.1.0'
HERE = Path(__file__).resolve().parent
WEB = HERE / 'web'
POLL_TIMEOUT = 20.0
OFFLINE_AFTER = 35.0
MAX_BODY = 65536
MAX_QUEUE = 128
MAX_CONNECTIONS = 48
PAIR_ATTEMPTS = 6
ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,80}$')
MDNS_HOST = re.compile(r'(?<= )[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\.local(?= )', re.I)


def env(name, default=None):
    """Accept the prototype's TABCAST variables as compatibility aliases."""
    return os.environ.get('TABTELLY_' + name, os.environ.get('TABCAST_' + name, default))


def lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('192.0.2.1', 9))  # Route selection only: no packet sent.
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()


def authority(value):
    """Normalize an ASCII HTTP host and optional port, rejecting ambiguous forms."""
    if not re.fullmatch(r'[A-Za-z0-9.-]+(?::[0-9]{1,5})?', value):
        raise ValueError('Invalid HTTP authority')
    parsed = urlsplit('http://' + value)
    port = parsed.port if parsed.port is not None else 80
    if not 1 <= port <= 65535:
        raise ValueError('Invalid HTTP port')
    return parsed.hostname.lower(), port


class Peer:
    def __init__(self, role):
        self.role = role
        self.id = None
        self.queue = collections.deque(maxlen=MAX_QUEUE)
        self.last_seen = 0.0
        self.info = {}

    def online(self):
        return self.id is not None and time.monotonic() - self.last_seen < OFFLINE_AFTER


class Hub:
    """One sender and receiver. The condition protects every shared mutation."""
    def __init__(self):
        self.cv = threading.Condition(threading.RLock())
        self.peers = {'tv': Peer('tv'), 'sender': Peer('sender')}
        self.tv_report = {}
        self.sender_report = {}
        self.casting = False

    @staticmethod
    def other(role):
        return 'sender' if role == 'tv' else 'tv'

    def push(self, role, message):
        with self.cv:
            self.peers[role].queue.append(message)
            self.cv.notify_all()

    def poll(self, role, cid, address=None):
        with self.cv:
            peer = self.peers[role]
            if role == 'sender' and peer.id not in (None, cid) and peer.online() and self.casting:
                self.cv.wait(0.5)
                return [{'type': 'busy'}]
            fresh = peer.id != cid
            if fresh:
                peer.id = cid
                peer.queue.clear()
                peer.info = {}
                if role == 'tv':
                    self.tv_report = {}
                else:
                    self.sender_report = {}
                    self.casting = False
                self.push(self.other(role), {'type': role + '-joined', 'id': cid})
            peer.last_seen = time.monotonic()
            if address:
                peer.info['ip'] = address
            deadline = time.monotonic() + POLL_TIMEOUT
            while not fresh and peer.id == cid and not peer.queue:
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                self.cv.wait(left)
            if peer.id != cid:
                return [{'type': 'replaced'}]
            peer.last_seen = time.monotonic()
            messages = list(peer.queue)
            peer.queue.clear()
            other = self.peers[self.other(role)]
            messages.append({'type': 'presence', 'peer': self.other(role), 'online': other.online(), 'id': other.id})
            return messages

    def stop(self):
        with self.cv:
            self.casting = False
            self.push('sender', {'type': 'stop'})
            self.push('tv', {'type': 'bye'})


def munge_mdns(obj, address):
    """Replace only sender ICE host addresses, never arbitrary SDP metadata."""
    result = dict(obj)
    if isinstance(obj.get('candidate'), dict):
        result['candidate'] = dict(obj['candidate'])
        candidate = result['candidate'].get('candidate', '')
        result['candidate']['candidate'] = MDNS_HOST.sub(address, candidate)
    if isinstance(obj.get('sdp'), dict):
        result['sdp'] = dict(obj['sdp'])
        lines = result['sdp'].get('sdp', '').splitlines(keepends=True)
        result['sdp']['sdp'] = ''.join(MDNS_HOST.sub(address, line) if line.startswith('a=candidate:') else line for line in lines)
    return result


class RateLimit:
    """Bounded fixed window counters: no per-address unbounded allocation."""
    def __init__(self):
        self.lock = threading.Lock()
        self.buckets = collections.OrderedDict()

    def allow(self, key, limit, window=60):
        now = time.monotonic()
        with self.lock:
            start, count = self.buckets.pop(key, (now, 0))
            if now - start >= window:
                start, count = now, 0
            self.buckets[key] = (start, count + 1)
            while len(self.buckets) > 256:
                self.buckets.popitem(last=False)
            return count < limit


class AppServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler):
        self.slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        super().__init__(address, handler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Malformed/disconnected sockets are routine; never dump request data.
        print('TabTelly: client connection ended unexpectedly.', file=sys.stderr)


class RequestError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'TabTelly/' + VERSION
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, fmt, *args):
        pass

    def is_local(self):
        return self.client_address[0] in ('127.0.0.1', '::1')

    def response(self, body, code=200, ctype='application/json; charset=utf-8'):
        self.close_connection = True
        if not isinstance(body, bytes):
            body = json.dumps(body).encode('utf-8')
        try:
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' blob:; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
            if code == 429:
                self.send_header('Retry-After', '60')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def guard(self):
        hosts = self.headers.get_all('Host', [])
        try:
            host = authority(hosts[0]) if len(hosts) == 1 else None
        except ValueError:
            host = None
        if host not in self.server.allowed_hosts:
            raise RequestError(403, 'Unrecognized Host; use the printed localhost or LAN URL')
        origin = self.headers.get('Origin')
        if origin is not None:
            try:
                parsed = urlsplit(origin)
                valid = parsed.scheme == 'http' and not (parsed.path or parsed.query or parsed.fragment)
                valid = valid and authority(parsed.netloc) == host
            except ValueError:
                valid = False
            if not valid:
                raise RequestError(403, 'Cross-origin requests are not allowed')
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise RequestError(403, 'Cross-site requests are not allowed')

    def read_json(self):
        lengths = self.headers.get_all('Content-Length', [])
        if self.headers.get('Transfer-Encoding') or len(lengths) != 1:
            raise RequestError(400, 'Exactly one Content-Length required; chunked bodies unsupported')
        try:
            size = int(lengths[0])
        except ValueError as exc:
            raise RequestError(400, 'Invalid Content-Length') from exc
        if size < 0:
            raise RequestError(400, 'Invalid Content-Length')
        if size > MAX_BODY:
            raise RequestError(413, 'Request too large')
        if self.headers.get_content_type() != 'application/json':
            raise RequestError(415, 'Content-Type must be application/json')
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError('Incomplete body')
            def reject_constant(_value):
                raise ValueError('Non-finite JSON number')
            obj = json.loads(raw, parse_constant=reject_constant)
        except (ValueError, UnicodeDecodeError, RecursionError) as exc:
            raise RequestError(400, 'Invalid JSON') from exc
        if not isinstance(obj, dict):
            raise RequestError(400, 'JSON body must be an object')
        return obj

    def authorize(self, role=None, local=False):
        if local and not self.is_local():
            raise RequestError(403, 'This endpoint is only available on localhost')
        token = self.headers.get('X-Tabcast-Token', '')
        if not token or not token.isascii():
            raise RequestError(401, 'Pair the TV or reload the local sender page')
        roles = [('sender', self.server.session['senderToken']), ('admin', self.server.session['adminToken']), ('tv', self.server.receiver_token)]
        actual = next((name for name, secret in roles if secrets.compare_digest(token, secret)), None)
        if actual is None:
            raise RequestError(401, 'Session expired; pair again or reload the sender')
        if actual in ('sender', 'admin') and not self.is_local():
            raise RequestError(403, 'Sender credentials are local only')
        if role and actual not in role:
            raise RequestError(403, 'Credential is not valid for this role')
        return actual

    def page(self, name, sender=False):
        if sender and not self.is_local():
            raise RequestError(403, 'Open the sender using localhost on the computer')
        config = {'receiverUrl': self.server.receiver_url, 'version': VERSION}
        if sender:
            config.update(senderToken=self.server.session['senderToken'], pairCode=self.server.session['pairCode'])
        body = (WEB / name).read_text(encoding='utf-8')
        config_script = '<script>window.TABCAST=' + json.dumps(config).replace('<', '\\u003c') + ';</script>\n'
        body = body.replace('<script>', config_script + '<script>', 1)
        self.response(body.encode('utf-8'), ctype='text/html; charset=utf-8')

    def do_GET(self):
        self.dispatch('GET')

    def do_POST(self):
        self.dispatch('POST')

    def do_HEAD(self):
        self.dispatch('HEAD')

    def do_OPTIONS(self):
        self.response({'error': 'Cross-origin access is unsupported'}, 405)

    def do_PUT(self):
        self.response({'error': 'Method not allowed'}, 405)

    do_DELETE = do_PATCH = do_PUT

    def dispatch(self, method):
        try:
            self.guard()
            url = urlsplit(self.path)
            path = url.path
            q = {k: v[0] for k, v in parse_qs(url.query, max_num_fields=8).items()}
            if method in ('GET', 'HEAD'):
                if path == '/health':
                    if not self.is_local():
                        raise RequestError(403, 'Health identity is local only')
                    return self.response({'app': 'tabcast', 'version': VERSION, 'instance': self.server.session['instance'], 'pid': os.getpid()})
                if path == '/':
                    return self.page('sender.html' if self.is_local() else 'receiver.html', self.is_local())
                if path in ('/send', '/sender'):
                    return self.page('sender.html', True)
                if path in ('/tv', '/receiver'):
                    return self.page('receiver.html')
                if path == '/latency':
                    if not self.is_local():
                        raise RequestError(403, 'Latency test is local only')
                    return self.page('latency.html')
                if path == '/time':
                    self.authorize(('sender', 'tv'))
                    return self.response({'t': time.time() * 1000})
                if path == '/status':
                    self.authorize(('sender', 'admin'), local=True)
                    return self.response(self.status())
                if path == '/poll' and method == 'GET':
                    role, cid = q.get('role'), q.get('id')
                    self.check_id(role, cid)
                    self.authorize((role,))
                    return self.response(self.server.hub.poll(role, cid, self.client_address[0]))
            elif method == 'POST':
                if path == '/pair':
                    obj = self.read_json()
                    allowed_ip = self.server.limits.allow(('pair', self.client_address[0]), PAIR_ATTEMPTS)
                    allowed_global = self.server.limits.allow('pair-all', 30)
                    if not allowed_ip or not allowed_global:
                        raise RequestError(429, 'Too many pairing attempts; wait 60 seconds')
                    code = obj.get('code')
                    if not isinstance(code, str) or not code.isascii() or not secrets.compare_digest(code, self.server.session['pairCode']):
                        raise RequestError(401, 'Incorrect pairing code')
                    return self.response({'token': self.server.receiver_token})
                if path == '/shutdown':
                    self.authorize(('admin',), local=True)
                    self.read_json()
                    self.server.hub.stop()
                    self.response({'ok': True})
                    timer = threading.Timer(0.3, self.server.shutdown)
                    timer.daemon = True
                    timer.start()
                    return
                if path == '/stop':
                    self.authorize(('sender', 'admin'), local=True)
                    self.read_json()
                    self.server.hub.stop()
                    return self.response({'ok': True})
                if path in ('/msg', '/report'):
                    role = self.authorize(('sender', 'tv'))
                    obj = self.read_json()
                    if not self.server.limits.allow(('message', role), 180, 10):
                        raise RequestError(429, 'Signaling rate exceeded; retry shortly')
                    self.check_id(obj.get('from' if path == '/msg' else 'role'), obj.get('id'))
                    if obj.get('from' if path == '/msg' else 'role') != role:
                        raise RequestError(403, 'Role does not match credential')
                    hub = self.server.hub
                    with hub.cv:
                        if hub.peers[role].id != obj['id']:
                            raise RequestError(409, 'Client replaced or not registered; poll first')
                        hub.peers[role].last_seen = time.monotonic()
                        if path == '/msg':
                            self.message(role, obj)
                        else:
                            self.report(role, obj)
                    return self.response({'ok': True})
            raise RequestError(404, 'Not found')
        except RequestError as exc:
            self.response({'error': exc.message}, exc.code)
        except (ValueError, UnicodeError):
            self.response({'error': 'Malformed request'}, 400)
        except (TimeoutError, ConnectionError):
            self.close_connection = True

    @staticmethod
    def check_id(role, cid):
        if role not in ('sender', 'tv') or not isinstance(cid, str) or not ID_PATTERN.fullmatch(cid):
            raise RequestError(400, 'Valid role and client id required')

    def message(self, role, obj):
        kind = obj.get('type')
        allowed = {'sender': ('offer', 'candidate', 'bye'), 'tv': ('answer', 'candidate', 'tv-ready')}
        if kind not in allowed[role]:
            raise RequestError(400, 'Message type is not allowed for role')
        message = {'type': kind}
        if kind in ('offer', 'answer'):
            sdp = obj.get('sdp')
            if not isinstance(sdp, dict) or sdp.get('type') != kind or not isinstance(sdp.get('sdp'), str):
                raise RequestError(400, 'Invalid session description')
            message['sdp'] = {'type': kind, 'sdp': sdp['sdp']}
        if kind == 'candidate':
            candidate = obj.get('candidate')
            if not isinstance(candidate, dict) or not isinstance(candidate.get('candidate'), str):
                raise RequestError(400, 'Invalid ICE candidate')
            for field in ('sdpMid', 'usernameFragment'):
                if candidate.get(field) is not None and not isinstance(candidate[field], str):
                    raise RequestError(400, 'Invalid ICE metadata')
            if candidate.get('sdpMLineIndex') is not None and type(candidate['sdpMLineIndex']) is not int:
                raise RequestError(400, 'Invalid ICE index')
            message['candidate'] = candidate
        if role == 'sender':
            message = munge_mdns(message, self.server.lan_address)
            if kind in ('offer', 'bye'):
                self.server.hub.casting = kind == 'offer'
        self.server.hub.push(self.server.hub.other(role), message)

    def report(self, role, obj):
        for field in ('stats', 'caps'):
            if field in obj and not isinstance(obj[field], dict):
                raise RequestError(400, 'Invalid report: ' + field + ' must be an object')
        hub = self.server.hub
        if 'caps' in obj:
            hub.peers[role].info['caps'] = obj['caps']
        if 'stats' in obj:
            report = dict(obj['stats'], at=time.strftime('%H:%M:%S'))
            if role == 'tv':
                hub.tv_report = report
            else:
                hub.sender_report = report
        # Events and tab titles are deliberately not persisted or logged.

    def status(self):
        hub = self.server.hub
        with hub.cv:
            status = {'receiverUrl': self.server.receiver_url, 'senderUrl': self.server.sender_url, 'pairCode': self.server.session['pairCode'], 'version': VERSION}
            for role in ('tv', 'sender'):
                peer = hub.peers[role]
                status[role] = {'online': peer.online(), 'id': peer.id, 'ip': peer.info.get('ip'), 'caps': peer.info.get('caps'), 'secondsSinceSeen': round(time.monotonic() - peer.last_seen, 1) if peer.id else None, 'report': hub.tv_report if role == 'tv' else hub.sender_report}
            return status


def create_server(bind, port, runtime_dir, lan_address):
    """Create an isolated server and atomically publish its private CLI identity."""
    advertised = ipaddress.IPv4Address(lan_address)
    if advertised.is_unspecified or advertised.is_multicast or str(advertised) == '255.255.255.255':
        raise ValueError('Advertised LAN address must be a unicast IPv4 address')
    if bind not in ('0.0.0.0', '127.0.0.1'):
        raise ValueError('Bind must be 0.0.0.0 (LAN) or 127.0.0.1 (local testing)')
    srv = AppServer((bind, port), Handler)
    try:
        actual_port = srv.server_address[1]
        srv.lan_address = lan_address
        srv.receiver_url = f'http://{lan_address}:{actual_port}/'
        srv.sender_url = f'http://localhost:{actual_port}/send'
        srv.allowed_hosts = {authority(f'{host}:{actual_port}') for host in ('localhost', '127.0.0.1', lan_address, bind) if host != '0.0.0.0'}
        srv.hub = Hub()
        srv.limits = RateLimit()
        srv.receiver_token = secrets.token_urlsafe(32)
        srv.session = {'adminToken': secrets.token_urlsafe(32), 'senderToken': secrets.token_urlsafe(32), 'pairCode': f'{secrets.randbelow(1000000):06d}', 'instance': secrets.token_hex(16), 'pid': os.getpid(), 'port': actual_port}
        runtime = Path(runtime_dir)
        runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
        if runtime.is_symlink() or (runtime / 'session.json').is_symlink():
            raise ValueError('Runtime directory and session must not be symlinks')
        runtime.chmod(0o700)
        session_file = runtime / 'session.json'
        # Exclusive randomized temporary file prevents following existing symlinks.
        temporary = runtime / ('.session-' + secrets.token_hex(8))
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(srv.session, stream)
        os.replace(temporary, session_file)
        return srv
    except BaseException:
        srv.server_close()
        raise


def main():
    if sys.version_info < (3, 10):
        sys.exit('TabTelly requires Python 3.10 or newer.')
    try:
        port = int(env('PORT', '8090'))
        if not 1 <= port <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        runtime = Path(env('RUNTIME_DIR', str(HERE / '.run' / str(port))))
        srv = create_server(env('BIND', '0.0.0.0'), port, runtime, env('LAN_IP') or lan_ip())
    except (ValueError, OSError) as exc:
        sys.exit(f'Cannot start TabTelly: {exc}')
    print(f'TabTelly {VERSION}\n  Sender: {srv.sender_url}\n  TV browser: {srv.receiver_url}\n  Pairing code: {srv.session["pairCode"]}\nUse a trusted LAN. HTTP signaling is not encrypted. Ctrl+C stops the server.', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.hub.stop()
        srv.server_close()


if __name__ == '__main__':
    main()
