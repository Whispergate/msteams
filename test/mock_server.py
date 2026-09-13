#!/usr/bin/env python3
"""
Mock server that simulates both:
  1. Microsoft Graph API (OAuth2 token + Teams channel messages)
  2. Mythic C2 backend (POST endpoint that echoes/processes messages)

Run this to test the MS Teams C2 profile without any Azure or M365 account.

Usage:
    python mock_server.py

Endpoints:
    Graph API mock (port 8443):
        POST /{tenant}/oauth2/v2.0/token     -> returns fake access token
        GET  /v1.0/teams/{team}/channels/{ch}/messages  -> list messages
        POST /v1.0/teams/{team}/channels/{ch}/messages  -> send message
        POST /v1.0/teams/{team}/channels/{ch}/messages/{id}/softDelete -> delete

    Mythic mock (port 8080):
        POST /                                -> echo back agent message
"""

import json
import time
import uuid
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
from urllib.parse import parse_qs

messages = []
message_counter = 0
messages_lock = Lock()

# track which client_id each token was issued to
token_to_client = {}


class GraphAPIHandler(BaseHTTPRequestHandler):
    """Mocks Microsoft Graph API endpoints."""

    def log_message(self, format, *args):
        print(f"  [Graph] {args[0]}")

    def _send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return self.rfile.read(length)
        return b""

    def _get_client_id_from_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return token_to_client.get(token)
        return None

    def do_POST(self):
        global message_counter

        if "/oauth2/v2.0/token" in self.path:
            body = self._read_body()
            params = parse_qs(body.decode(errors="replace"))
            client_id = params.get("client_id", ["unknown"])[0]
            token = f"mock_token_{uuid.uuid4().hex[:16]}"
            token_to_client[token] = client_id
            print(f"  [Graph] Token issued to client_id={client_id}")
            self._send_json(200, {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 3600,
            })
            return

        if "/messages" in self.path and "/softDelete" not in self.path:
            body = self._read_body()
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"body": {"content": body.decode(errors="replace")}}

            content = payload.get("body", {}).get("content", "")
            client_id = self._get_client_id_from_token()

            with messages_lock:
                message_counter += 1
                msg_id = str(message_counter)

                msg = {
                    "id": msg_id,
                    "createdDateTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "from": {
                        "application": {"id": client_id} if client_id else None,
                        "user": {"displayName": "Agent", "id": "agent-user-id"}
                    },
                    "body": {"contentType": "text", "content": content},
                    "messageType": "message",
                }

                messages.append(msg)

            sender = f"app:{client_id}" if client_id else "anonymous"
            print(f"  [Graph] Message #{msg_id} stored ({len(content)} chars) from {sender}")
            self._send_json(201, msg)
            return

        if "/softDelete" in self.path:
            parts = self.path.split("/messages/")
            if len(parts) > 1:
                msg_id = parts[1].split("/")[0]
                with messages_lock:
                    messages[:] = [m for m in messages if m["id"] != msg_id]
                print(f"  [Graph] Message #{msg_id} deleted")
            self._send_json(204, {})
            return

        self._send_json(404, {"error": "not found"})

    def do_GET(self):
        if "/messages" in self.path:
            top = 50
            if "$top=" in self.path:
                try:
                    top = int(self.path.split("$top=")[1].split("&")[0])
                except Exception:
                    pass
            with messages_lock:
                recent = list(reversed(messages[-top:]))
            self._send_json(200, {"value": recent})
            return

        self._send_json(404, {"error": "not found"})


class MythicHandler(BaseHTTPRequestHandler):
    """Mocks the Mythic C2 backend — receives agent messages and responds."""

    def log_message(self, format, *args):
        print(f"  [Mythic] {args[0]}")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b""

        c2_header = self.headers.get("Mythic", "unknown")
        print(f"  [Mythic] Received {len(body)} bytes from C2 profile '{c2_header}'")
        print(f"  [Mythic] Data preview: {body[:100]}...")

        response = body
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def run_graph_server(port=8443):
    server = HTTPServer(("0.0.0.0", port), GraphAPIHandler)
    print(f"[*] Mock Graph API server on http://0.0.0.0:{port}")
    server.serve_forever()


def run_mythic_server(port=8080):
    try:
        server = HTTPServer(("0.0.0.0", port), MythicHandler)
        print(f"[*] Mock Mythic server on http://0.0.0.0:{port}")
        server.serve_forever()
    except OSError:
        print(f"[!] Mock Mythic server skipped (port {port} in use) — not needed when real Mythic is running")


def main():
    graph_port = int(os.environ.get("GRAPH_PORT", 8443))
    mythic_port = int(os.environ.get("MYTHIC_PORT", 8080))

    print("=" * 60)
    print("  MS Teams C2 Profile - Mock Test Server")
    print("=" * 60)
    print()
    print(f"  Graph API mock:  http://localhost:{graph_port}")
    print(f"  Mythic mock:     http://localhost:{mythic_port}")
    print()
    print("  Ctrl+C to stop")
    print("=" * 60)

    t1 = Thread(target=run_graph_server, args=(graph_port,), daemon=True)
    t2 = Thread(target=run_mythic_server, args=(mythic_port,), daemon=True)
    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down")


if __name__ == "__main__":
    main()
