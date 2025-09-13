
# scraper/base_scraper.py
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """抽象基底類別，定義所有爬蟲的通用介面。"""
    @abstractmethod
    def scrape(self, max_articles: int = 10) -> list[dict]:
        """
        爬取文章並回傳一個包含文章資料的字典列表。

        每篇文章應包含: 'url', 'title', 'content', 'source', 'scraped_at'
        """
        pass
