import aiohttp
import json
import time
from config import config
from mythic_container.logging import logger

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
LOGIN_BASE = "https://login.microsoftonline.com"

_access_token = None
_token_expiry = 0


async def _get_headers():
    global _access_token, _token_expiry
    if _access_token and time.time() < _token_expiry - 60:
        return {
            "Authorization": f"Bearer {_access_token}",
            "Content-Type": "application/json",
        }
    await _authenticate()
    return {
        "Authorization": f"Bearer {_access_token}",
        "Content-Type": "application/json",
    }


async def _authenticate():
    global _access_token, _token_expiry
    url = f"{LOGIN_BASE}/{config['tenant_id']}/oauth2/v2.0/token"
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            if resp.status == 200:
                body = await resp.json()
                _access_token = body["access_token"]
                _token_expiry = time.time() + body.get("expires_in", 3600)
                if config.get("debug"):
                    logger.info("Graph API: authenticated successfully")
            else:
                text = await resp.text()
                logger.error(f"Graph API auth failed ({resp.status}): {text}")
                raise Exception(f"Authentication failed: {resp.status}")


async def get_channel_messages(top=50):
    url = (
        f"{GRAPH_BASE}/teams/{config['team_id']}"
        f"/channels/{config['channel_id']}/messages?$top={top}"
    )
    headers = await _get_headers()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                body = await resp.json()
                return body.get("value", [])
            else:
                text = await resp.text()
                logger.error(f"Graph API get messages failed ({resp.status}): {text}")
                return []


async def send_message(content):
    if config.get("webhook_url"):
        return await _send_via_webhook(content)
    return await _send_via_graph(content)


async def _send_via_graph(content):
    url = (
        f"{GRAPH_BASE}/teams/{config['team_id']}"
        f"/channels/{config['channel_id']}/messages"
    )
    headers = await _get_headers()
    payload = {"body": {"contentType": "text", "content": content}}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status in (200, 201):
                if config.get("debug"):
                    logger.info("Graph API: message sent")
                return await resp.json()
            else:
                text = await resp.text()
                logger.error(f"Graph API send failed ({resp.status}): {text}")
                return None


async def _send_via_webhook(content):
    url = config["webhook_url"]
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": json.dumps(
                    {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": [{"type": "TextBlock", "text": content, "wrap": True}],
                    }
                ),
            }
        ],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status in (200, 201, 202):
                if config.get("debug"):
                    logger.info("Webhook: message sent")
                return True
            else:
                text = await resp.text()
                logger.error(f"Webhook send failed ({resp.status}): {text}")
                return None


async def reply_to_message(message_id, content):
    url = (
        f"{GRAPH_BASE}/teams/{config['team_id']}"
        f"/channels/{config['channel_id']}/messages/{message_id}/replies"
    )
    headers = await _get_headers()
    payload = {"body": {"contentType": "text", "content": content}}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status in (200, 201):
                if config.get("debug"):
                    logger.info(f"Graph API: replied to {message_id}")
                return await resp.json()
            else:
                text = await resp.text()
                logger.error(f"Graph API reply failed ({resp.status}): {text}")
                return None


async def delete_message(message_id):
    url = (
        f"{GRAPH_BASE}/teams/{config['team_id']}"
        f"/channels/{config['channel_id']}/messages/{message_id}/softDelete"
    )
    headers = await _get_headers()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            if resp.status in (200, 204):
                if config.get("debug"):
                    logger.info(f"Graph API: deleted message {message_id}")
            else:
                text = await resp.text()
                logger.warning(
                    f"Graph API delete failed ({resp.status}): {text}"
                )
