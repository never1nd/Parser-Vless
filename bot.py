import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import (
    BOT_TOKEN,
    OUTPUT_GROUP1,
    OUTPUT_GROUP2,
    OUTPUT_GROUP3,
    OUTPUT_GROUP4,
    SUBS_BASE_URL,
    SUBS_SECRET,
    ENABLE_DISCOVERY,
)
import os
import platform
import zipfile
import requests

# Logging MUST be set up before any function that uses logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our existing logic
from parser_engine import async_main as run_parsing_pipeline
from filter_reality import filter_keys
from verify_working import verify_working
from modules.discovery import DiscoveryModule
from scheduler.recheck_worker import recheck_working_groups
from utils.status_store import load_status

# URL for Xray-core releases
XRAY_RELEASES = "https://github.com/XTLS/Xray-core/releases/latest/download/"

async def ensure_xray_binary():
    from config import XRAY_PATH
    import zipfile
    system = platform.system().lower()
    is_linux = system != "windows"

    if os.path.exists(XRAY_PATH):
        logger.info(f"✅ Xray binary found at: {XRAY_PATH}")
        if is_linux:
            try:
                os.chmod(XRAY_PATH, 0o755)
                logger.info("✅ Execute permission set on xray binary.")
            except Exception as e:
                logger.error(f"❌ Failed to set permissions: {e}")
        return

    logger.warning(f"⚠️ Xray binary not found at {XRAY_PATH}. Downloading now...")
    
    arch = "64"
    if is_linux:
        filename = f"Xray-linux-{arch}.zip"
    else:
        filename = f"Xray-windows-{arch}.zip"

    url = f"https://github.com/XTLS/Xray-core/releases/latest/download/{filename}"
    logger.info(f"Downloading Xray from: {url}")
    
    try:
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("Download complete. Extracting...")

        with zipfile.ZipFile(filename, "r") as z:
            z.extractall(".")
        os.remove(filename)

        if is_linux and os.path.exists("xray"):
            os.chmod("xray", 0o755)
            logger.info("✅ Xray downloaded and ready.")
        else:
            logger.error("❌ xray binary not found after extraction!")
    except Exception as e:
        logger.error(f"❌ Failed to download Xray: {e}")
        logger.error("Verification will be skipped.")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def _subscription_urls():
    if not SUBS_BASE_URL:
        return {}
    base = f"{SUBS_BASE_URL}/subs/{SUBS_SECRET}"
    return {
        1: f"{base}/group1.txt",
        2: f"{base}/group2.txt",
        3: f"{base}/group3.txt",
        4: f"{base}/group4.txt",
    }

async def scheduled_task():
    logger.info("Starting scheduled 6-hour task...")
    try:
        loop = asyncio.get_running_loop()

        # Phase 1: Optional discovery
        if ENABLE_DISCOVERY:
            discovery = DiscoveryModule()
            await loop.run_in_executor(None, discovery.sync_discover_github)
        
        # Phase 2: Parsing
        await run_parsing_pipeline()
        
        # Phase 3: Filter & Verify
        # These are heavy sync tasks, run in executor
        await loop.run_in_executor(None, filter_keys)
        await loop.run_in_executor(None, verify_working)
        
        logger.info("Scheduled task completed successfully.")
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Hi! I am Vless Parser Bot.\n\n"
        "Commands:\n"
        "/parsing - run full parsing and verification\n"
        "/ping - show group stats and last recheck\n"
        "/status - show bot status and sources\n"
    )


@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    status = load_status()
    counts = status.get("group_counts", {})
    last_recheck = status.get("last_recheck", "-")
    removed = status.get("recheck_removed", "-")
    remaining = status.get("recheck_remaining", "-")

    response = (
        "Group stats:\n"
        f"1 (full access): {counts.get('group1', 0)}\n"
        f"2 (AI): {counts.get('group2', 0)}\n"
        f"3 (Google AI): {counts.get('group3', 0)}\n"
        f"4 (YouTube/Discord): {counts.get('group4', 0)}\n\n"
        f"Last recheck: {last_recheck}\n"
        f"Removed: {removed}\n"
        f"Remaining: {remaining}"
    )
    await message.answer(response)


@dp.message(Command("parsing"))
async def cmd_parsing(message: Message):
    await message.answer("Running full parsing and verification. This may take a few minutes...")
    await scheduled_task()

    files = [
        (OUTPUT_GROUP1, "Group 1 - full access"),
        (OUTPUT_GROUP2, "Group 2 - AI"),
        (OUTPUT_GROUP3, "Group 3 - Google AI"),
        (OUTPUT_GROUP4, "Group 4 - YouTube/Discord"),
    ]

    sent_any = False
    for path, caption in files:
        if os.path.exists(path):
            file = types.FSInputFile(path)
            await message.answer_document(file, caption=caption)
            sent_any = True

    if not sent_any:
        await message.answer("No subscription files created: no working keys.")

    urls = _subscription_urls()
    if urls:
        url_text = (
            "Subscription URLs:\n"
            f"1: {urls[1]}\n"
            f"2: {urls[2]}\n"
            f"3: {urls[3]}\n"
            f"4: {urls[4]}"
        )
        await message.answer(url_text)
    else:
        await message.answer("Subscription URLs are not configured (SUBS_BASE_URL is empty).")


@dp.message(Command("status"))
async def cmd_status(message: Message):
    status = load_status()
    counts = status.get("group_counts", {})
    last_verify = status.get("last_verify", "-")
    last_recheck = status.get("last_recheck", "-")

    # Sources summary
    sources_text = "-"
    try:
        from database import SessionLocal, Source
        from sqlalchemy import select
        db = SessionLocal()
        try:
            rows = db.execute(select(Source).where(Source.is_active == True)).scalars().all()
            if rows:
                sources_text = "\n".join(sorted({s.url for s in rows}))
        finally:
            db.close()
    except Exception:
        pass

    response = (
        "Bot status:\n"
        f"Last verify: {last_verify}\n"
        f"Last recheck: {last_recheck}\n\n"
        "Groups:\n"
        f"1: {counts.get('group1', 0)}\n"
        f"2: {counts.get('group2', 0)}\n"
        f"3: {counts.get('group3', 0)}\n"
        f"4: {counts.get('group4', 0)}\n\n"
        "Active sources:\n"
        f"{sources_text}"
    )
    await message.answer(response)


async def main():
    # 1. Handle DB migration if user uploaded a fresh one
    import os
    from config import DB_PATH
    if os.path.exists("vless_parser_fromhost.db") and not os.path.exists(DB_PATH + ".migrated"):
        logger.info("Found vless_parser_fromhost.db! Migration to vless_parser.db...")
        try:
            import shutil
            shutil.copyfile("vless_parser_fromhost.db", DB_PATH)
            # Mark as migrated
            with open(DB_PATH + ".migrated", "w") as f: f.write("done")
        except Exception as e:
            logger.error(f"Migration error: {e}")

    # Ensure DB is initialized
    from database import init_db
    init_db()
    
    # Ensure xray is present
    await ensure_xray_binary()
    
    # Setup Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_task, 'interval', hours=6)
    scheduler.add_job(recheck_working_groups, 'interval', hours=1)
    scheduler.start()
    
    # Pre-seed DB (with sources)
    discovery = DiscoveryModule()
    # Ensure sources are in DB
    try:
        from database import SessionLocal, Source
        db = SessionLocal()
        if not db.query(Source).filter_by(is_active=True).first():
            logger.info("No active sources in DB. Seeding from config.py...")
            await discovery.seed_initial_sources()
        db.close()
    except:
        pass
    
    logger.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
