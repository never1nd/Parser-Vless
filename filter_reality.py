import os
from config import OUTPUT_PREMIUM, OUTPUT_FREE, OUTPUT_REALITY
from utils.validator import is_reality
from utils.scraper import logger

def filter_keys():
    logger.info("--- Starting Reality Filtering Stage ---")
    
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
            
    # 2. Filter for Reality
    initial_total = len(all_keys)
    reality_keys = [key for key in all_keys if is_reality(key)]
    
    # 3. Save result
    if reality_keys:
        with open(OUTPUT_REALITY, "w", encoding="utf-8") as f:
            for key in reality_keys:
                f.write(f"{key}\n")
        logger.info(f"Filtered {len(reality_keys)} Reality keys from {initial_total} unique source keys.")
        logger.info(f"Result saved to: {OUTPUT_REALITY}")
    else:
        logger.info("No Reality keys found in the source files.")

if __name__ == "__main__":
    filter_keys()
