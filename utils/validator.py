import re
import socket
from urllib.parse import urlparse

# Vless Regex Pattern
VLESS_PATTERN = r"vless:\/\/[^\s\'\"]+"

# Telegram Pattern (matches t.me/username and telegram.me/username)
TELEGRAM_PATTERN = r"(?:https?:\/\/)?t(?:elegram)?\.me\/([a-zA-Z0-9_]{5,})"

def extract_vless(text):
    """Extracts all vless links from text."""
    if not text:
        return []
    return re.findall(VLESS_PATTERN, text)

def extract_telegram_links(text):
    """Extracts telegram usernames/links from text."""
    if not text:
        return []
    # Find all matches and return the usernames
    return list(set(re.findall(TELEGRAM_PATTERN, text)))

def validate_vless(vless_url):
    """
    Simple validation: tries to resolve the host address to check if it's reachable.
    Note: A full ping or xray connection check would be more robust but requires additional dependencies or OS calls.
    """
    try:
        parsed = urlparse(vless_url)
        # Handle cases where the format might be vless://uuid@host:port...
        netloc = parsed.netloc
        if '@' in netloc:
            host_port = netloc.split('@')[1]
        else:
            host_port = netloc

        if ':' in host_port:
            host = host_port.split(':')[0]
            port = int(host_port.split(':')[1])
        else:
            host = host_port
            port = 443 # Default SSL port

        # Simple socket connection check to see if the port is open
        with socket.create_connection((host, port), timeout=3):
            return True
    except Exception:
        return False

def is_reality(vless_url):
    """Checks if the vless URL uses security=reality."""
    return "security=reality" in vless_url.lower()
