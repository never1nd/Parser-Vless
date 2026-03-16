from datetime import datetime, timedelta
from utils.scraper import logger
from utils.validator import is_reality
from utils.xray_handler import parse_vless_url
from config import PREFILTER_MAX_RATIO, PREFILTER_MAX_AGE_HOURS


def prefilter_keys(keys, key_meta=None, max_ratio=None, max_age_hours=None):
    """
    Fast pre-filter to reduce the number of keys before Xray checks.
    - Remove duplicate UUIDs.
    - For Reality keys: require port=443 and flow=xtls-rprx-vision.
    - If discovery_date is available: drop keys older than PREFILTER_MAX_AGE_HOURS.
    - Keep only top PREFILTER_MAX_RATIO (by recency if possible).
    """
    if not keys:
        return []

    now = datetime.utcnow()
    ratio = PREFILTER_MAX_RATIO if max_ratio is None else max_ratio
    age_hours = PREFILTER_MAX_AGE_HOURS if max_age_hours is None else max_age_hours

    # Build (key, discovery_date) list and sort by newest first if dates exist
    items = []
    has_dates = False
    for k in keys:
        dt = key_meta.get(k) if key_meta else None
        if dt:
            has_dates = True
        items.append((k, dt))

    if has_dates:
        items.sort(key=lambda x: x[1] or datetime.min, reverse=True)

    filtered = []
    seen_uuid = set()

    for key, dt in items:
        data = parse_vless_url(key)
        if not data:
            continue

        uuid = data.get("uuid")
        if not uuid or uuid in seen_uuid:
            continue

        # Reality strict rules
        if is_reality(key):
            if data.get("port") != 443:
                continue
            flow = data.get("params", {}).get("flow", "")
            if flow != "xtls-rprx-vision":
                continue

        # Age filter (only if date is present)
        if dt and (now - dt) > timedelta(hours=age_hours):
            continue

        filtered.append(key)
        seen_uuid.add(uuid)

    # Limit to top ratio
    if ratio < 1.0 and filtered:
        keep = max(1, int(len(filtered) * ratio))
        filtered = filtered[:keep]

    logger.info("Prefilter: %d -> %d keys (ratio=%.2f)", len(keys), len(filtered), ratio)
    return filtered
