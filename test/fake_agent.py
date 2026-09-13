#!/usr/bin/env python3
"""
Fake agent that simulates a Starburst implant talking to the
MS Teams C2 profile via the mock Graph API server.

This mimics what the real agent does:
  1. Authenticate (get access token)
  2. Post a message to the Teams channel (agent -> C2 server)
  3. Poll the channel for a response (C2 server -> agent)

Usage:
    # Start the mock server first:
    python mock_server.py

    # Then run this:
    python fake_agent.py
"""

import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

GRAPH_BASE = os.environ.get("GRAPH_URL", "http://localhost:8443")
TENANT_ID = "fake-tenant-id"
CLIENT_ID = "fake-client-id"
CLIENT_SECRET = "fake-client-secret"
TEAM_ID = "fake-team-id"
CHANNEL_ID = "fake-channel-id"
AGENT_UUID = "11111111-1111-1111-1111-111111111111"

access_token = None


def authenticate():
    global access_token
    url = f"{GRAPH_BASE}/{TENANT_ID}/oauth2/v2.0/token"
    data = (
        f"grant_type=client_credentials"
        f"&scope=https%3A%2F%2Fgraph.microsoft.com%2F.default"
        f"&client_id={CLIENT_ID}"
        f"&client_secret={CLIENT_SECRET}"
    ).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
        access_token = body["access_token"]
        print(f"[+] Authenticated: token={access_token[:32]}...")


def send_message(content):
    url = f"{GRAPH_BASE}/v1.0/teams/{TEAM_ID}/channels/{CHANNEL_ID}/messages"
    payload = json.dumps({"body": {"contentType": "text", "content": content}}).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
        print(f"[+] Message sent: id={body['id']}")
        return body["id"]


def get_messages(top=10):
    url = f"{GRAPH_BASE}/v1.0/teams/{TEAM_ID}/channels/{CHANNEL_ID}/messages?$top={top}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")

    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read())
        return body.get("value", [])


def main():
    print("=" * 50)
    print("  Fake MS Teams Agent")
    print("=" * 50)

    # authenticate
    print("\n[*] Authenticating to Graph API...")
    authenticate()

    # simulate checkin
    checkin_data = json.dumps({
        "action": "checkin",
        "uuid": AGENT_UUID,
        "ips": ["192.168.1.100"],
        "os": "Windows 10",
        "user": "testuser",
        "host": "WORKSTATION1",
        "pid": 1234,
        "architecture": "x64",
    }).encode()

    # in real agent: UUID + AES encrypt + base64
    # for mock: just base64 the raw data with UUID prefix
    raw = AGENT_UUID.encode() + checkin_data
    b64_msg = base64.b64encode(raw).decode()

    print(f"\n[*] Posting checkin message ({len(b64_msg)} chars)...")
    msg_id = send_message(b64_msg)

    # poll for response
    print("\n[*] Polling for C2 server response...")
    for i in range(30):
        time.sleep(1)
        msgs = get_messages(top=5)
        for m in msgs:
            if m["id"] != msg_id:
                content = m["body"]["content"]
                print(f"\n[+] Got response: id={m['id']}")
                print(f"    Content ({len(content)} chars): {content[:80]}...")

                # decode
                try:
                    decoded = base64.b64decode(content)
                    uuid_part = decoded[:36].decode(errors="replace")
                    data_part = decoded[36:]
                    print(f"    UUID: {uuid_part}")
                    print(f"    Data: {data_part[:200]}")
                except Exception as e:
                    print(f"    (raw, not base64): {content[:200]}")
                return

        if (i + 1) % 5 == 0:
            print(f"    ... still waiting ({i + 1}s)")

    print("\n[-] No response received after 30s")
    print("    Is the C2 server running and pointed at the mock?")


if __name__ == "__main__":
    main()
