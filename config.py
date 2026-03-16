import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API (User Account for Telethon)
API_ID = int(os.getenv("API_ID")) if os.getenv("API_ID") else None
API_HASH = os.getenv("API_HASH")

# Telegram Bot API (Managed by aiogram)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database
DB_PATH = "vless_parser.db"

# Subscription (public URLs) + FTP upload
SUBS_BASE_URL = os.getenv("SUBS_BASE_URL", "").rstrip("/")
SUBS_SECRET = os.getenv("SUBS_SECRET", "change_me")
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_PORT = int(os.getenv("FTP_PORT", "21"))
FTP_DIR = os.getenv("FTP_DIR", f"/htdocs/subs/{SUBS_SECRET}")
ENABLE_FTP_UPLOAD = os.getenv("ENABLE_FTP_UPLOAD", "1") == "1"

# Feature toggles
ENABLE_DISCOVERY = os.getenv("ENABLE_DISCOVERY", "0") == "1"
ENABLE_AUTO_TG_DISCOVERY = os.getenv("ENABLE_AUTO_TG_DISCOVERY", "0") == "1"

# External feeds (plain text or base64 subscriptions)
EXTRA_FEEDS_ENABLED = os.getenv("EXTRA_FEEDS_ENABLED", "0") == "1"
EXTRA_FEEDS_URLS = [
    u.strip()
    for u in os.getenv("EXTRA_FEEDS_URLS", "").split(",")
    if u.strip()
]

# Xray Verification Settings
import sys
XRAY_PATH = "./xray" if sys.platform != "win32" else "xray.exe"

# Search Channels Configuration
CHANNELS = {
    "premium": {
        "github": [
            "https://raw.githubusercontent.com/vorz1k/v2box/master/v2box.txt",
            "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/master/configs.txt",
            "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
            "https://raw.githubusercontent.com/vveg26/free-v2ray-configs/main/v2ray_sub.txt",
            "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/Splitted-By-Protocol/vless.txt",
            "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/vless.txt",
            "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/subs/sub1.txt",
            "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vless.txt",
            "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/vless.txt"
        ],
        "telegram": [
            "supreme_vpns",
            "vpnstashbot",
            "vlesstrojan",
            "v2box_configs",
            "vpn_reseller_vless",
            "VlessPremium",
            "V2RayRootFree",
            "stretten",
            "hackkcahvpn_grupo",
            "PrivateVless",
            "PremiumVpnKeys"
        ],
        "web": [
            "https://www.reddit.com/r/v2ray/",
            "https://vlesskey.com/",
            "https://listvpn.net/free-vless-v2ray-servers",
            "https://rutracker.net/forum/viewforum.php?f=1649",
            "https://rutracker.net/forum/viewforum.php?f=1958",
            "https://rutracker.net/forum/viewforum.php?f=659",
            "https://maintracker.org/forum/viewforum.php?f=1649",
            "https://rutoro.info/lastnews"
        ]
    },
    "free": {
        "github": [
            "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/master/vless",
            "https://raw.githubusercontent.com/miladtahanian/Config-Collector/main/sub/vless",
            "https://raw.githubusercontent.com/freefq/free/master/v2ray",
            "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
            "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/v2ray.txt",
            "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/list.txt",
            "https://raw.githubusercontent.com/bannedbook/fanqiang/master/v2ray/vless.txt",
            "https://raw.githubusercontent.com/ssrsub/ssr/master/vless.txt",
            "https://raw.githubusercontent.com/v2ray-free/free/master/vless",
            "https://raw.githubusercontent.com/Paw0-o/V2ray-Configs/main/Splited-Configs/vless.txt"
        ],
        "telegram": [
            "VlessVpnFree",
            "ALIILAPRO_Config",
            "vlesskeys",
            "proxy_free_vpn",
            "ShadowSocks_Free",
            "v2ray_free_conf",
            "Configs_Free",
            "VlessConfigs",
            "FreeV2rayConfig",
            "Vpn_Free_Config",
            "Vless_Vmess_Trojan",
            "sshs8com",
            "VPNHackGroup",
            "v2nodes"
        ],
        "web": [
            "https://v2nodes.com/",
            "https://sshs8.com/vless",
            "https://vpnjantit.com/free-v2ray-vless",
            "https://vpnhack.com/vless-config",
            "https://lolz.live",
            "https://ntc.party",
            "https://nodeseek.com",
            "https://v2ex.com"
        ]
    }
}

# Xray Verification Settings (Moved up)
# XRAY_PATH defined above
TEST_URL = "http://cp.cloudflare.com/generate_204"
SOCKS_PORT = 10808
VERIFICATION_TIMEOUT = 10

# Output files
OUTPUT_PREMIUM = "premium_vless.txt"
OUTPUT_FREE = "free_vless.txt"
OUTPUT_REALITY = "vless-reality.txt"
OUTPUT_WORKING = "working_vless.txt"
OUTPUT_GROUP1 = "working_group1.txt"
OUTPUT_GROUP2 = "working_group2.txt"
OUTPUT_GROUP3 = "working_group3.txt"
OUTPUT_GROUP4 = "working_group4.txt"

# Scraper Settings
VERIFY_SSL = False # Change to True if you fix the local SSL issue

# Scraper Settings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

TIMEOUT = 10
RANDOM_SLEEP = (5, 10)

# Prefilter settings
PREFILTER_MAX_RATIO = float(os.getenv("PREFILTER_MAX_RATIO", "0.3"))
PREFILTER_MAX_AGE_HOURS = int(os.getenv("PREFILTER_MAX_AGE_HOURS", "48"))

# Reality ports allowed for filtering
REALITY_ALLOWED_PORTS = [
    int(p.strip())
    for p in os.getenv("REALITY_ALLOWED_PORTS", "443,8443,9443,1080").split(",")
    if p.strip().isdigit()
]
