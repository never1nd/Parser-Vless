import re
import socket
from urllib.parse import urlparse

# Vless Regex Pattern
VLESS_PATTERN = r"vless:\/\/[^\s\'\"]+"

# Telegram Pattern (matches t.me/username and telegram.me/username)
TELEGRAM_PATTERN = r"(?:https?:\/\/)?t(?:elegram)?\.me\/([a-zA-Z0-9_]{5,})"

# Vless Regex Pattern - optimized to avoid trailing backticks/markdown
VLESS_PATTERN = r"vless:\/\/[^ \s\'\"`]+"

def extract_vless(text):
    """Extracts all vless links from text and cleans them."""
    if not text:
        return []
    raw_links = re.findall(VLESS_PATTERN, text)
    # Final cleanup: trim any trailing punctuation that regex might have grabbed
    clean_links = [link.strip("`.,() ") for link in raw_links]
    return [l for l in clean_links if "vless://" in l]

def extract_telegram_links(text):
    """Extracts telegram usernames/links from text."""
    if not text:
        return []
    # Find all matches and return the usernames
    return list(set(re.findall(TELEGRAM_PATTERN, text)))

def validate_vless(vless_url):
    """
    Simple validation: checks structure. 
    Socket check disabled as it's too slow for large lists.
    Full verification is handled by the XrayTester stage.
    """
    try:
        parsed = urlparse(vless_url)
        return parsed.scheme == "vless" and "@" in parsed.netloc
    except Exception:
        return False

def is_reality(vless_url):
    """Checks if the vless URL uses security=reality."""
    return "security=reality" in vless_url.lower()
