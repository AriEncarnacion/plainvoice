import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlencode, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import browser_key_bridge as bridge

class TestKeyBridge(unittest.TestCase):
    def test_origin_host_format_checks_and_no_key_echo(self):
        stdout = io.StringIO()
        responses = []
        secret = 'sk-or-' + 'x' * 60
        class Server:
            def __init__(self, address, handler):
                self.server_address = (address[0], address[1] or 8877)
                self.handler = handler
                self.timeout = None
                self.closed = False
            def handle_request(self):
                url = stdout.getvalue().strip().split('=', 1)[1]
                endpoint = urlsplit(url).path
                cases = [
                    ({'Host': 'attacker.invalid', 'Origin': 'http://127.0.0.1:8877'}, {'key': secret}, 403),
                    ({'Host': '127.0.0.1:8877', 'Origin': 'https://evil.invalid'}, {'key': secret}, 403),
                    ({'Host': '127.0.0.1:8877', 'Origin': 'http://127.0.0.1:8877'}, {'key': secret, 'extra': 'bad'}, 400),
                    ({'Host': '127.0.0.1:8877', 'Origin': 'http://127.0.0.1:8877'}, {'key': secret}, 200),
                ]
                for headers, fields, expected in cases:
                    raw = urlencode(fields).encode()
                    h = self.handler.__new__(self.handler)
                    h.path = endpoint
                    h.headers = {**headers, 'Content-Length': str(len(raw)), 'Content-Type': 'application/x-www-form-urlencoded'}
                    h.rfile = io.BytesIO(raw)
                    h.respond = lambda code, content: responses.append((code, content))
                    h.do_POST()
                    if responses[-1][0] != expected:
                        raise AssertionError('Unexpected bridge status')
            def server_close(self):
                self.closed = True
        with patch.object(bridge, 'HTTPServer', Server), contextlib.redirect_stdout(stdout):
            result = bridge.receive_key(timeout=2)
        self.assertEqual(result, secret)
        self.assertEqual([x[0] for x in responses], [403, 403, 400, 200])
        self.assertNotIn(secret, stdout.getvalue() + repr(responses))
        self.assertIn('127.0.0.1:8877/', stdout.getvalue())

if __name__ == '__main__':
    unittest.main(verbosity=2)
