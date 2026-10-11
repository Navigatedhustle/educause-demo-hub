#!/usr/bin/env python3
"""Loopback-only browser companion and lifecycle API; no external dependencies."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit
from controller import Controller, DEMOS

ROOT = Path(__file__).resolve().parent
manager = Controller()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if '/api/status' not in str(args[0]):
            super().log_message(format, *args)

    def reply(self, status, body, content_type='application/json'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Permissions-Policy', 'microphone=(self "http://localhost:8100" "http://127.0.0.1:8100"), camera=(self "http://localhost:8100" "http://127.0.0.1:8100"), autoplay=*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/status':
            self.reply(200, manager.snapshot())
        elif path == '/api/demos':
            self.reply(200, DEMOS)
        elif path in ('/', '/hub.html', '/atlas.png', '/hub.js', '/hub.css'):
            name = 'hub.html' if path == '/' else path.lstrip('/')
            mime = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png'}
            file = ROOT / name
            self.reply(200, file.read_bytes(), mime[file.suffix])
        else:
            self.reply(404, b'Not found', 'text/plain')

    def do_POST(self):
        # Local UI only: reject browser cross-origin writes and DNS rebinding.
        if self.headers.get('Host') not in ('127.0.0.1:8790', 'localhost:8790') or self.headers.get('Origin') not in (None, 'http://127.0.0.1:8790', 'http://localhost:8790'):
            self.reply(403, {'error': 'Use the local hub.'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size > 1024:
                raise ValueError('Request too large')
            data = json.loads(self.rfile.read(size) or b'{}')
            if self.path == '/api/start':
                self.reply(202, manager.request(data['demo']))
            elif self.path == '/api/stop':
                self.reply(202, manager.request())
            else:
                self.reply(404, {'error': 'Unknown action'})
        except (ValueError, KeyError) as error:
            self.reply(400, {'error': str(error)})


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8790), Handler).serve_forever()
