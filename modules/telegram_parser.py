from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless
from bs4 import BeautifulSoup

class TelegramParser(BaseScraper):
    def __init__(self, client=None):
        super().__init__()
        # client arg kept for compatibility with old calls

    def parse_channels(self, channels, limit=50):
        """
        Scrapes public Telegram channels using their web view (t.me/s/username).
        Does NOT require API keys or authorization.
        """
        all_keys = set()
        for channel in channels:
            # Normalize channel name
            username = channel.strip().replace("@", "")
            url = f"https://t.me/s/{username}"
            logger.info(f"Scraping Telegram web view: {url}")
            
            try:
                html = self.fetch(url)
                if not html:
                    continue
                
                # Check for "Nobody is using this username"
                if "Nobody is using this username" in html:
                    logger.warning(f"Telegram channel @{username} not found.")
                    continue

                soup = BeautifulSoup(html, 'html.parser')
                # Message text is usually in div with class 'tgme_widget_message_text'
                messages = soup.find_all(class_='tgme_widget_message_text')
                
                for msg in messages:
                    text = msg.get_text()
                    keys = extract_vless(text)
                    all_keys.update(keys)
                
                logger.info(f"Finished web-scraping @{username}")
            except Exception as e:
                logger.error(f"Error web-scraping Telegram channel {username}: {e}")
        
        return list(all_keys)

