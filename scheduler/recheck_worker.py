import os
import base64
from datetime import datetime

from config import OUTPUT_GROUP1, OUTPUT_GROUP2, OUTPUT_GROUP3, OUTPUT_GROUP4
from utils.scraper import logger
from utils.status_store import update_status
from utils.subscription_uploader import upload_files
from verify_working import verify_keys, _write_group_file


def _read_group_file(path):
    if not os.path.exists(path):
        return []
    content = open(path, "r", encoding="utf-8").read().strip()
    if not content:
        return []
    try:
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning("Failed to decode %s: %s", path, e)
        return []
    return [line.strip() for line in decoded.splitlines() if line.strip()]


def recheck_working_groups():
    logger.info("--- Hourly Recheck: Start ---")

    group_files = [OUTPUT_GROUP1, OUTPUT_GROUP2, OUTPUT_GROUP3, OUTPUT_GROUP4]
    keys = []
    for path in group_files:
        keys.extend(_read_group_file(path))

    total_before = len(set(keys))
    if total_before == 0:
        logger.info("No keys found in working_group files. Skipping recheck.")
        return

    # Load discovery_date meta for prefilter (optional)
    key_meta = {}
    try:
        from database import SessionLocal, VlessKey
        from sqlalchemy import select
        db = SessionLocal()
        try:
            stmt = select(VlessKey.raw_url, VlessKey.discovery_date).where(VlessKey.raw_url.in_(set(keys)))
            for raw_url, discovery_date in db.execute(stmt).all():
                key_meta[raw_url] = discovery_date
        finally:
            db.close()
    except Exception as e:
        logger.warning("Meta lookup failed: %s", e)

    groups, stats = verify_keys(list(set(keys)), key_meta=key_meta, prefilter_ratio=1.0)

    # Rewrite group files
    _write_group_file(OUTPUT_GROUP1, groups[1])
    _write_group_file(OUTPUT_GROUP2, groups[2])
    _write_group_file(OUTPUT_GROUP3, groups[3])
    _write_group_file(OUTPUT_GROUP4, groups[4])

    total_after = len(groups[1]) + len(groups[2]) + len(groups[3]) + len(groups[4])
    removed = max(0, total_before - total_after)

    logger.info("Recheck done. Removed %d keys, remaining %d.", removed, total_after)

    update_status(
        last_recheck=datetime.utcnow().isoformat(),
        recheck_removed=removed,
        recheck_remaining=total_after,
        last_recheck_total_before=total_before,
        last_recheck_after_prefilter=stats["after_prefilter"],
    )

    upload_files([OUTPUT_GROUP1, OUTPUT_GROUP2, OUTPUT_GROUP3, OUTPUT_GROUP4])


if __name__ == "__main__":
    recheck_working_groups()
