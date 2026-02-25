from bs4 import BeautifulSoup
from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless

class WebParser(BaseScraper):
    def parse_sites(self, urls):
        all_keys = set()
        for url in urls:
            # For trackers, we might want to target search results if it's just the base URL
            target_url = url
            if "rutracker" in url or "maintracker" in url or "rutoro" in url:
                if url.endswith('/') or len(url.split('/')) <= 3:
                     # This is just a placeholder idea, real logic would need specific search paths
                     # For now we'll stick to the provided URLs but improve extraction
                     pass
            
            logger.info(f"Parsing Web site: {target_url}")
            html = self.fetch(target_url)
            if html:
                # Direct regex on full HTML (most efficient)
                keys = extract_vless(html)
                
                # BS4 for hidden or structured content
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check <code>, <pre>, <a> (href), and <div> text
                tags_to_check = soup.find_all(['code', 'pre', 'a', 'div', 'span', 'p'])
                for tag in tags_to_check:
                    # Check text content
                    text_keys = extract_vless(tag.get_text())
                    keys.extend(text_keys)
                    
                    # Check href if it's an anchor
                    if tag.name == 'a' and tag.has_attr('href'):
                        href_keys = extract_vless(tag['href'])
                        keys.extend(href_keys)
                
                significant_keys = set(keys)
                all_keys.update(significant_keys)
                logger.info(f"Found {len(significant_keys)} potential keys in {target_url}")
            self.sleep()
        return list(all_keys)
