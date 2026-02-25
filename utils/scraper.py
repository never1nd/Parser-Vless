import requests
import random
import time
import logging
import urllib3
from config import USER_AGENTS, TIMEOUT, VERIFY_SSL

# Suppress SSL warnings for headless servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self):
        self.session = requests.Session()

    def get_user_agent(self):
        return random.choice(USER_AGENTS)

    def fetch(self, url):
        headers = {'User-Agent': self.get_user_agent()}
        try:
            response = self.session.get(url, headers=headers, timeout=TIMEOUT, verify=VERIFY_SSL)
            if response.status_code == 404:
                return "404_NOT_FOUND" 
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def sleep(self, range_seconds=(5, 10)):
        duration = random.uniform(*range_seconds)
        time.sleep(duration)
