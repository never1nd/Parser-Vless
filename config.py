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

# Xray Verification Settings
import sys
XRAY_PATH = "xray" if sys.platform != "win32" else "xray.exe"

# Search Channels Configuration
CHANNELS = {
    "premium": {
        "github": [
            "https://raw.githubusercontent.com/vorz1k/v2box/master/v2box.txt",
            "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/master/configs.txt",
            "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
            "https://raw.githubusercontent.com/vveg26/free-v2ray-configs/main/v2ray_sub.txt",
            "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/vless.txt",
            "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/master/All_Configs_Sub.txt",
            "https://raw.githubusercontent.com/LonUp/NodeList/main/V2RayCloud",
            "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/vless.txt"
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
            "https://safe-vpn.tech/vless-configs/",
            "https://vlesskey.com/",
            "https://listvpn.net/free-vless-v2ray-servers"
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
            "Vless_Vmess_Trojan"
        ],
        "web": [
            "https://v2nodes.com/",
            "https://lncn.org/",
            "https://free-v2ray.com/",
            "https://sshs8.com/vless",
            "https://vpnjantit.com/free-v2ray-vless",
            "https://vpnhack.com/vless-config"
        ]
    }
}

# Xray Verification Settings (Moved up)
# XRAY_PATH defined above
TEST_URL = "http://cp.cloudflare.com/generate_204"
SOCKS_PORT = 10808
VERIFICATION_TIMEOUT = 2

# Output files
OUTPUT_PREMIUM = "premium_vless.txt"
OUTPUT_FREE = "free_vless.txt"
OUTPUT_REALITY = "vless-reality.txt"
OUTPUT_WORKING = "working_vless.txt"

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
