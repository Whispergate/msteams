# Testing the MS Teams C2 Profile

Test the full C2 pipeline locally without any Azure or Microsoft account.

## Quick Start

Open three terminals:

### Terminal 1 — Mock servers (Graph API + Mythic)
```bash
cd test
python mock_server.py
```

### Terminal 2 — C2 server (pointed at mocks)
```bash
cd test
python test_c2_server.py
```

### Terminal 3 — Fake agent
```bash
cd test
python fake_agent.py
```

## What happens

1. **mock_server.py** starts two HTTP servers:
   - Port 8443: Fake Microsoft Graph API (token auth, channel messages CRUD)
   - Port 8080: Fake Mythic backend (echoes agent messages back)

2. **test_c2_server.py** runs the real C2 server code but patched to talk to localhost mocks instead of real Graph API / Mythic.

3. **fake_agent.py** simulates a Starburst implant:
   - Authenticates to the mock Graph API
   - Posts a base64-encoded checkin message to the channel
   - Polls for the C2 server's response

## Expected output

The fake agent posts a message, the C2 server picks it up, forwards to mock Mythic, posts the response back, and the fake agent reads it. You should see log lines in all three terminals showing the message flow.
