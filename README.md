# msteams

A [Mythic](https://github.com/its-a-feature/Mythic) C2 Profile that uses the Microsoft Graph API to communicate through a Microsoft Teams channel.

## How It Works

```
Agent <---> Microsoft Teams Channel <---> C2 Server <---> Mythic
```

1. The agent authenticates to Microsoft Entra ID via OAuth2 client credentials
2. Posts its Mythic message (base64-encoded, AES-encrypted) to a Teams channel
3. The C2 server polls the channel via the Graph API, forwards new messages to Mythic
4. Mythic's response is posted back to the channel
5. The agent polls the channel and picks up the response

Communication appears as normal Teams channel activity.

This profile supports:

- Kill Dates
- Sleep Intervals with Jitter
- AES256 Encryption
- Proxy Configuration
- Optional message cleanup (delete messages after processing)
- Webhook fallback for sending

## Installation

From your Mythic server:

```
sudo ./mythic-cli install github https://github.com/Whispergate/msteams
```

Or from a local folder:

```
sudo ./mythic-cli install folder /path/to/msteams
```

## Entra ID Setup

1. **App Registration** - Create in Azure Portal > Microsoft Entra ID > App registrations
2. **Client Secret** - Generate under Certificates & secrets
3. **API Permissions** - Grant application permissions and admin consent:
   - `ChannelMessage.Read.All` - Read channel messages
   - `ChannelMessage.Send` - Send channel messages
4. **Team & Channel IDs** - Get via Graph Explorer or the Teams client channel link

If `ChannelMessage.Send` is not available, use `Group.ReadWrite.All` or configure a webhook URL.

Full setup instructions are in the Mythic documentation page after installation at `https://<your-mythic-server>:7443/docs/c2-profiles/msteams`.

## Configuration

Edit via the Mythic UI: C2 Profiles > msteams > View/Edit Config.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `tenant_id` | Entra ID tenant (directory) ID | |
| `client_id` | App registration client ID | |
| `client_secret` | App registration client secret | |
| `team_id` | Teams team ID | |
| `channel_id` | Teams channel ID | |
| `webhook_url` | Optional webhook URL for sending | |
| `graph_base` | Graph API base URL | `https://graph.microsoft.com/v1.0` |
| `login_base` | Login endpoint base URL | `https://login.microsoftonline.com` |
| `poll_interval` | Seconds between polls | `10` |
| `clear_messages` | Delete messages after processing | `false` |
| `debug` | Enable verbose logging | `false` |

## Compatible Agents

- **[Starburst](https://github.com/Whispergate/Starburst)** - Full support via WinHTTP-based MS Teams transport

Any Mythic agent that implements the `msteams` C2 profile parameters can use this profile. The agent needs to:

1. Authenticate to the Graph API using the configured credentials
2. Post base64-encoded Mythic messages to the configured Teams channel
3. Poll the channel for responses from the C2 server

## Testing Without Azure

A mock test infrastructure is included in `test/` for local testing without any Azure or M365 account. This lets you test the full C2 pipeline — including compiled implants — against a local fake Graph API.

### Mock Server Setup

1. Copy `test/mock_server.py` to your Mythic host and start it:
   ```
   python3 mock_server.py
   ```
   This starts a fake Graph API on port 8443.

2. Configure the msteams C2 profile in Mythic with mock values:
   ```json
   {
     "tenant_id": "fake-tenant-id",
     "client_id": "fake-client-id",
     "client_secret": "fake-client-secret",
     "team_id": "fake-team-id",
     "channel_id": "fake-channel-id",
     "graph_base": "http://<mythic-host-ip>:8443/v1.0",
     "login_base": "http://<mythic-host-ip>:8443",
     "poll_interval": 3,
     "clear_messages": true,
     "debug": true
   }
   ```

3. Start the msteams profile in the Mythic UI.

### Testing with a Compiled Implant (Starburst)

To test a real compiled agent against the mock, the agent binary needs to be built with the mock server's IP and port hardcoded instead of the real Graph API endpoints. In the Starburst agent code (`agent_code/src/transport/msteams.cc`):

```cpp
// Change these for mock testing:
#define GRAPH_API_HOST  "<mythic-host-ip>"
#define LOGIN_HOST      "<mythic-host-ip>"
#define API_PORT        8443

// And change WINHTTP_FLAG_SECURE to 0 in WinHttpOpenRequest
// since the mock server uses plain HTTP:
        WINHTTP_DEFAULT_ACCEPT_TYPES,
        0
```

Then reinstall Starburst, build a payload with the msteams profile (using the same fake tenant/client/team/channel IDs), and run it on a Windows VM that can reach the Mythic host.

**Remember to revert these changes before building production payloads:**
```cpp
#define GRAPH_API_HOST  "graph.microsoft.com"
#define LOGIN_HOST      "login.microsoftonline.com"
#define API_PORT        443

        WINHTTP_DEFAULT_ACCEPT_TYPES,
        WINHTTP_FLAG_SECURE
```

### Testing with the Fake Agent (No Compilation)

For a quick pipeline test without compiling an agent:
```
GRAPH_URL=http://<mythic-host-ip>:8443 python test/fake_agent.py
```

See [test/README.md](test/README.md) for more details.

## OPSEC Considerations

- Use a dedicated private channel with minimal membership
- Enable `clear_messages` to clean up after processing
- Keep `poll_interval` reasonable (10-30s) to avoid rate limiting
- All messages are AES256-encrypted at the Mythic payload level
- Teams messages are NOT end-to-end encrypted (visible to tenant admins and Microsoft)
- The Graph API rate limit is approximately 30 requests per second per app per tenant

## File Structure

```
msteams/
  config.json                          # Mythic container config
  C2_Profiles/msteams/
    Dockerfile                         # Container image
    main.py                            # Mythic service entrypoint
    requirements.txt                   # Python dependencies
    rabbitmq_config.json               # RabbitMQ settings
    msteams/
      c2_functions/msteams.py          # C2Profile class + parameters
      c2_code/
        server.py                      # Main polling loop
        graph_client.py                # MS Graph API client
        mythic_client.py               # Mythic API forwarder
        config.py                      # Config singleton
        config.json                    # Default config values
  documentation-c2/msteams/_index.md   # Mythic docs page
  test/
    mock_server.py                     # Mock Graph API server
    fake_agent.py                      # Simulated agent for testing
    test_c2_server.py                  # Standalone C2 server test harness
    test_config.json                   # Test config with fake values
```
