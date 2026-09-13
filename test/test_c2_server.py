#!/usr/bin/env python3
"""
Standalone test harness for the MS Teams C2 server code.
Runs the server's polling loop against the mock Graph API + mock Mythic.

Usage:
    # Terminal 1: start mocks
    python mock_server.py

    # Terminal 2: start C2 server against mocks
    python test_c2_server.py

    # Terminal 3: simulate an agent
    python fake_agent.py
"""

import asyncio
import json
import os
import sys

# Patch the Graph API and Mythic URLs to point at mocks
GRAPH_MOCK = os.environ.get("GRAPH_URL", "http://localhost:8443")
MYTHIC_MOCK = os.environ.get("MYTHIC_URL", "http://localhost:8080")

# Monkey-patch the graph_client module before importing server
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
    "..", "C2_Profiles", "msteams", "msteams", "c2_code"))

import graph_client
import mythic_client
from config import config

# Override graph API base URLs
graph_client.GRAPH_BASE = f"{GRAPH_MOCK}/v1.0"
graph_client.LOGIN_BASE = GRAPH_MOCK

# Load test config
config_path = os.path.join(os.path.dirname(__file__), "test_config.json")
with open(config_path, "rb") as f:
    config.update(json.loads(f.read().decode("utf-8")))

config["mythic_address"] = MYTHIC_MOCK

# Import and run the server's main loop
import server

print("[*] Starting C2 server against mock endpoints...")
print(f"    Graph API: {GRAPH_MOCK}")
print(f"    Mythic:    {MYTHIC_MOCK}")
print(f"    Poll interval: {config.get('poll_interval', 10)}s")
print()

asyncio.run(server.main())
