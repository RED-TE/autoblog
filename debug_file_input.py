import time
import browser_core as b
from selenium.webdriver.common.by import By

def scan_file_inputs():
    driver = b.get_driver("profile_main_profile")
    
    # 1. iframe 진입
    try:
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Total iframes: {len(frames)}")
        for i, fr in enumerate(frames):
            print(f"iframe {i}: id={fr.get_attribute('id')}, name={fr.get_attribute('name')}")
            
        driver.switch_to.frame("mainFrame")
        print("Switched to mainFrame")
    except Exception as e:
        print("Cannot switch to mainFrame:", e)
        return

    # 2. 파일 인풋 검색
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    print(f"Found {len(file_inputs)} file inputs in mainFrame:")
    for i, fi in enumerate(file_inputs):
        print(f"  [{i}] class={fi.get_attribute('class')}, id={fi.get_attribute('id')}, accept={fi.get_attribute('accept')}")
        
scan_file_inputs()
