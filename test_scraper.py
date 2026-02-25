import asyncio
import logging
import sys
import os

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Add current dir to path
sys.path.append(os.getcwd())

from modules.web_parser import WebParser
from database import init_db

async def test_rutracker_scraping():
    logger.info("Initializing DB...")
    init_db()
    
    parser = WebParser()
    urls = [
        "https://rutracker.net/forum/viewforum.php?f=1649"
    ]
    
    logger.info(f"Testing scraping for: {urls}")
    # Run sync method in executor
    loop = asyncio.get_running_loop()
    keys = await loop.run_in_executor(None, parser.parse_sites, urls)
    
    logger.info(f"Found {len(keys)} unique Vless keys.")
    if keys:
        for k in list(keys)[:3]:
            logger.info(f"Sample key: {k[:50]}...")
            
    logger.info("Test complete.")

if __name__ == "__main__":
    asyncio.run(test_rutracker_scraping())
