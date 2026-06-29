#!/usr/bin/env python3
"""
DuckBotOS Session Picker — lightweight HTTP server
Serves the session picker UI and handles mode switching.
Runs as a systemd service on port 8080.

Endpoints:
  GET  /           — session picker HTML
  POST /api/session — switch kiosk mode (writes /etc/duckbotos/kiosk-mode symlink)
  GET  /api/status  — current kiosk mode status
"""

import http.server
import json
import os
import socket
import socketserver
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

KIOSK_MODE_FILE = Path("/etc/duckbotos/kiosk-mode")
KIOSK_CONFIG_DIR = Path("/etc/duckbotos")
SESSION_PORT = 8080

HERMES_URL = "http://localhost:9119"
OPENCLAW_URL = "http://localhost:18789/plugins/openclawos"
HYBRID_URL = "http://localhost:8081"  # GNOME hybrid mode

MODES = {
    "hermes":   {"label": "Hermes",   "url": HERMES_URL,   "service": "duckbotos-kiosk-hermes"},
    "openclaw": {"label": "OpenClaw",  "url": OPENCLAW_URL, "service": "duckbotos-kiosk-openclaw"},
    "hybrid":   {"label": "Hybrid",    "url": HYBRID_URL,   "service": "duckbotos-hybrid"},
}

INDEX_HTML = Path(__file__).parent / "index.html"


class SessionPickerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write(f"[session-picker] {fmt % args}\n")
        sys.stdout.flush()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.serve_index()
        elif parsed.path == "/api/status":
            self.serve_status()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/session":
            self.handle_session_switch()
        else:
            self.send_error(404, "Not Found")

    def serve_index(self):
        try:
            html = INDEX_HTML.read_text()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode())
        except FileNotFoundError:
            self.send_error(503, "Session picker HTML not found")

    def serve_status(self):
        current_mode = self._get_current_mode()
        status = {
            "mode": current_mode,
            "url": MODES.get(current_mode, {}).get("url", HERMES_URL),
            "available_modes": list(MODES.keys()),
            "hostname": socket.gethostname(),
        }
        self.send_json(status)

    def handle_session_switch(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body) if body else {}
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        mode = data.get("mode")
        if mode not in MODES:
            self.send_error(400, f"Unknown mode: {mode}")
            return

        # Write kiosk mode symlink
        target_url = MODES[mode]["url"]

        try:
            KIOSK_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            KIOSK_MODE_FILE.write_text(target_url)
        except PermissionError:
            # Fallback: try via pkexec (graphical sudo)
            import subprocess
            result = subprocess.run(
                ["pkexec", "bash", "-c", f'mkdir -p {KIOSK_CONFIG_DIR} && echo {target_url} > {KIOSK_MODE_FILE}'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self.send_error(500, f"Permission denied: {result.stderr}")
                return

        self.send_json({"ok": True, "mode": mode, "url": target_url})
        self.log_message(f"Switched to mode: {mode} → {target_url}")

    def _get_current_mode(self):
        try:
            if KIOSK_MODE_FILE.exists():
                url = KIOSK_MODE_FILE.read_text().strip()
                for m, info in MODES.items():
                    if info["url"] == url:
                        return m
            return "hermes"  # default
        except Exception:
            return "hermes"

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    port = SESSION_PORT

    with ReuseAddrTCPServer(("", port), SessionPickerHandler) as httpd:
        print(f"[session-picker] DuckBotOS Session Picker running on http://localhost:{port}")
        print(f"[session-picker] Modes: {', '.join(MODES.keys())}")
        print(f"[session-picker] Current mode: {SessionPickerHandler._get_current_mode(None)}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[session-picker] Shutting down...")
            sys.exit(0)


if __name__ == "__main__":
    main()