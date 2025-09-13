
# scraper/scrapers.py
import requests
from bs4 import BeautifulSoup
import datetime
import json
from .base_scraper import BaseScraper

class BaseScraper:
    def scrape(self, **kwargs):
        raise NotImplementedError

class TFCScraper(BaseScraper):
    def scrape(self, base_url: str, max_pages: int = 1) -> list[dict]:
        all_articles = []
        if not base_url.endswith('/'):
            base_url += '/'
            
        for page_num in range(1, max_pages + 1):
            if page_num > 1:
                url = f"{base_url}page/{page_num}/"
            else:
                url = base_url

            print(f"Scraping TFC page: {url}")
            try:
                # 移除 verify=False，解決 InsecureRequestWarning 警告
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'},verify=False)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {url}: {e}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- 核心修正 #1: 使用正確的標籤 <li> 和 class 'kb-query-item' ---
            article_containers = soup.find_all('li', class_='kb-query-item')

            if not article_containers:
                print(f"No articles found on page {page_num}. The structure might have changed or it's the last page.")
                break

            for container in article_containers:
                # --- 核心修正 #2: 使用新的選擇器來找資料 ---
                
                # 找狀態 (例如："錯誤", "部分錯誤")
                status_tag = container.find('a', class_='kb-dynamic-list-item-link')
                status = status_tag.text.strip() if status_tag else 'N/A'

                # 找標題
                title_tag = container.find('div', class_='kb-dynamic-html-id-88164_c2c307-ab')
                title = title_tag.text.strip() if title_tag else 'N/A'

                # 找文章連結
                url_tag = container.find('a', class_='kb-section-link-overlay')
                article_url = url_tag['href'] if url_tag and 'href' in url_tag.attrs else None

                if not article_url:
                    continue
                
                # 抓取單一文章的詳細內容和發布日期
                article_content, publication_date = self.scrape_article_content(article_url)
                
                if article_content:
                    article = {
                        "url": article_url,
                        "title": title,
                        "content": article_content,
                        "status": status,
                        "source": "台灣事實查核中心",
                        "scraped_at": datetime.datetime.now().isoformat(),
                        "publication_date": publication_date
                    }
                    all_articles.append(article)
        
        print(f"Total articles scraped from TFC: {len(all_articles)}")
        return all_articles

    def scrape_article_content(self, url: str) -> tuple[str | None, str | None]:
        """輔助函式：抓取單一文章頁面的內文和發布日期。"""
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'},verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 內文容器的 class 依然是 'entry-content'
            content_div = soup.find('div', class_='entry-content')
            content = content_div.get_text(separator='\n', strip=True) if content_div else ""

            publication_date = None
            # 根據使用者提供的 class 和文字內容尋找發布日期
            headings = soup.find_all('div', class_='wp-block-kadence-advancedheading')
            for heading in headings:
                if '發佈日期' in heading.get_text():
                    date_text = heading.get_text(strip=True)
                    if '：' in date_text:
                        publication_date = date_text.split('：')[1].strip()
                    break
            
            return content, publication_date

        except requests.exceptions.RequestException as e:
            print(f"Error fetching article content from {url}: {e}")
            return "", None

