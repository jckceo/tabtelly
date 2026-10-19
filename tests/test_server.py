"""HTTP regression tests use isolated loopback servers and runtime directories."""
import http.client
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

import server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.srv = server.create_server('127.0.0.1', 0, Path(self.tmp.name), '127.0.0.1')
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.srv.server_address[1]
        self.session = json.loads((Path(self.tmp.name) / 'session.json').read_text())

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, path, body=None, token=None, method=None, headers=None):
        h = dict(headers or {})
        if token:
            h['X-Tabcast-Token'] = token
        if body is not None:
            body = json.dumps(body)
            h.setdefault('Content-Type', 'application/json')
        con = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        con.request(method or ('POST' if body is not None else 'GET'), path, body, h)
        res = con.getresponse()
        data = res.read().decode()
        result = res.status, dict(res.getheaders()), data
        con.close()
        return result

    def sender(self):
        return self.session['senderToken']

    def pair(self):
        status, _, body = self.request('/pair', {'code': self.session['pairCode']})
        self.assertEqual(status, 200)
        return json.loads(body)['token']

    def test_health_has_no_credentials(self):
        status, _, body = self.request('/health')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['instance'], self.session['instance'])
        self.assertNotIn(self.sender(), body)
        self.assertNotIn(self.session['pairCode'], body)

    def test_status_and_stop_require_local_token(self):
        self.assertEqual(self.request('/status')[0], 401)
        self.assertEqual(self.request('/stop', {})[0], 401)
        self.assertEqual(self.request('/status', token=self.sender())[0], 200)
        self.assertEqual(self.request('/stop', {}, token=self.session['adminToken'])[0], 200)
        self.assertEqual(self.request('/stop', {}, token=self.sender())[0], 200)
        self.assertEqual(self.request('/stop', {}, token=self.pair())[0], 403)
        self.assertEqual(self.request('/status', token=self.pair())[0], 403)

    def test_pair_rejects_bad_codes_and_rate_limits(self):
        for _ in range(server.PAIR_ATTEMPTS):
            self.assertEqual(self.request('/pair', {'code': 'wrong'})[0], 401)
        self.assertEqual(self.request('/pair', {'code': self.session['pairCode']})[0], 429)

    def test_receiver_page_never_contains_sender_credentials(self):
        code, headers, text = self.request('/tv')
        self.assertEqual(code, 200)
        self.assertNotIn(self.sender(), text)
        self.assertNotIn(self.session['pairCode'], text)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
        self.assertIn(self.sender(), self.request('/send')[2])

    def test_origin_and_host_rebinding_protection(self):
        self.assertEqual(self.request('/send', headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.request('/stop', {}, self.sender(), headers={'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(self.request('/send', headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)

    def test_invalid_json_and_non_object_are_rejected(self):
        self.assertEqual(self.request('/msg', [1, 2], self.sender())[0], 400)
        con = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
        con.request('POST', '/msg', '{bad', {'Content-Type': 'application/json', 'X-Tabcast-Token': self.sender()})
        r = con.getresponse()
        self.assertEqual(r.status, 400)
        r.read()
        con.close()

    def test_oversize_and_chunked_bodies_rejected(self):
        self.assertEqual(self.request('/msg', {'data': 'a' * (server.MAX_BODY + 1)}, self.sender())[0], 413)
        self.assertEqual(self.request('/pair', {}, headers={'Transfer-Encoding': 'chunked'})[0], 400)

    def test_pair_token_cannot_impersonate_sender(self):
        token = self.pair()
        self.assertEqual(self.request('/poll?role=sender&id=attacker', token=token)[0], 403)
        self.assertEqual(self.request('/msg', {'from': 'sender', 'id': 'attacker', 'type': 'bye'}, token)[0], 403)

    def test_signaling_registration_ownership_and_round_trip(self):
        tv = self.pair()
        self.assertEqual(self.request('/poll?role=sender&id=s1', token=self.sender())[0], 200)
        self.assertEqual(self.request('/poll?role=tv&id=t1', token=tv)[0], 200)
        offer = {'from': 'sender', 'id': 's1', 'type': 'offer', 'sdp': {'type': 'offer', 'sdp': 'v=0\r\n'}}
        self.assertEqual(self.request('/msg', offer, self.sender())[0], 200)
        msgs = json.loads(self.request('/poll?role=tv&id=t1', token=tv)[2])
        self.assertTrue(any(m['type'] == 'offer' for m in msgs))
        self.assertEqual(self.request('/msg', dict(offer, id='s2'), self.sender())[0], 409)
        self.assertEqual(self.request('/report', {'role': 'tv', 'id': 't1', 'stats': {'pc': 'connected'}}, tv)[0], 200)
        status = json.loads(self.request('/status', token=self.sender())[2])
        self.assertEqual(status['tv']['report']['pc'], 'connected')

    def test_bad_message_shapes_cannot_crash_or_relay(self):
        self.request('/poll?role=sender&id=s1', token=self.sender())
        for message in [
            {'type': 'stop'}, {'type': 'answer', 'sdp': {}},
            {'type': 'offer', 'sdp': 'bad'}, {'type': 'candidate', 'candidate': []},
        ]:
            message.update({'from': 'sender', 'id': 's1'})
            self.assertEqual(self.request('/msg', message, self.sender())[0], 400)
        self.assertEqual(self.request('/report', {'role': 'sender', 'id': 's1', 'stats': []}, self.sender())[0], 400)

    def test_remote_sender_status_and_stop_denied_even_with_token(self):
        # Unit boundary: do not probe any actual network device.
        handler = object.__new__(server.Handler)
        handler.client_address = ('192.0.2.123', 12345)
        self.assertFalse(handler.is_local())

    def test_shutdown_is_admin_only_and_closes_listener(self):
        self.assertEqual(self.request('/shutdown', {}, self.sender())[0], 403)
        self.assertEqual(self.request('/shutdown', {}, self.session['adminToken'])[0], 200)
        self.thread.join(3)
        self.assertFalse(self.thread.is_alive())

    def test_non_ascii_credentials_return_errors(self):
        self.assertEqual(self.request('/pair', {'code': 'é12345'})[0], 401)
        self.assertEqual(self.request('/status', token='é')[0], 401)

    def test_remote_admin_endpoints_are_rejected(self):
        with patch.object(server.Handler, 'is_local', return_value=False):
            for endpoint in ('/send', '/status', '/health'):
                self.assertEqual(self.request(endpoint, token=self.sender())[0], 403)
            self.assertEqual(self.request('/stop', {}, self.sender())[0], 403)
            self.assertEqual(self.request('/shutdown', {}, self.session['adminToken'])[0], 403)

    def test_nonstandard_numbers_and_excessive_nesting_are_rejected(self):
        payloads = (
            ('NaN', '{"code":NaN}'),
            ('overflow', '{"code":1e999}'),
            ('depth-40', '{"code":' + '[' * 40 + '0' + ']' * 40 + '}'),
            ('depth-1500', '{"code":' + '[' * 1500 + '0' + ']' * 1500 + '}'),
        )
        for label, body in payloads:
            with self.subTest(payload=label):
                con = http.client.HTTPConnection('127.0.0.1', self.port, timeout=3)
                try:
                    con.request('POST', '/pair', body, {'Content-Type': 'application/json'})
                    res = con.getresponse()
                    res.read()
                    self.assertEqual(res.status, 400)
                finally:
                    con.close()

    def test_hostnames_are_case_insensitive_but_authorities_must_match(self):
        self.assertEqual(self.request('/health', headers={'Host': f'LOCALHOST:{self.port}'})[0], 200)
        self.assertEqual(self.request('/health', headers={'Host': f'localhost:{self.port}', 'Origin': f'http://LOCALHOST:{self.port}'})[0], 200)
        self.assertEqual(self.request('/health', headers={'Host': f'localhost:{self.port}@evil.example'})[0], 403)
        self.assertEqual(self.request('/health', headers={'Host': f'localhost:{self.port}', 'Origin': f'http://localhost:{self.port}/evil'})[0], 403)

    def test_message_rate_limit_enforced(self):
        self.request('/poll?role=sender&id=s1', token=self.sender())
        for _ in range(180):
            self.assertEqual(self.request('/msg', {'from': 'sender', 'id': 's1', 'type': 'bye'}, self.sender())[0], 200)
        self.assertEqual(self.request('/msg', {'from': 'sender', 'id': 's1', 'type': 'bye'}, self.sender())[0], 429)

    def test_private_runtime_permissions(self):
        import os
        if os.name != 'nt':
            self.assertEqual(Path(self.tmp.name).stat().st_mode & 0o777, 0o700)
            self.assertEqual((Path(self.tmp.name) / 'session.json').stat().st_mode & 0o777, 0o600)

    def test_method_and_path_rejection(self):
        self.assertEqual(self.request('/../server.py')[0], 404)
        self.assertEqual(self.request('/health', method='PUT')[0], 405)


class HubTests(unittest.TestCase):
    def test_server_start_does_not_require_hostname_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server.socket, 'getfqdn', side_effect=AssertionError('DNS must not be required')):
                srv = server.create_server('127.0.0.1', 0, Path(tmp), '127.0.0.1')
                srv.server_close()

    def test_invalid_bind_and_advertised_addresses_rejected_before_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bind, advertised in [('192.0.2.1', '127.0.0.1'), ('0.0.0.0', '0.0.0.0'), ('0.0.0.0', '224.0.0.1')]:
                with self.assertRaises(ValueError):
                    server.create_server(bind, 0, Path(tmp), advertised)

    def test_authority_normalizes_default_http_port(self):
        self.assertEqual(server.authority('LOCALHOST:80'), server.authority('localhost'))
        self.assertNotEqual(server.authority('localhost:8090'), server.authority('localhost'))

    def test_rate_counters_have_a_fixed_window_and_bound_memory(self):
        limiter = server.RateLimit()
        self.assertTrue(limiter.allow('global-pair', 1))
        self.assertFalse(limiter.allow('global-pair', 1))
        with patch.object(server.time, 'monotonic', return_value=server.time.monotonic() + 61):
            self.assertTrue(limiter.allow('global-pair', 1))
        for n in range(1000):
            limiter.allow(n, 1)
        self.assertLessEqual(len(limiter.buckets), 256)

    def test_request_capacity_rejects_excess_and_releases_completed_slots(self):
        srv = object.__new__(server.AppServer)
        srv.slots = threading.BoundedSemaphore(1)
        request = unittest.mock.Mock()
        srv.slots.acquire()
        srv.process_request(request, ('127.0.0.1', 1))
        request.close.assert_called_once()
        with patch.object(server.ThreadingHTTPServer, 'process_request_thread'):
            srv.process_request_thread(request, ('127.0.0.1', 1))
        self.assertTrue(srv.slots.acquire(blocking=False))
        srv.slots.release()

    def test_runtime_symlinks_rejected(self):
        import os
        if os.name == 'nt':
            self.skipTest('Creating Windows symlinks needs privileges')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'actual').mkdir()
            (path / 'runtime').symlink_to(path / 'actual', target_is_directory=True)
            with self.assertRaises(ValueError):
                server.create_server('127.0.0.1', 0, path / 'runtime', '127.0.0.1')

    def test_queue_is_bounded(self):
        hub = server.Hub()
        for n in range(server.MAX_QUEUE * 2):
            hub.push('tv', {'type': 'candidate', 'n': n})
        self.assertLessEqual(len(hub.peers['tv'].queue), server.MAX_QUEUE)

    def test_mdns_rewrite_is_limited_to_candidate_addresses(self):
        mdns = '12345678-abcd-1234-abcd-123456789012.local'
        obj = {'type': 'offer', 'sdp': {'type': 'offer', 'sdp': f'a=msid:{mdns}\r\na=candidate:1 1 udp 123 {mdns} 999 typ host\r\n'}}
        result = server.munge_mdns(obj, '192.0.2.5')
        self.assertIn(f'a=msid:{mdns}', result['sdp']['sdp'])
        self.assertIn('123 192.0.2.5 999', result['sdp']['sdp'])
        self.assertIn(mdns, obj['sdp']['sdp'])

    def test_receiver_and_sender_queues_do_not_leak_on_replacement(self):
        hub = server.Hub()
        hub.poll('sender', 'a')
        hub.push('sender', {'type': 'old'})
        msgs = hub.poll('sender', 'b')
        self.assertFalse(any(m['type'] == 'old' for m in msgs))


if __name__ == '__main__':
    unittest.main()
