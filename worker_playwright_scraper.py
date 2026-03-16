"""
Optional worker for blocked forums.
Run this on a machine that can open these sites (local PC/VPS).

Requires:
  pip install playwright
  playwright install
"""
import os
from datetime import datetime
from utils.validator import extract_vless
from utils.scraper import logger
from utils.subscription_uploader import upload_files

SITES = [
    "https://lolz.live",
    "https://nodeseek.com",
    "https://ntc.party",
    "https://v2ex.com",
]

OUTPUT_FILE = os.getenv("EXTRA_FEED_FILE", "extra_feed.txt")


def _scrape_with_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        logger.error("Playwright not installed: %s", e)
        return []

    keys = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in SITES:
            try:
                logger.info("Playwright visit: %s", url)
                page.goto(url, wait_until="networkidle", timeout=45000)
                html = page.content()
                keys.update(extract_vless(html))
            except Exception as e:
                logger.warning("Playwright failed for %s: %s", url, e)
        browser.close()
    return list(keys)


def main():
    keys = _scrape_with_playwright()
    if not keys:
        logger.info("No keys found in blocked sites.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for k in keys:
            f.write(f"{k}\n")

    logger.info("Saved %d keys to %s", len(keys), OUTPUT_FILE)

    # Optional upload to InfinityFree (same FTP settings from .env)
    upload_files([OUTPUT_FILE])
    logger.info("Upload done at %s", datetime.utcnow().isoformat())


if __name__ == "__main__":
    main()
