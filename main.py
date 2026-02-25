
import threading
from config import CHANNELS, OUTPUT_PREMIUM, OUTPUT_FREE
from modules.github_parser import GitHubParser
from modules.telegram_parser import TelegramParser
from modules.web_parser import WebParser
from utils.validator import validate_vless
from utils.scraper import logger
import asyncio
from telethon import TelegramClient
from config import API_ID, API_HASH

# Global Telethon client to share across threads
tg_client = TelegramClient('vless_parser_session', API_ID, API_HASH)

async def run_pipeline(channel_name, resources):
    logger.info(f"--- Starting {channel_name.upper()} Pipeline ---")
    
    all_keys = set()
    loop = asyncio.get_running_loop()
    
    # 1. GitHub (Running sync code in executor)
    gh = GitHubParser()
    gh_keys = await loop.run_in_executor(None, gh.parse_links, resources.get("github", []))
    all_keys.update(gh_keys)
    
    # 2. Telegram
    tg = TelegramParser(client=tg_client)
    tg_keys = await tg.parse_channels(resources.get("telegram", []))
    all_keys.update(tg_keys)
    
    # 3. Web (Running sync code in executor)
    web = WebParser()
    web_keys = await loop.run_in_executor(None, web.parse_sites, resources.get("web", []))
    all_keys.update(web_keys)
    
    # 4. Validation
    valid_keys = []
    logger.info(f"Total unique keys found for {channel_name}: {len(all_keys)}")
    logger.info(f"Validating keys...")
    for key in all_keys:
        if validate_vless(key):
            valid_keys.append(key)
    
    # Remove any potential validation-stage dupes (though unlikely with set)
    valid_keys = list(dict.fromkeys(valid_keys))
    
    # 5. Save results
    output_file = OUTPUT_PREMIUM if channel_name == "premium" else OUTPUT_FREE
    with open(output_file, "w", encoding="utf-8") as f:
        for key in valid_keys:
            f.write(f"{key}\n")
            
    logger.info(f"--- {channel_name.upper()} Pipeline Finished. Saved {len(valid_keys)} valid keys to {output_file} ---")

async def async_main():
    # 0. Authorize Telegram
    print("--- Telegram Authorization ---")
    await tg_client.start()
    
    # Run pipelines in parallel using asyncio.gather
    tasks = []
    for channel_name, resources in CHANNELS.items():
        tasks.append(run_pipeline(channel_name, resources))
        
    await asyncio.gather(*tasks)
    logger.info("All parsing tasks completed.")

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
