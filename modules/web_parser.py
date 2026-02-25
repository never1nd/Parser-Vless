from bs4 import BeautifulSoup
from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless

class WebParser(BaseScraper):
    def parse_sites(self, urls):
        all_keys = set()
        discovered_telegram = set()
        
        for url in urls:
            logger.info(f"Parsing Web site: {url}")
            html = self.fetch(url)
            if not html:
                continue

            # Check if this is a forum section (viewforum.php)
            if "viewforum.php" in url:
                topic_urls = self._extract_topic_links(html, url)
                logger.info(f"Forum section detected! Found {len(topic_urls)} potential topics to crawl.")
                
                # Crawl each topic
                for t_url in topic_urls:
                    t_html = self.fetch(t_url)
                    if t_html:
                        keys, tg_links = self._extract_from_html(t_html)
                        all_keys.update(keys)
                        discovered_telegram.update(tg_links)
                    self.sleep((2, 5))
            else:
                # Regular page parsing
                keys, tg_links = self._extract_from_html(html)
                all_keys.update(keys)
                discovered_telegram.update(tg_links)
            
            self.sleep()
            
        # If new telegram sources were discovered, we might want to pass them back
        # However, for now, we'll log them and they'll be processed by discovery module
        # if we modify the pipeline to handle them.
        if discovered_telegram:
            logger.info(f"Discovered {len(discovered_telegram)} potential new Telegram sources from web: {discovered_telegram}")
            self._save_discovered_telegram(discovered_telegram)

        return list(all_keys)

    def _extract_topic_links(self, html, base_url):
        """Extracts viewtopic.php links from a viewforum page."""
        from urllib.parse import urljoin
        soup = BeautifulSoup(html, 'html.parser')
        topic_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "viewtopic.php?t=" in href:
                # Use urljoin to handle all relative formats correctly
                full_url = urljoin(base_url, href)
                topic_links.add(full_url)
        return list(topic_links)[:10]

    def _extract_from_html(self, html):
        """Extracts both Vless keys and Telegram links from HTML."""
        from utils.validator import extract_telegram_links
        keys = extract_vless(html)
        
        # Deep extraction from tags
        soup = BeautifulSoup(html, 'html.parser')
        tags_to_check = soup.find_all(['code', 'pre', 'a', 'div', 'span', 'p'])
        
        tg_links = set()
        for tag in tags_to_check:
            text = tag.get_text()
            keys.extend(extract_vless(text))
            tg_links.update(extract_telegram_links(text))
            
            if tag.name == 'a' and tag.has_attr('href'):
                keys.extend(extract_vless(tag['href']))
                tg_links.update(extract_telegram_links(tag['href']))
                
        return set(keys), tg_links

    def _save_discovered_telegram(self, usernames):
        """Saves discovered telegram usernames to the database as new free sources."""
        from database import SessionLocal, Source
        from sqlalchemy import select
        db = SessionLocal()
        try:
            for username in usernames:
                # Basic cleanup: remove @ and URL parts
                username = username.strip().split('/')[-1].replace('@', '')
                if len(username) < 5: continue
                
                url = f"https://t.me/{username}"
                stmt = select(Source).where(Source.url == url)
                result = db.execute(stmt).scalars().first()
                if not result:
                    new_src = Source(url=url, type="telegram", channel="free")
                    db.add(new_src)
                    logger.info(f"Auto-discovered new Telegram source: {url}")
            db.commit()
        except Exception as e:
            logger.error(f"Error saving discovered sources: {e}")
        finally:
            db.close()
