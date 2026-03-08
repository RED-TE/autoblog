import time
import browser_core as b
from selenium.webdriver.common.by import By

def scan_all_frames(driver, parent_name=""):
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for fr in frames:
        fr_id = fr.get_attribute("id") or fr.get_attribute("name") or "unknown"
        path = f"{parent_name} > {fr_id}" if parent_name else fr_id
        print(f"[{path}] In frame...")
        driver.switch_to.frame(fr)
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for inp in inputs:
            print(f"   => Found file input in {path}: id={inp.get_attribute('id')}, class={inp.get_attribute('class')}")
        scan_all_frames(driver, path)
        driver.switch_to.parent_frame()

def main():
    driver = b.get_driver("profile_main_profile")
    driver.switch_to.window(driver.window_handles[-1])
    driver.switch_to.default_content()
    print("[ROOT] Starting scan...")
    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    for inp in inputs:
        print(f"   => Found file input in ROOT: id={inp.get_attribute('id')}, class={inp.get_attribute('class')}")
    scan_all_frames(driver)

if __name__ == "__main__":
    main()
