"""One-shot loopback form: transfer a newly created key into worker memory only."""
import re
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs


def receive_key(port=0, timeout=1800):
    token = secrets.token_urlsafe(32)
    endpoint = '/' + token
    origin = f'http://127.0.0.1:{port}'
    result = []
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            # HTTPServer.timeout limits accept(), not an incomplete request.
            self.connection.settimeout(5)

        def log_message(self, *_):
            pass

        def respond(self, code, content):
            data = content.encode()
            self.send_response(code)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.headers.get('Host') != f'127.0.0.1:{port}' or self.path != endpoint:
                return self.respond(404, 'Not found')
            self.respond(200, '<!doctype html><title>Plainvoice local connection</title>'
                '<h1>Connect this local batch</h1><p>The key goes only to this local process. '
                'It is not saved to a file, the repository, or browser storage.</p>'
                f'<form method="post" action="{endpoint}" autocomplete="off">'
                '<label>OpenRouter batch key <input name="key" type="password" '
                'autocomplete="off" required></label><button type="submit">Connect batch</button></form>')

        def do_POST(self):
            if (self.path != endpoint or self.headers.get('Host') != f'127.0.0.1:{port}'
                    or self.headers.get('Origin') != origin or result
                    or self.headers.get('Transfer-Encoding') is not None
                    or self.headers.get('Content-Type', '').split(';', 1)[0].strip()
                       != 'application/x-www-form-urlencoded'):
                return self.respond(403, 'Rejected')
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size < 1024:
                    raise ValueError()
                fields = parse_qs(self.rfile.read(size).decode(), strict_parsing=True)
                if set(fields) != {'key'} or len(fields['key']) != 1:
                    raise ValueError()
                key = fields['key'][0]
                if not re.fullmatch(r'sk-or-[A-Za-z0-9_-]{40,200}', key):
                    raise ValueError()
            except (ValueError, KeyError, UnicodeError, TimeoutError):
                return self.respond(400, 'Invalid key format')
            result.append(key)
            self.respond(200, '<title>Connected</title><h1>Connected</h1><p>The key is in worker memory. This form is now closed.</p>')

    class QuietHTTPServer(HTTPServer):
        def handle_error(self, request, client_address):
            # Never print request exceptions or request details to logs.
            pass

    server = QuietHTTPServer(('127.0.0.1', port), Handler)
    port = server.server_address[1]
    origin = f'http://127.0.0.1:{port}'
    server.timeout = 1
    print('KEY_BRIDGE_URL=' + origin + endpoint, flush=True)
    deadline = time.monotonic() + timeout
    try:
        while not result and time.monotonic() < deadline:
            server.handle_request()
        if not result:
            raise TimeoutError('Local key handoff timed out')
        return result.pop()
    finally:
        server.server_close()
