from bs4 import BeautifulSoup
from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless

class WebParser(BaseScraper):
    def parse_sites(self, urls):
        all_keys = set()
        for url in urls:
            logger.info(f"Parsing Web site: {url}")
            html = self.fetch(url)
            if html:
                # First try direct regex on HTML (many keys are in plain text or scripts)
                keys = extract_vless(html)
                
                # If no keys found, try parsing typical containers
                if not keys:
                    soup = BeautifulSoup(html, 'html.parser')
                    # Look for <code> or <pre> tags which often contain configs
                    for tag in soup.find_all(['code', 'pre', 'div']):
                        keys.extend(extract_vless(tag.get_text()))
                
                significant_keys = set(keys)
                all_keys.update(significant_keys)
                logger.info(f"Found {len(significant_keys)} potential keys in {url}")
            self.sleep()
        return list(all_keys)
