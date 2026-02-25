import asyncio
from telethon import TelegramClient
from config import API_ID, API_HASH
from utils.validator import extract_vless
from utils.scraper import logger

class TelegramParser:
    def __init__(self, client=None):
        self.api_id = API_ID
        self.api_hash = API_HASH
        if client:
            self.client = client
        else:
            self.client = TelegramClient('vless_parser_session', self.api_id, self.api_hash)

    async def authorize(self):
        """Ensures the client is authorized in the main thread."""
        logger.info("Initializing Telegram session...")
        await self.client.start()
        logger.info("Telegram authorized successfully.")

    async def parse_channels(self, channels, limit=50):
        all_keys = set()
        # No 'async with' here, assuming client is already started
        for channel in channels:
                logger.info(f"Parsing Telegram channel: @{channel}")
                try:
                    async for message in self.client.iter_messages(channel, limit=limit):
                        if message.text:
                            keys = extract_vless(message.text)
                            all_keys.update(keys)
                    logger.info(f"Finished parsing @{channel}")
                except Exception as e:
                    logger.error(f"Error parsing Telegram channel {channel}: {e}")
        return list(all_keys)

    def run(self, channels, limit=50):
        # Run the async code in a loop
        return asyncio.run(self.parse_channels(channels, limit))
