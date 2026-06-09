#!/usr/bin/env python3
"""
Figma Asset Exporter — local save server.
Run once, leave the terminal open while using the plugin.

  python save_server.py

Press Ctrl+C to stop.
"""
import http.server, json, base64, os, sys

PORT = 7788


class Handler(http.server.BaseHTTPRequestHandler):

    # ── CORS helpers ──────────────────────────────────────────────────────────
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ── Ping ──────────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == '/ping':
            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404)
            self.end_headers()

    # ── Save file ─────────────────────────────────────────────────────────────
    def do_POST(self):
        if self.path != '/save':
            self.send_response(404)
            self.end_headers()
            return

        try:
            length   = int(self.headers['Content-Length'])
            body     = json.loads(self.rfile.read(length).decode('utf-8'))

            base_path  = body.get('basePath',  '').strip()
            path_parts = body.get('pathParts', [])
            filename   = body.get('filename',  'asset')
            data       = base64.b64decode(body['data'])

            if not base_path:
                raise ValueError('basePath is empty')

            # Sanitise path components
            def safe(s):
                return ''.join(
                    c if c not in r'<>:"/\|?*' and ord(c) >= 32 else '_'
                    for c in str(s)
                ).strip() or 'unnamed'

            folder = base_path
            for part in path_parts:
                folder = os.path.join(folder, safe(part))
            os.makedirs(folder, exist_ok=True)

            # Unique filename
            safe_fn  = safe(filename)
            filepath = os.path.join(folder, safe_fn)
            if os.path.exists(filepath):
                name, ext = os.path.splitext(safe_fn)
                n = 1
                while os.path.exists(os.path.join(folder, f'{name}_{n}{ext}')):
                    n += 1
                filepath = os.path.join(folder, f'{name}_{n}{ext}')

            with open(filepath, 'wb') as f:
                f.write(data)

            print(f'  ✔  {filepath}')

            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'path': filepath}).encode())

        except Exception as exc:
            print(f'  ✖  {exc}', file=sys.stderr)
            self.send_response(500)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': False, 'error': str(exc)}).encode())

    def log_message(self, *_):   # silence default request log
        pass


if __name__ == '__main__':
    server = http.server.HTTPServer(('', PORT), Handler)
    print(f'✅  Asset Exporter server — port {PORT}')
    print('    Leave this window open while exporting from Figma.')
    print('    Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
