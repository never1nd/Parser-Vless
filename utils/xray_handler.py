import json
import os
import subprocess
import time
import requests
from config import XRAY_PATH, SOCKS_PORT, TEST_URL, VERIFICATION_TIMEOUT
from utils.scraper import logger

import json
import os
import subprocess
import time
import requests
from urllib.parse import urlparse, parse_qs, unquote
from config import XRAY_PATH, SOCKS_PORT, TEST_URL, VERIFICATION_TIMEOUT
from utils.scraper import logger

def parse_vless_url(url):
    """
    Parses a Vless URL into a usable dictionary.
    vless://uuid@host:port?query#fragment
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme != 'vless':
            return None
        
        # Extract UUID and Host/Port
        netloc = parsed.netloc
        if '@' not in netloc:
            return None
        
        uuid_part, address_part = netloc.split('@')
        
        if ':' in address_part:
            host, port = address_part.split(':')
            port = int(port)
        else:
            host = address_part
            port = 443
            
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        name = unquote(parsed.fragment) if parsed.fragment else "Vless-Node"
        
        return {
            "uuid": uuid_part,
            "address": host,
            "port": port,
            "params": params,
            "name": name
        }
    except Exception as e:
        logger.debug(f"Failed to parse Vless URL {url}: {e}")
        return None

def generate_xray_config(parsed_data, socks_port):
    """
    Generates Xray JSON configuration for a Vless outbound.
    """
    params = parsed_data["params"]
    security = params.get("security", "none")
    
    outbound = {
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": parsed_data["address"],
                "port": parsed_data["port"],
                "users": [{
                    "id": parsed_data["uuid"],
                    "encryption": "none",
                    "flow": params.get("flow", "")
                }]
            }]
        },
        "streamSettings": {
            "network": params.get("type", "tcp"),
            "security": security
        }
    }
    
    # Handle TLS/Reality settings
    if security == "tls":
        outbound["streamSettings"]["tlsSettings"] = {
            "serverName": params.get("sni", ""),
            "fingerprint": params.get("fp", "chrome")
        }
    elif security == "reality":
        outbound["streamSettings"]["realitySettings"] = {
            "serverName": params.get("sni", ""),
            "fingerprint": params.get("fp", "chrome"),
            "publicKey": params.get("pbk", ""),
            "shortId": params.get("sid", ""),
            "spiderX": params.get("spx", "/")
        }
        
    # Handle transport settings (ws, grpc)
    transport_type = params.get("type")
    if transport_type == "ws":
        outbound["streamSettings"]["wsSettings"] = {
            "path": params.get("path", "/"),
            "headers": {"Host": params.get("host", "")}
        }
    elif transport_type == "grpc":
        outbound["streamSettings"]["grpcSettings"] = {
            "serviceName": params.get("serviceName", "")
        }

    config = {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "port": socks_port,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"udp": True}
        }],
        "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"}]
    }
    return config

class XrayTester:
    def __init__(self, binary_path=XRAY_PATH):
        self.binary_path = binary_path
        self.process = None

    def is_binary_present(self):
        return os.path.exists(self.binary_path)

    def test_link(self, vless_url):
        if not self.is_binary_present():
            logger.warning("Xray binary not found at path: %s", self.binary_path)
            return False, "xray binary missing"
            
        data = parse_vless_url(vless_url)
        if not data:
            return False, "Invalid URL"
        
        short_url = vless_url[:60] + "..." if len(vless_url) > 60 else vless_url
        logger.debug("Testing: %s @ %s:%s", data['address'], data['address'], data['port'])
            
        config = generate_xray_config(data, SOCKS_PORT)
        config_path = f"temp_config_{SOCKS_PORT}.json"
        
        with open(config_path, "w") as f:
            json.dump(config, f)
            
        try:
            # Start Xray
            self.process = subprocess.Popen(
                [self.binary_path, "run", "-c", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for Xray to start (increased for reliability)
            time.sleep(3)
            
            # Test connection via SOCKS5 proxy
            proxies = {
                "http": f"socks5h://127.0.0.1:{SOCKS_PORT}",
                "https": f"socks5h://127.0.0.1:{SOCKS_PORT}"
            }
            
            start_time = time.time()
            response = requests.get(TEST_URL, proxies=proxies, timeout=VERIFICATION_TIMEOUT)
            latency = int((time.time() - start_time) * 1000)
            
            if response.status_code in [200, 204]:
                logger.info("✅ WORKING: %s:%s (%dms)", data['address'], data['port'], latency)
                return True, f"{latency}ms"
            logger.debug("❌ Failed: %s:%s — HTTP %s", data['address'], data['port'], response.status_code)
            return False, f"Status {response.status_code}"
            
        except Exception as e:
            logger.debug("❌ Error: %s:%s — %s", data['address'], data['port'], str(e))
            return False, str(e)
        finally:
            if self.process:
                self.process.terminate()
                self.process.wait()
            if os.path.exists(config_path):
                os.remove(config_path)
