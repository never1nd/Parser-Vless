from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless

class GitHubParser(BaseScraper):
    def parse_links(self, urls):
        all_keys = set()
        for url in urls:
            logger.info(f"Parsing GitHub raw: {url}")
            content = self.fetch(url)
            if content:
                keys = extract_vless(content)
                all_keys.update(keys)
                logger.info(f"Found {len(keys)} keys in {url}")
            self.sleep()
        return list(all_keys)
