# msteams

A [Mythic](https://github.com/its-a-feature/Mythic) C2 Profile that uses the Microsoft Graph API to communicate through a Microsoft Teams channel.

## How It Works

The C2 server polls a Teams channel for new messages using the Microsoft Graph API. Agent messages are forwarded to Mythic, and responses are posted back to the channel. Communication looks like normal Teams channel activity.

This profile supports:

- Kill Dates
- Sleep Intervals with Jitter
- AES256 Encryption
- Proxy Configuration
- Optional message cleanup
- Webhook fallback for sending

## Installation

On your Mythic server:

```
sudo ./mythic-cli install github https://github.com/MythicC2Profiles/msteams
```

To install a specific branch:

```
sudo ./mythic-cli install github https://github.com/MythicC2Profiles/msteams branchname
```

## Setup

1. Create an Azure AD App Registration with the required Graph API permissions
2. Get your Team ID and Channel ID
3. Configure the C2 profile in Mythic with your Azure credentials

Full setup instructions are in the documentation, accessible at `https://<your-mythic-server>:7443/docs/c2-profiles/msteams` after installing the C2 profile.

## Required Azure Permissions

| Permission | Type | Purpose |
|------------|------|---------|
| `ChannelMessage.Read.All` | Application | Read channel messages |
| `ChannelMessage.Send` | Application | Send channel messages |

If `ChannelMessage.Send` is not available, use `Group.ReadWrite.All` or configure a webhook URL.

## Compatible Agents

Any Mythic agent that implements the `msteams` C2 profile parameters can use this profile. The agent needs to:

1. Authenticate to the Graph API (or use a webhook) using the configured credentials
2. Post base64-encoded Mythic messages to the configured Teams channel
3. Poll the channel for responses from the C2 server

## Configuration

The server configuration is in `C2_Profiles/msteams/msteams/c2_code/config.json`:

```json
{
  "tenant_id": "",
  "client_id": "",
  "client_secret": "",
  "team_id": "",
  "channel_id": "",
  "webhook_url": "",
  "poll_interval": 10,
  "clear_messages": false,
  "debug": false
}
```

Edit this via the Mythic UI: C2 Profiles > msteams > View/Edit Config.
