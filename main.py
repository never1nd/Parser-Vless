
import asyncio
import logging
from bot import main as start_bot

# This main.py now acts as a redirect to bot.py
# This ensures compatibility with hostings that default to main.py

if __name__ == "__main__":
    logging.info("Main.py started. Redirecting to Bot loop...")
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
