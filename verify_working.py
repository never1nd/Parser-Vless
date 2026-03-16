from concurrent.futures import ThreadPoolExecutor
import os
import base64
from datetime import datetime

from config import (
    OUTPUT_REALITY,
    OUTPUT_GROUP1,
    OUTPUT_GROUP2,
    OUTPUT_GROUP3,
    OUTPUT_GROUP4,
    XRAY_PATH,
    SOCKS_PORT,
)
from utils.xray_handler import XrayTester
from utils.scraper import logger
from preflight_filter import prefilter_keys
from utils.status_store import update_status
from utils.subscription_uploader import upload_files


ALL_SITES = ["youtube", "discord", "gemini", "ai_studio", "chatgpt", "claude"]
AI_SITES = ["gemini", "ai_studio", "chatgpt", "claude"]
GOOGLE_AI_SITES = ["gemini", "ai_studio"]
SOCIAL_SITES = ["youtube", "discord"]


def assign_group(results):
    """
    Assigns a group based on multi-site check results.
    Returns 1..4, or 0 if not matched.
    """
    if all(results.get(s) for s in ALL_SITES):
        return 1
    if all(results.get(s) for s in AI_SITES):
        return 2
    if all(results.get(s) for s in GOOGLE_AI_SITES):
        return 3
    if all(results.get(s) for s in SOCIAL_SITES):
        return 4
    return 0


def test_single_key(args):
    key, port = args
    tester = XrayTester()
    try:
        results = tester.test_link_multi_site(key, port=port)
        group = assign_group(results)
        return {"key": key, "group": group, "results": results}
    except Exception as e:
        logger.error("Error testing key: %s", e)
        return {"key": key, "group": 0, "results": {}}


def _update_db_results(results):
    """Updates the database with verification results."""
    from database import SessionLocal, VlessKey
    from sqlalchemy import update

    db = SessionLocal()
    try:
        for res in results:
            is_working = res["group"] > 0
            stmt = update(VlessKey).where(VlessKey.raw_url == res["key"]).values(
                is_working=is_working,
                key_group=res["group"],
                last_check=datetime.utcnow(),
            )
            db.execute(stmt)
        db.commit()
    except Exception as e:
        logger.error("Error updating DB results: %s", e)
        db.rollback()
    finally:
        db.close()


def _write_group_file(path, keys):
    data = "\n".join(keys).encode("utf-8")
    encoded = base64.b64encode(data).decode("utf-8")
    with open(path, "w", encoding="utf-8") as f:
        f.write(encoded)

def verify_keys(keys, key_meta=None, prefilter_ratio=None):
    """
    Core verification flow for a given list of keys.
    Returns (groups, stats).
    """
    total = len(keys)
    if total == 0:
        return {1: [], 2: [], 3: [], 4: []}, {"total": 0, "after_prefilter": 0}

    filtered = prefilter_keys(keys, key_meta=key_meta or {}, max_ratio=prefilter_ratio)
    if not filtered:
        return {1: [], 2: [], 3: [], 4: []}, {"total": total, "after_prefilter": 0}

    logger.info("Loaded %d keys, %d after prefilter.", total, len(filtered))

    max_workers = 10
    test_args = [(key, SOCKS_PORT + (i % max_workers)) for i, key in enumerate(filtered)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(test_single_key, test_args))

    _update_db_results(results)

    groups = {1: [], 2: [], 3: [], 4: []}
    for res in results:
        if res["group"] in groups:
            groups[res["group"]].append(res["key"])

    return groups, {"total": total, "after_prefilter": len(filtered)}


def verify_working():
    tester = XrayTester()

    if not tester.is_binary_present():
        logger.error("FATAL: %s not found in the project directory!", XRAY_PATH)
        logger.info("Please download Xray-core from: https://github.com/XTLS/Xray-core/releases")
        return

    logger.info("--- Starting Deep Verification Stage (Reality Only, Multi-Site) ---")

    # 1. Read keys from Database (Primary source)
    from database import SessionLocal, VlessKey
    from sqlalchemy import select

    db = SessionLocal()
    keys = []
    key_meta = {}
    try:
        stmt = select(VlessKey.raw_url, VlessKey.discovery_date).where(VlessKey.security == "reality")
        rows = db.execute(stmt).all()
        for raw_url, discovery_date in rows:
            keys.append(raw_url)
            key_meta[raw_url] = discovery_date
    finally:
        db.close()

    if not keys:
        logger.warning("No Reality keys found in database. Checking text files as fallback...")
        if os.path.exists(OUTPUT_REALITY):
            with open(OUTPUT_REALITY, "r", encoding="utf-8") as f:
                keys = [line.strip() for line in f if line.strip()]

    if not keys:
        logger.warning("No Reality keys found for verification.")
        return

    groups, stats = verify_keys(keys, key_meta=key_meta)
    if stats["after_prefilter"] == 0:
        logger.warning("All keys filtered out before Xray verification.")
        return

    # Write base64 subscription files
    _write_group_file(OUTPUT_GROUP1, groups[1])
    _write_group_file(OUTPUT_GROUP2, groups[2])
    _write_group_file(OUTPUT_GROUP3, groups[3])
    _write_group_file(OUTPUT_GROUP4, groups[4])

    logger.info(
        "Verification finished! Groups: g1=%d g2=%d g3=%d g4=%d",
        len(groups[1]), len(groups[2]), len(groups[3]), len(groups[4]),
    )

    update_status(
        last_verify=datetime.utcnow().isoformat(),
        group_counts={
            "group1": len(groups[1]),
            "group2": len(groups[2]),
            "group3": len(groups[3]),
            "group4": len(groups[4]),
        },
        last_verify_total=stats["total"],
        last_verify_after_prefilter=stats["after_prefilter"],
    )

    upload_files([OUTPUT_GROUP1, OUTPUT_GROUP2, OUTPUT_GROUP3, OUTPUT_GROUP4])


if __name__ == "__main__":
    verify_working()
