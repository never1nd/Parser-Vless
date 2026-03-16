
import threading
from config import CHANNELS, OUTPUT_PREMIUM, OUTPUT_FREE, EXTRA_FEEDS_ENABLED, EXTRA_FEEDS_URLS
from modules.github_parser import GitHubParser
from modules.telegram_parser import TelegramParser
from modules.web_parser import WebParser
from utils.validator import validate_vless, extract_vless
from utils.scraper import logger
import asyncio
from database import SessionLocal, Source, init_db
from sqlalchemy import select
import base64
from utils.scraper import BaseScraper

async def run_pipeline(channel_name, resources):
    logger.info(f"--- Starting {channel_name.upper()} Pipeline ---")
    
    all_keys = set()
    loop = asyncio.get_running_loop()
    
    # 1. GitHub
    gh = GitHubParser()
    logger.info(f"--- {channel_name.upper()} Phase: GitHub Parsing ---")
    gh_keys = await loop.run_in_executor(None, gh.parse_links, resources.get('github', []))
    all_keys.update(gh_keys)
    logger.info(f"GitHub phase found {len(gh_keys)} keys")
    
    # 2. Telegram
    tg = TelegramParser()
    logger.info(f"--- {channel_name.upper()} Phase: Telegram Parsing ---")
    tg_keys = await loop.run_in_executor(None, tg.parse_channels, resources.get('telegram', []))
    all_keys.update(tg_keys)
    logger.info(f"Telegram phase found {len(tg_keys)} keys")
    
    # 3. Web
    web = WebParser()
    logger.info(f"--- {channel_name.upper()} Phase: Web Parsing ---")
    web_keys = await loop.run_in_executor(None, web.parse_sites, resources.get('web', []))
    all_keys.update(web_keys)
    logger.info(f"Web phase found {len(web_keys)} keys")

    # 3b. External feeds (optional)
    if EXTRA_FEEDS_ENABLED and EXTRA_FEEDS_URLS:
        ext = BaseScraper()
        ext_keys_total = 0
        for url in EXTRA_FEEDS_URLS:
            logger.info(f"Parsing external feed: {url}")
            text = ext.fetch(url)
            if not text or text == "404_NOT_FOUND":
                continue
            keys = _extract_from_feed(text)
            ext_keys_total += len(keys)
            all_keys.update(keys)
        logger.info(f"External feeds found {ext_keys_total} keys")
    
    # 4. Filter and Save
    valid_keys = []
    for key in all_keys:
        if validate_vless(key):
            valid_keys.append(key)
            
    # Deduplicate by UUID to reduce noise
    from utils.xray_handler import parse_vless_url
    uuid_seen = set()
    dedup_keys = []
    for key in valid_keys:
        data = parse_vless_url(key)
        if not data:
            continue
        uuid = data.get("uuid")
        if not uuid or uuid in uuid_seen:
            continue
        uuid_seen.add(uuid)
        dedup_keys.append(key)

    # Save to Database first (Primary storage)
    from database import save_vless_keys_bulk
    await loop.run_in_executor(None, save_vless_keys_bulk, dedup_keys)
    
    # Save to Text File (Secondary storage/export)
    output_file = resources.get('output', f"{channel_name}_vless.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        for key in dedup_keys:
            f.write(f"{key}\n")
            
    logger.info(f"--- {channel_name.upper()} Pipeline Finished. Saved {len(dedup_keys)} keys to DB and {output_file} ---")

def _extract_from_feed(text: str):
    """Extracts VLESS links from plain text or base64-encoded subscriptions."""
    keys = extract_vless(text)
    if keys:
        return keys
    # Try base64 decode if no keys found
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        return extract_vless(decoded)
    except Exception:
        return []

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
