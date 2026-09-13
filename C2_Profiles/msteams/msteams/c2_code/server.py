#!/usr/local/bin/python
import asyncio
import json
import os
import sys
from config import config
from mythic_container.logging import logger
import graph_client
import mythic_client

processed_ids = set()
self_sent_ids = set()
MAX_PROCESSED_CACHE = 5000


def is_agent_message(msg):
    msg_id = msg.get("id")
    if msg_id in self_sent_ids:
        return False
    msg_type = msg.get("messageType", "")
    if msg_type != "message":
        return False
    body = msg.get("body", {})
    content = body.get("content", "").strip()
    if not content:
        return False
    return True


async def process_messages():
    global processed_ids, self_sent_ids
    messages = await graph_client.get_channel_messages(top=50)
    if not messages:
        return

    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id or msg_id in processed_ids:
            continue
        if not is_agent_message(msg):
            processed_ids.add(msg_id)
            continue

        content = msg["body"]["content"].strip()
        if config.get("debug"):
            logger.info(f"Processing message {msg_id} ({len(content)} bytes)")

        resp = await mythic_client.send_to_mythic(content)
        if resp is None:
            logger.warning(f"No response from Mythic for message {msg_id}")
            continue

        result = await graph_client.send_message(resp)
        if result and isinstance(result, dict) and "id" in result:
            self_sent_ids.add(result["id"])
            if config.get("debug"):
                logger.info(f"Tracked self-sent message {result['id']}")

        if config.get("clear_messages"):
            await graph_client.delete_message(msg_id)

        processed_ids.add(msg_id)

    if len(processed_ids) > MAX_PROCESSED_CACHE:
        processed_ids = set(list(processed_ids)[-1000:])
    if len(self_sent_ids) > MAX_PROCESSED_CACHE:
        self_sent_ids = set(list(self_sent_ids)[-1000:])


async def main():
    logger.info("MS Teams C2 server starting")

    with open("config.json", "rb") as f:
        config.update(json.loads(f.read().decode("utf-8")))

    config["mythic_address"] = os.environ.get("MYTHIC_ADDRESS", "")
    if not config["mythic_address"]:
        logger.error("MYTHIC_ADDRESS environment variable not set")
        sys.exit(1)

    for key in ("tenant_id", "client_id", "client_secret", "team_id", "channel_id"):
        if not config.get(key):
            logger.error(f"Required config field '{key}' is empty")
            sys.exit(1)

    poll_interval = int(config.get("poll_interval", 10))
    logger.info(
        f"Polling team={config['team_id']} channel={config['channel_id']} "
        f"every {poll_interval}s"
    )

    while True:
        try:
            await process_messages()
        except Exception as e:
            logger.error(f"Error in poll loop: {e}")
        await asyncio.sleep(poll_interval)


asyncio.run(main())
