
import threading
from config import CHANNELS, OUTPUT_PREMIUM, OUTPUT_FREE
from modules.github_parser import GitHubParser
from modules.telegram_parser import TelegramParser
from modules.web_parser import WebParser
from utils.validator import validate_vless
from utils.scraper import logger
import asyncio
from database import SessionLocal, Source, init_db
from sqlalchemy import select

async def run_pipeline(channel_name, resources):
    logger.info(f"--- Starting {channel_name.upper()} Pipeline ---")
    
    all_keys = set()
    loop = asyncio.get_running_loop()
    
    # 1. GitHub (Running sync code in executor)
    gh = GitHubParser()
    gh_keys = await loop.run_in_executor(None, gh.parse_links, resources.get('github', []))
    all_keys.update(gh_keys)
    
    # 2. Telegram (Now using web-scraping to support 24/7 headless mode)
    tg = TelegramParser()
    tg_keys = await tg.parse_channels(resources.get('telegram', []))
    all_keys.update(tg_keys)
    
    # 3. Web
    web = WebParser()
    web_keys = await loop.run_in_executor(None, web.parse_sites, resources.get('web', []))
    all_keys.update(web_keys)
    
    # 4. Filter and Save
    valid_keys = []
    for key in all_keys:
        if validate_vless(key):
            valid_keys.append(key)
            
    output_file = resources.get('output', f"{channel_name}_vless.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for key in valid_keys:
            f.write(f"{key}\n")
            
    logger.info(f"--- {channel_name.upper()} Pipeline Finished. Saved {len(valid_keys)} valid keys to {output_file} ---")

async def async_main():
    # Ensure DB is initialized
    init_db()
    
    # 1. Fetch sources from DB
    db = SessionLocal()
    try:
        stmt = select(Source).where(Source.is_active == True)
        sources = db.execute(stmt).scalars().all()
    finally:
        db.close()
        
    if not sources:
        logger.warning("No sources found in database. Using config.py as fallback.")
        tasks = []
        for channel_name, resources in CHANNELS.items():
            tasks.append(run_pipeline(channel_name, resources))
        await asyncio.gather(*tasks)
    else:
        # Group by channel for pipeline
        grouped_sources = {"premium": {"github": [], "telegram": [], "web": []}, 
                           "free": {"github": [], "telegram": [], "web": []}}
        for s in sources:
            grouped_sources[s.channel][s.type].append(s.url)
            
        tasks = []
        for channel_name, resources in grouped_sources.items():
            resources['output'] = OUTPUT_PREMIUM if channel_name == "premium" else OUTPUT_FREE
            tasks.append(run_pipeline(channel_name, resources))
        await asyncio.gather(*tasks)
        
    logger.info("All parsing tasks completed.")
