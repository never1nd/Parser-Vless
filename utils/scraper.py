import requests
import random
import time
import logging
from config import USER_AGENTS, TIMEOUT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self):
        self.session = requests.Session()

    def get_user_agent(self):
        return random.choice(USER_AGENTS)

    def fetch(self, url):
        from config import VERIFY_SSL
        headers = {'User-Agent': self.get_user_agent()}
        try:
            response = self.session.get(url, headers=headers, timeout=TIMEOUT, verify=VERIFY_SSL)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def sleep(self, range_seconds=(5, 10)):
        duration = random.uniform(*range_seconds)
        time.sleep(duration)
