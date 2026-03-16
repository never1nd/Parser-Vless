import os
from config import OUTPUT_PREMIUM, OUTPUT_FREE, OUTPUT_REALITY
from utils.validator import is_reality
from utils.scraper import logger
from urllib.parse import urlparse, parse_qs


def is_strict_reality(key: str) -> bool:
    """
    Returns True if key is a Reality key AND meets strict criteria:
    - security=reality
    - port=443
    - flow=xtls-rprx-vision
    """
    if not is_reality(key):
        return False
    try:
        parsed = urlparse(key)
        # Check port
        netloc = parsed.netloc
        if ':' in netloc:
            port = int(netloc.split(':')[-1])
            if port != 443:
                return False
        else:
            return False  # No port = not 443
        # Check flow param
        params = parse_qs(parsed.query)
        flow = params.get('flow', [''])[0]
        if flow != 'xtls-rprx-vision':
            return False
        return True
    except Exception:
        return False


def filter_keys():
    logger.info("--- Starting Reality Filtering Stage (strict: port=443, flow=xtls-rprx-vision) ---")
    
    # 1. Read keys from Database (Primary source)
    from database import SessionLocal, VlessKey
    from sqlalchemy import select
    
    db = SessionLocal()
    try:
        stmt = select(VlessKey.raw_url)
        all_keys = set(db.execute(stmt).scalars().all())
    finally:
        db.close()
        
    if not all_keys:
        logger.warning("No keys found in database. Checking text files as fallback...")
        input_files = [OUTPUT_PREMIUM, OUTPUT_FREE]
        for file_path in input_files:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    all_keys.update({line.strip() for line in f if line.strip()})
            
    # 2. Filter for strict Reality (port=443 AND flow=xtls-rprx-vision)
    initial_total = len(all_keys)
    reality_keys = [key for key in all_keys if is_strict_reality(key)]
    
    # 3. Mark filtered keys in DB
    if reality_keys:
        db = SessionLocal()
        try:
            from sqlalchemy import update
            # Reset all to none, then mark filtered ones
            db.execute(update(VlessKey).values(security="none"))
            for key in reality_keys:
                db.execute(update(VlessKey).where(VlessKey.raw_url == key).values(security="reality"))
            db.commit()
        except Exception as e:
            logger.error(f"Error updating DB: {e}")
            db.rollback()
        finally:
            db.close()

    # 4. Save result
    if reality_keys:
        with open(OUTPUT_REALITY, "w", encoding="utf-8") as f:
            for key in reality_keys:
                f.write(f"{key}\n")
        logger.info(f"Filtered {len(reality_keys)} strict Reality keys (port=443, xtls-rprx-vision) from {initial_total} total.")
        logger.info(f"Result saved to: {OUTPUT_REALITY}")
    else:
        logger.info("No strict Reality keys found in the source files.")

if __name__ == "__main__":
    filter_keys()
