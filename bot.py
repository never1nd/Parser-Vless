import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, OUTPUT_WORKING
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

async def scheduled_task():
    logger.info("Starting scheduled 6-hour task...")
    try:
        # Phase 1: Discovery (Continuous but here we trigger a burst)
        discovery = DiscoveryModule()
        loop = asyncio.get_running_loop()
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
        "👋 Привет! Я Vless Parser Bot.\n\n"
        "Я работаю 24/7:\n"
        "🔍 Ищу новые источники\n"
        "🧹 Удаляю дубликаты\n"
        "⚡ Проверяю ключи на скорость\n\n"
        "Команды:\n"
        "/parsing - Запустить полный цикл проверки прямо сейчас\n"
        "/ping - Проверить задержку существующих Reality ключей\n"
        "/get_working - Получить файл с рабочими Reality ключами"
    )

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    await message.answer("⚡ Проверяю текущие Reality ключи на задержку...")
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, verify_working)
    
    # Fetch top 10 working keys from DB
    from database import SessionLocal, VlessKey
    from sqlalchemy import select
    
    db = SessionLocal()
    try:
        # Total count of reality keys
        from sqlalchemy import func
        total_reality = db.query(func.count(VlessKey.id)).filter(VlessKey.security == 'reality').scalar()
        
        stmt = select(VlessKey).where(VlessKey.is_working == True).order_by(VlessKey.latency.asc()).limit(10)
        working = db.execute(stmt).scalars().all()
    finally:
        db.close()
        
    if working:
        response = f"✅ **Топ рабочих серверов (из {total_reality} в базе):**\n\n"
        for i, k in enumerate(working, 1):
            response += f"{i}. ⚡ {k.latency}ms\n`{k.raw_url}`\n\n"
        await message.answer(response, parse_mode="Markdown")
    else:
        await message.answer(f"❌ Рабочих ключей не найдено. Всего в базе {total_reality} Reality ключей.\nПопробуйте /parsing для поиска новых.")

@dp.message(Command("parsing"))
async def cmd_parsing(message: Message):
    await message.answer("🚀 Запускаю полный цикл парсинга и проверки. Это может занять несколько минут...")
    await scheduled_task()
    
    if os.path.exists(OUTPUT_WORKING):
        await message.answer("✅ Парсинг завершен!")
        file = types.FSInputFile(OUTPUT_WORKING)
        await message.answer_document(file, caption="Актуальный список рабочих ключей.")
    else:
        await message.answer("❌ К сожалению, рабочих ключей не найдено.")

@dp.message(Command("get_working"))
async def cmd_get(message: Message):
    if os.path.exists(OUTPUT_WORKING):
        file = types.FSInputFile(OUTPUT_WORKING)
        await message.answer_document(file, caption="Список проверенных Reality ключей.")
    else:
        await message.answer("Файл с рабочими ключами еще не создан. Запустите /parsing")

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
