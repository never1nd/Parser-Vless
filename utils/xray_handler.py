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
            host_port = address_part.split(':')
            host = host_port[0]
            port = int(host_port[1])
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

    def is_binary_present(self):
        return os.path.exists(self.binary_path)

    def test_link(self, vless_url, port=SOCKS_PORT):
        """
        Tests a Vless link using Xray.
        Port can be specified for parallel testing.
        """
        if not self.is_binary_present():
            logger.warning("Xray binary not found at path: %s", self.binary_path)
            return False, "xray binary missing"
            
        data = parse_vless_url(vless_url)
        if not data:
            return False, "Invalid URL"
        
        logger.debug("Testing: %s @ %s:%s on SOCKS port %d", 
                     data['address'], data['address'], data['port'], port)
            
        config = generate_xray_config(data, port)
        config_path = f"temp_config_{port}.json"
        
        with open(config_path, "w") as f:
            json.dump(config, f)
            
        process = None
        try:
            # Start Xray
            process = subprocess.Popen(
                [self.binary_path, "run", "-c", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for Xray to start
            time.sleep(2)
            
            # Test connection via SOCKS5 proxy
            proxies = {
                "http": f"socks5h://127.0.0.1:{port}",
                "https": f"socks5h://127.0.0.1:{port}"
            }
            
            start_time = time.time()
            response = requests.get(TEST_URL, proxies=proxies, timeout=VERIFICATION_TIMEOUT)
            latency = int((time.time() - start_time) * 1000)
            
            if response.status_code in [200, 204]:
                logger.info("✅ WORKING: %s:%s (%dms)", data['address'], data['port'], latency)
                return True, f"{latency}ms"
            logger.warning("❌ Failed: %s:%s — HTTP %s", data['address'], data['port'], response.status_code)
            return False, f"Status {response.status_code}"
            
        except Exception as e:
            logger.warning("❌ Error: %s:%s — %s", data['address'], data['port'], str(e))
            return False, str(e)
        finally:
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                except:
                    pass

    def test_link_multi_site(self, vless_url, port=SOCKS_PORT):
        """
        Tests a Vless link against multiple sites.
        Returns a dict: { site_name: True/False }
        Sites: youtube, discord, gemini, ai_studio, chatgpt, claude
        """
        SITES = {
            "youtube":   "https://www.youtube.com/generate_204",
            "discord":   "https://discord.com/favicon.ico",
            "gemini":    "https://gemini.google.com/favicon.ico",
            "ai_studio": "https://aistudio.google.com/favicon.ico",
            "chatgpt":   "https://chat.openai.com/favicon.ico",
            "claude":    "https://claude.ai/favicon.ico",
        }

        if not self.is_binary_present():
            logger.warning("Xray binary not found at path: %s", self.binary_path)
            return {k: False for k in SITES}

        data = parse_vless_url(vless_url)
        if not data:
            return {k: False for k in SITES}

        config = generate_xray_config(data, port)
        config_path = f"temp_config_{port}.json"

        with open(config_path, "w") as f:
            json.dump(config, f)

        process = None
        results = {k: False for k in SITES}
        try:
            process = subprocess.Popen(
                [self.binary_path, "run", "-c", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)

            proxies = {
                "http":  f"socks5h://127.0.0.1:{port}",
                "https": f"socks5h://127.0.0.1:{port}",
            }

            for name, url in SITES.items():
                try:
                    resp = requests.get(url, proxies=proxies, timeout=VERIFICATION_TIMEOUT, allow_redirects=True)
                    results[name] = resp.status_code < 500
                except Exception:
                    results[name] = False

            passing = [k for k, v in results.items() if v]
            logger.info("MultiSite %s:%s → %s", data['address'], data['port'], passing or "none")
        except Exception as e:
            logger.warning("MultiSite Error: %s:%s — %s", data.get('address','?'), data.get('port','?'), e)
        finally:
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                except:
                    pass

        return results
