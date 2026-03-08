# -*- coding: utf-8 -*-
# rank_tracker.py
# Naver Blog Rank Tracker (Mobile View)

import time
import random
from selenium.webdriver.common.by import By
import browser_core as browser

def check_rank(driver, keyword, blog_id):
    """
    Checks the rank of the recent post by blog_id for the given keyword.
    Searches in MOBILE view (m.naver.com) as it's the standard.
    """
    print(f"   📊 [Rank] Checking rank for '{keyword}' (Blog: {blog_id})...")
    
    # 1. Switch to Mobile User-Agent temporarily? 
    # Or just use the current browser but access m.naver.com
    # For accurate mobile rank, mobile UA is better, but let's try with current setup first.
    # To be safe, we stick to PC view 'VIEW' tab or 'BLOG' tab which corresponds to mobile VIEW.
    
    url = f"https://search.naver.com/search.naver?where=view&query={keyword}"
    browser.safe_navigate(driver, url)
    time.sleep(random.uniform(2, 3))
    
    found_rank = -1
    
    try:
        # Get list of items in VIEW tab
        items = driver.find_elements(By.CSS_SELECTOR, "li.bx, .view_wrap")
        
        for idx, item in enumerate(items):
            try:
                # Find author/blog info
                # Selector varies: .name, .sub_txt, .user_name
                author_elem = item.find_element(By.CSS_SELECTOR, ".name, .user_name, .sub_txt")
                author_text = author_elem.get_text(strip=True)
                
                # Check if it matches our blog_id (or nickname)
                # This part is tricky if we only have ID. 
                # Ideally config should have BLOG_NICKNAME.
                # For now, we assume simple check.
                
                # Also check link
                link = item.find_element(By.CSS_SELECTOR, "a.title_link, a.api_txt_lines").get_attribute("href")
                
                if blog_id in link:
                    found_rank = idx + 1
                    break
            except: continue
            
            if idx >= 30: break # Check top 30 only
            
    except Exception as e:
        print(f"   ⚠️ [Rank] Error: {e}")
        
    if found_rank != -1:
        print(f"   🎉 Found at Rank {found_rank}!")
        return found_rank
    else:
        print("   📉 Not found in Top 30.")
        return None
