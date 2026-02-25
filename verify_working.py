from concurrent.futures import ThreadPoolExecutor
import os
from config import OUTPUT_PREMIUM, OUTPUT_FREE, OUTPUT_WORKING, XRAY_PATH, SOCKS_PORT
from utils.xray_handler import XrayTester
from utils.scraper import logger

def test_single_key(args):
    key, port = args
    tester = XrayTester()
    
    try:
        success, info = tester.test_link(key, port=port)
        latency = None
        if success and "ms" in info:
            try:
                latency = int(info.replace("ms", ""))
            except:
                pass
        return {"key": key, "success": success, "latency": latency}
    except Exception as e:
        logger.error(f"Error testing key: {e}")
        return {"key": key, "success": False, "latency": None}

def update_db_results(results):
    """Updates the database with verification results."""
    from database import SessionLocal, VlessKey
    from sqlalchemy import update
    from datetime import datetime
    
    db = SessionLocal()
    try:
        for res in results:
            stmt = update(VlessKey).where(VlessKey.raw_url == res["key"]).values(
                is_working=res["success"],
                latency=res["latency"],
                last_check=datetime.utcnow()
            )
            db.execute(stmt)
        db.commit()
    except Exception as e:
        logger.error(f"Error updating DB results: {e}")
        db.rollback()
    finally:
        db.close()

def verify_working():
    tester = XrayTester()
    
    if not tester.is_binary_present():
        logger.error(f"FATAL: {XRAY_PATH} not found in the project directory!")
        logger.info("Please download Xray-core from: https://github.com/XTLS/Xray-core/releases")
        return

    logger.info("--- Starting Deep Verification Stage (Reality Only) ---")
    
    # 1. Read keys from Database (Primary source)
    from database import SessionLocal, VlessKey
    from sqlalchemy import select
    
    db = SessionLocal()
    all_keys = set()
    try:
        # Load Reality keys from DB
        stmt = select(VlessKey.raw_url).where(VlessKey.security == "reality")
        all_keys = set(db.execute(stmt).scalars().all())
    finally:
        db.close()
        
    if not all_keys:
        logger.warning("No Reality keys found in database. Checking text files as fallback...")
        from config import OUTPUT_REALITY
        if os.path.exists(OUTPUT_REALITY):
            with open(OUTPUT_REALITY, "r", encoding="utf-8") as f:
                all_keys.update([line.strip() for line in f if line.strip()])

    total = len(all_keys)
    if total == 0:
        logger.warning("No Reality keys found for verification.")
        return

    logger.info(f"Loaded {total} unique keys for testing...")
    
    working_keys = []
    max_workers = 10
    
    # Create arguments for each worker: (key, unique_port)
    # We use a range of ports starting from SOCKS_PORT
    test_args = [(key, SOCKS_PORT + (i % max_workers)) for i, key in enumerate(all_keys)]
    
    logger.info(f"Starting parallel verification with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(test_single_key, test_args))
    
    # 2. Update Database with ALL results
    update_db_results(results)
    
    # 3. Filter working keys for the .txt export
    working_keys = [res["key"] for res in results if res["success"]]

    if working_keys:
        with open(OUTPUT_WORKING, "w", encoding="utf-8") as f:
            for key in working_keys:
                f.write(f"{key}\n")
        logger.info(f"Verification finished! Saved {len(working_keys)} WORKING keys to DB and {OUTPUT_WORKING}")
    else:
        logger.warning("No working keys found after full verification.")

if __name__ == "__main__":
    verify_working()
