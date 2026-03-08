import browser_core as browser
import time

def debug_scraper():
    driver = browser.get_driver("debug_profile")
    keyword = "장기렌트"
    url = f"https://search.naver.com/search.naver?where=blog&query={keyword}"
    
    print(f"Navigating to {url}...")
    browser.safe_navigate(driver, url)
    time.sleep(5)
    
    # Save page source
    with open("debug_html.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Page source saved to debug_html.html")
    
    driver.quit()

if __name__ == "__main__":
    debug_scraper()
