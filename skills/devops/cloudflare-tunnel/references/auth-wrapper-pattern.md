# HTTP Basic Auth Proxy Pattern

Python HTTP proxy that adds HTTP Basic Auth in front of any backend service.
Uses only stdlib — no pip dependencies needed.

## When to Use

- Backend app (Streamlit, Flask dev server, etc.) lacks built-in authentication
- You want simple username/password protection without modifying the app
- Cloudflare Access is not available or not desired

## Full Implementation

```python
#!/usr/bin/env python3
"""
HTTP Basic Auth wrapper. Proxies authenticated requests to a backend.
Credentials configured via USERNAME / PASSWORD constants.
"""
import base64
import http.client
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

USERNAME = "sa"
PASSWORD = "your-password"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8502  # Backend listens here, wrapper on 8501

class AuthProxyHandler(BaseHTTPRequestHandler):
    def check_auth(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode("utf-8")
            user, pwd = decoded.split(":", 1)
            return user == USERNAME and pwd == PASSWORD
        except Exception:
            return False

    def handle_request(self):
        if not self.check_auth():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="MyApp"')
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Required</h1></body></html>")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        skip = {"host", "authorization", "connection", "transfer-encoding", "keep-alive"}
        fwd_headers = {k: v for k, v in self.headers.items() if k.lower() not in skip}
        fwd_headers["Host"] = f"{BACKEND_HOST}:{BACKEND_PORT}"

        try:
            conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=120)
            conn.request(self.command, self.path, body=body, headers=fwd_headers)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for h, v in resp.getheaders():
                if h.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(h, v)
            self.end_headers()
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
            conn.close()
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Backend error: {e}".encode())

    def do_GET(self):     self.handle_request()
    def do_POST(self):    self.handle_request()
    def do_PUT(self):     self.handle_request()
    def do_DELETE(self):  self.handle_request()
    def do_PATCH(self):   self.handle_request()
    def log_message(self, *args): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    server = HTTPServer(("127.0.0.1", port), AuthProxyHandler)
    print(f"Auth proxy listening on 127.0.0.1:{port}")
    server.serve_forever()
```

## Systemd Integration

Two services: backend (internal port) + auth wrapper (exposed port).

```ini
# backend.service (e.g. streamlit-onetag.service)
[Unit]
Description=Backend App (internal)
After=network-online.target
[Service]
Type=simple
WorkingDirectory=/path/to/app
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port 8502 --server.headless true --server.address 127.0.0.1
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
```

```ini
# auth-wrapper.service (e.g. auth-wrapper-onetag.service)
[Unit]
Description=HTTP Basic Auth Wrapper
After=backend.service
Requires=backend.service
[Service]
Type=simple
ExecStart=/path/to/venv/bin/python /path/to/auth_wrapper.py 8501
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
```

**Key:** Use absolute paths to venv Python. Do NOT rely on `WorkingDirectory` + relative path — it causes exit code 1 in systemd.

## Limitations

- No HTTPS internally (backend binds to 127.0.0.1, only the CF tunnel provides HTTPS)
- No session persistence — credentials sent with every request
- Browser may cache credentials aggressively (use `Cache-Control: no-store` header)
- Not suitable for high-traffic production use (use nginx or oauth2-proxy instead)
