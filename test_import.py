
try:
    print("Testing imports...")
    import undetected_chromedriver as uc
    print("undetected_chromedriver imported")
    from selenium import webdriver
    print("selenium imported")
    import browser_core
    print("browser_core imported")
    import human_action
    print("human_action imported")
    import naver_core
    print("naver_core imported")
except Exception as e:
    print(f"Import failed: {e}")
