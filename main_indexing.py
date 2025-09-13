# main_indexing.py
import json
import os
from scraper.scrapers import TFCScraper
from knowledge_base.indexing import build_knowledge_base
from utils.config import PROCESSED_DATA_PATH, DATA_DIR

def run_scrapers():
    """執行所有爬蟲並將結果合併。"""
    all_articles = []

    # --- TFC Scraper ---
    # 使用新的爬蟲，從指定的分類頁面開始爬取
    # 您可以更改 max_pages 來決定要爬取多少頁
    tfc_scraper = TFCScraper()
    tfc_base_url = "https://tfc-taiwan.org.tw/fact-check-reports-all/"
    tfc_articles = tfc_scraper.scrape(base_url=tfc_base_url, max_pages=5) # 先爬取 2 頁作為範例
    all_articles.extend(tfc_articles)



    return all_articles

def main():
    """完整流程：爬取資料 -> 儲存 -> 建立知識庫。"""
    print("Starting the full indexing pipeline...")
    
    # 1. 爬取資料
    articles = run_scrapers()
    if not articles:
        print("No articles were scraped. Exiting.")
        return

    # 2. 儲存處理過的資料
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    with open(PROCESSED_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved {len(articles)} articles to {PROCESSED_DATA_PATH}")

    # 3. 建立知識庫 (向量索引)
    print("\nBuilding knowledge base from the scraped data...")
    build_knowledge_base() 
    
    print("\nPipeline finished successfully!")

if __name__ == "__main__":
    main()
