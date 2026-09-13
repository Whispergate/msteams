import aiohttp
from config import config
from mythic_container.logging import logger


async def send_to_mythic(message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            config["mythic_address"],
            headers={"Mythic": "msteams"},
            data=message,
        ) as resp:
            if resp.status == 200:
                return await resp.text()
            else:
                logger.error(
                    f"Mythic send failed ({resp.status}): {await resp.text()}"
                )
                return None
