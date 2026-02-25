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
    system = platform.system().lower()
    is_linux = system != "windows"

    # Critical fix: if we're on Linux but only have xray.exe, delete it and re-download
    if is_linux and os.path.exists("xray.exe") and not os.path.exists("xray"):
        logger.warning("Found xray.exe on Linux — this binary won't work! Deleting and downloading the Linux version...")
        os.remove("xray.exe")

    if os.path.exists(XRAY_PATH):
        logger.info(f"Xray binary found at: {XRAY_PATH}")
        return

    logger.info(f"{XRAY_PATH} not found. Attempting to download Xray-core for {system}...")

    arch = "64"  # Assume 64-bit for servers
    if system == "windows":
        filename = f"Xray-windows-{arch}.zip"
    else:
        filename = f"Xray-linux-{arch}.zip"

    url = XRAY_RELEASES + filename
    logger.info(f"Downloading from: {url}")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Download complete: {filename}")

        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(".")
        logger.info("Extraction complete.")

        if is_linux:
            os.chmod("xray", 0o755)
            logger.info("Set execute permission on xray binary.")

        os.remove(filename)
        logger.info(f"Xray-core ready at: {XRAY_PATH}")
    except Exception as e:
        logger.error(f"FATAL: Failed to download Xray-core from {url}: {e}")
        logger.error("Verification stage will be skipped.")

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
        "/get_working - Получить файл с рабочими Reality ключами"
    )

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
    # Ensure DB is initialized
    from database import init_db
    init_db()
    
    # Ensure xray is present
    await ensure_xray_binary()
    
    # Setup Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_task, 'interval', hours=6)
    scheduler.start()
    
    # Pre-seed DB
    discovery = DiscoveryModule()
    await discovery.seed_initial_sources()
    
    logger.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
