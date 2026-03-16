import json
from pathlib import Path
from utils.scraper import logger

STATUS_FILE = Path("status.json")


def load_status():
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to read status.json: %s", e)
    return {}


def update_status(**kwargs):
    data = load_status()
    data.update(kwargs)
    try:
        STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to write status.json: %s", e)
    return data
