import time
import os
import functools
import builtins
_orig_print = builtins.print
builtins.print = functools.partial(_orig_print, flush=True)

import browser_core as browser
import naver_core as naver
import human_action as human
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# 1. Prepare environment
account_id = "test_account"
profile_name = "profile_temp_debug"

print("1. 브라우저 띄우기...")
driver = browser.get_driver(profile_name)

print("2. 에디터 진입 (3초 대기)")
driver.get("https://blog.naver.com/GoBlogWrite.naver")
time.sleep(3)

print("3. 프레임 정리")
try:
    driver.switch_to.alert.accept()
except:
    pass

try:
    iframe = driver.find_element(By.ID, "mainFrame")
    driver.switch_to.frame(iframe)
    print(" ✅ mainFrame 진입 완료")
except Exception as e:
    print(" ⚠️ mainFrame 진입 실패:", e)

# Cancel previous draft if popup exists
try:
    cancel = driver.find_element(By.XPATH, "//span[contains(@class, 'se-popup-button-text') and (contains(text(),'취소') or contains(text(),'새 글'))]")
    cancel.click()
    print(" ✅ 이전 글 불러오기 취소")
    time.sleep(1)
except:
    pass

ui = naver.NaverBlogUI(driver)
title_area = ui.find_title_area()
if title_area:
    title_area.click()
    human.human_typing(driver, None, "이미지 테스트", use_action_chains=True)

time.sleep(1)
body_area = ui.find_body_area()
if body_area:
    body_area.click()
else:
    print("본문 클릭 실패")

# 이미지 시스템 준비
# 테스트용 이미지 1장 준비
test_img = ""
img_dir = os.path.join(os.getcwd(), "_uploaded_images")
if os.path.exists(img_dir):
    for root, dirs, files in os.walk(img_dir):
        for f in files:
            if f.endswith(".jpg") or f.endswith(".png"):
                test_img = os.path.join(root, f)
                break
        if test_img: break

if not test_img:
    print("테스트 이미지가 없습니다. 종료합니다.")
    driver.quit()
    exit()

print(f"4. 클립보드 복사 테스트: {test_img}")
if human.copy_image_to_clipboard(test_img):
    print(" ✅ 클립보드 복사 완료")
    print("5. 붙여넣기 시도 (수정된 클립보드 방식 테스트)")
    
    # Try sending to active element directly
    try:
        el = driver.switch_to.active_element
        el.send_keys(By.Keys.CONTROL, 'v') if hasattr(By, 'Keys') else None
        human.ActionChains(driver).key_down(naver.Keys.CONTROL).send_keys('v').key_up(naver.Keys.CONTROL).perform()
    except Exception as e:
        print("   ⚠️ Active Element Paste Failed:", e)
        human.human_paste(driver, "")
    
    # 여기서부터 기다리면서 DOM 상태 출력
    print("6. 5초간 DOM 상태 감시...")
    for i in range(5):
        time.sleep(1)
        # 이미지 찾기
        comb = ", ".join([
            ".se-image-resource", ".se-module-image img", ".se-component-content img",
            ".se-image-container img", ".se2-image img",
            "img[src*='postfiles']", "img[src*='blogfiles']",
            "img[class*='se-image']", "img[class*='__se__image']"
        ])
        imgs = driver.find_elements(By.CSS_SELECTOR, comb)
        print(f"   [{i+1}초] 발견된 이미지 수: {len(imgs)}")
        if len(imgs) > 0:
            for idx, img in enumerate(imgs):
                try:
                    w = img.size.get('width', -1)
                    disp = img.is_displayed()
                    src = img.get_attribute("src")[:50]
                    print(f"     -> 이미지 {idx}: width={w}, displayed={disp}, src={src}")
                except Exception as e:
                    print(f"     -> 이미지 {idx} 에러: {e}")
else:
    print(" ❌ 클립보드 복사 실패")

# 테스트 2: input type file이 있는지 확인
try:
    print("7. 숨겨진 파일 인풋(input[type='file']) 탐색 시도...")
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    print(f"   -> 발견된 파일 인풋 개수: {len(file_inputs)}")
    for fi in file_inputs:
        print(f"   -> id={fi.get_attribute('id')}, accept={fi.get_attribute('accept')}")
except Exception as e:
    print("   -> 파일 인풋 탐색 실패:", e)

print("확인을 위해 브라우저를 끄지 않습니다.")
