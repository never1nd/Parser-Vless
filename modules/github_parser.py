from utils.scraper import BaseScraper, logger
from utils.validator import extract_vless

class GitHubParser(BaseScraper):
    def parse_links(self, urls):
        all_keys = set()
        for url in urls:
            logger.info(f"Parsing GitHub raw: {url}")
            html = self.fetch(url)
            if html == "404_NOT_FOUND":
                logger.warning(f"Source {url} returned 404. Disabling in DB.")
                self._disable_source(url)
                continue
            if not html:
                continue
            keys = extract_vless(html)
            all_keys.update(keys)
            logger.info(f"Found {len(keys)} keys in {url}")
            self.sleep()
        return list(all_keys)

    def _disable_source(self, url):
        from database import SessionLocal, Source
        from sqlalchemy import update
        db = SessionLocal()
        try:
            db.execute(update(Source).where(Source.url == url).values(is_active=False))
            db.commit()
        finally:
            db.close()
