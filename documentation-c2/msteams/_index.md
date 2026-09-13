+++
title = "msteams"
chapter = false
weight = 5
+++

## Overview

The MS Teams C2 profile uses the Microsoft Graph API to send and receive messages through a Microsoft Teams channel. The C2 server polls the channel for new messages from agents, forwards them to Mythic, and posts Mythic's responses back to the channel.

This profile supports:

- Kill dates
- Sleep intervals with jitter
- AES256 encryption
- Proxy configuration
- Optional message cleanup (delete processed messages)
- Webhook fallback for sending messages

## Architecture

```
Agent <---> Teams Channel <---> C2 Server <---> Mythic
```

1. The agent posts its Mythic message (base64-encoded) to the Teams channel
2. The C2 server polls the channel for new messages via the Graph API
3. New agent messages are forwarded to Mythic over the internal API
4. Mythic's response is posted back to the Teams channel
5. The agent picks up the response on its next check-in

## Entra ID Setup

### 1. Create an App Registration

1. Go to [Azure Portal](https://portal.azure.com) > **Microsoft Entra ID** > **App registrations**
2. Click **New registration**
3. Name it anything (e.g. "Teams Integration")
4. Set **Supported account types** to "Accounts in this organizational directory only"
5. Click **Register**
6. Note the **Application (client) ID** and **Directory (tenant) ID**

### 2. Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and choose an expiry period
4. Click **Add** and **copy the secret value immediately** (it won't be shown again)

### 3. Grant API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Application permissions**
3. Add the following permissions:
   - `ChannelMessage.Read.All` — read channel messages
   - `ChannelMessage.Send` — send channel messages (if available; otherwise use `Group.ReadWrite.All`)
   - `ChannelMessage.UpdatePolicyViolation.All` — optional, needed for deleting messages via `clear_messages`
4. Click **Grant admin consent** for your organization

> **Note**: If `ChannelMessage.Send` is not available as an application permission in your tenant, you have two options:
> - Use `Group.ReadWrite.All` (broader but works)
> - Set up an Incoming Webhook or Workflow webhook in the channel and put the URL in the `webhook_url` config field

### 4. Get the Team and Channel IDs

**Team ID**: Use [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) to call `GET https://graph.microsoft.com/v1.0/groups` and find your team. The `id` field is your `team_id`.

**Channel ID**: Call `GET https://graph.microsoft.com/v1.0/teams/{team_id}/channels` and find the channel. The `id` field is your `channel_id`.

Alternatively, in the Teams desktop client:
1. Right-click the channel > **Get link to channel**
2. The URL contains the channel ID (URL-encoded)

## C2 Profile Configuration

Browse to **C2 Profiles** in Mythic, click the dropdown arrow next to **Start Profile**, then click **View/Edit Config** to set these values:

| Parameter | Description |
|-----------|-------------|
| `tenant_id` | Entra ID Directory (tenant) ID |
| `client_id` | Application (client) ID from the app registration |
| `client_secret` | Client secret value |
| `team_id` | ID of the Teams team |
| `channel_id` | ID of the Teams channel |
| `webhook_url` | Optional: Incoming Webhook URL for sending (leave empty to use Graph API) |
| `poll_interval` | Seconds between channel polls (default: 10) |
| `clear_messages` | Delete messages after processing (default: false) |
| `debug` | Enable verbose logging (default: false) |

## Agent Configuration

When building an agent payload, set these parameters:

| Parameter | Description |
|-----------|-------------|
| `tenant_id` | Same Entra ID tenant ID |
| `client_id` | Same or different app registration client ID for the agent |
| `client_secret` | Corresponding client secret |
| `team_id` | Same team ID |
| `channel_id` | Same channel ID |
| `callback_interval` | How often the agent checks in (seconds) |
| `callback_jitter` | Randomization percentage for callback interval |

## Webhook Fallback

If you cannot get application-level send permissions, you can use a webhook URL instead:

### Incoming Webhook (Classic)
1. In Teams, right-click the channel > **Connectors** > **Incoming Webhook**
2. Name it and click **Create**
3. Copy the webhook URL into the `webhook_url` config field

### Workflow Webhook (Modern)
1. In Teams, right-click the channel > **Workflows**
2. Select **Post to a channel when a webhook request is received**
3. Follow the setup wizard
4. Copy the webhook URL into the `webhook_url` config field

## OPSEC Considerations

- Use a **dedicated private channel** to avoid attention
- Enable `clear_messages` to clean up the channel after processing
- Keep `poll_interval` reasonable (10-30s) to avoid rate limiting
- The Teams Graph API rate limit is approximately 30 requests per second per app per tenant
- Messages are visible to anyone with access to the channel — keep the channel membership tight
- Consider using `AESPSK` encryption to protect message contents
