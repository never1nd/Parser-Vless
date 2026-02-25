import os
from config import OUTPUT_PREMIUM, OUTPUT_FREE, OUTPUT_REALITY
from utils.validator import is_reality
from utils.scraper import logger

def filter_keys():
    logger.info("--- Starting Reality Filtering Stage ---")
    
    input_files = [OUTPUT_PREMIUM, OUTPUT_FREE]
    all_keys = set()
    
    # 1. Read keys from existing files
    for file_path in input_files:
        if os.path.exists(file_path):
            logger.info(f"Reading keys from {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                initial_count = len(lines)
                keys = {line.strip() for line in lines if line.strip()}
                all_keys.update(keys)
                dupes = initial_count - len(keys)
                if dupes > 0:
                    logger.info(f"Removed {dupes} internal duplicates from {file_path}")
        else:
            logger.warning(f"File {file_path} not found. Run main.py first.")
            
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
