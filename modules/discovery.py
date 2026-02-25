import requests
import re
import asyncio
from utils.scraper import logger, BaseScraper
from database import SessionLocal, Source
from sqlalchemy import select
from config import CHANNELS

class DiscoveryModule(BaseScraper):
    def __init__(self):
        super().__init__()
        self.github_api_url = "https://api.github.com/search/code"
        
    def sync_discover_github(self):
        """Sync version of discover_github_sources to be run in executor."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.discover_github_sources())
        finally:
            loop.close()

    async def discover_github_sources(self):
        """
        Search GitHub for new files containing 'vless://'
        Note: Requires GitHub token for higher rate limits (optional for now)
        """
        logger.info("Searching GitHub for new potential sources...")
        query = "vless:// language:Text"
        params = {"q": query, "sort": "indexed", "order": "desc"}
        
        try:
            # Note: This might hit rate limits without a token
            response = requests.get(self.github_api_url, params=params, headers=self.headers, timeout=15)
            if response.status_code == 200:
                items = response.json().get('items', [])
                new_urls = []
                for item in items:
                    raw_url = item.get('html_url', '').replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    new_urls.append(raw_url)
                
                await self._save_new_sources(new_urls, "github", "free")
            else:
                logger.warning(f"GitHub Search API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Error during GitHub discovery: {e}")

    async def _save_new_sources(self, urls, s_type, channel):
        db = SessionLocal()
        try:
            for url in urls:
                # Check if exists
                stmt = select(Source).where(Source.url == url)
                result = db.execute(stmt).scalars().first()
                if not result:
                    new_src = Source(url=url, type=s_type, channel=channel)
                    db.add(new_src)
                    logger.info(f"New {s_type} source discovered: {url}")
            db.commit()
        finally:
            db.close()

    async def seed_initial_sources(self):
        """Sync DB with sources from config.py"""
        db = SessionLocal()
        try:
            logger.info("Syncing sources from config.py to database...")
            for channel, types in CHANNELS.items():
                for s_type, urls in types.items():
                    for url in urls:
                        # Check if exists
                        stmt = select(Source).where(Source.url == url)
                        result = db.execute(stmt).scalars().first()
                        if not result:
                            new_src = Source(url=url, type=s_type, channel=channel)
                            db.add(new_src)
                            logger.info(f"Added new source from config: {url}")
                        else:
                            # Re-activate if it was disabled
                            result.is_active = True
            db.commit()
            logger.info("Database sync complete.")
        finally:
            db.close()

if __name__ == "__main__":
    discovery = DiscoveryModule()
    asyncio.run(discovery.seed_initial_sources())
    asyncio.run(discovery.discover_github_sources())
