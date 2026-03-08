# integration_test.py
# Test script for Benchmarking Engine

import time
import naver_scraper
import gemini_core
import browser_core

def test_pipeline():
    driver = browser_core.get_driver("test_profile")
    
    keyword = "제네시스 GV80"
    print(f"🚀 Starting Test Pipeline for '{keyword}'")
    
    # 1. Scraping
    links = naver_scraper.search_top_blogs(driver, keyword, count=1)
    if not links:
        print("❌ Getting links failed")
        return

    url = links[0]
    print(f"Processing URL: {url}")
    
    data = naver_scraper.extract_blog_content(driver, url)
    print(f"Original Title: {data.get('title')}")
    print(f"Text Length: {len(data.get('text', ''))}")
    
    # 2. AI Analysis
    print("🧠 Extracting Info with Gemini...")
    facts = gemini_core.client.extract_info(data.get('text', ''))
    print("Facts JSON:", facts)
    
    # 3. AI Rewrite
    print("✍️ Generating New Content...")
    new_post = gemini_core.client.rewrite_content(facts, persona="dealer")
    print("New Post JSON:", new_post)
    
    driver.quit()

if __name__ == "__main__":
    test_pipeline()
