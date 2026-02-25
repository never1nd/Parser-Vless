import os
from config import OUTPUT_PREMIUM, OUTPUT_FREE, OUTPUT_WORKING, XRAY_PATH
from utils.xray_handler import XrayTester
from utils.scraper import logger

def verify_working():
    tester = XrayTester()
    
    if not tester.is_binary_present():
        logger.error(f"FATAL: {XRAY_PATH} not found in the project directory!")
        logger.info("Please download Xray-core from: https://github.com/XTLS/Xray-core/releases")
        return

    logger.info("--- Starting Deep Verification Stage (Reality Only) ---")
    
    from config import OUTPUT_REALITY
    input_files = [OUTPUT_REALITY]
    all_keys = set()
    
    for file_path in input_files:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                all_keys.update([line.strip() for line in f if line.strip()])

    total = len(all_keys)
    logger.info(f"Loaded {total} unique keys for testing...")
    
    working_keys = []
    
    for i, key in enumerate(all_keys, 1):
        # Using a simple progress indicator
        print(f"Testing key {i}/{total}...", end="\r")
        
        success, info = tester.test_link(key)
        if success:
            logger.info(f"[WORKING] {info} | {key[:50]}...")
            working_keys.append(key)
        else:
            # logger.debug(f"[FAILED] {info} | {key[:50]}...")
            pass

    print("\n")
    if working_keys:
        with open(OUTPUT_WORKING, "w", encoding="utf-8") as f:
            for key in working_keys:
                f.write(f"{key}\n")
        logger.info(f"Verification finished! Saved {len(working_keys)} WORKING keys to {OUTPUT_WORKING}")
    else:
        logger.warning("No working keys found after full verification.")

if __name__ == "__main__":
    verify_working()
