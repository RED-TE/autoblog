import os
import sys

with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_apply_link_func = """
def apply_image_link_for_new_project(driver, link_url):
    import time
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    print(f"🔗 [Image Link] 이미지 하이퍼링크 삽입 시작: {link_url}")
    time.sleep(5.0)
    try:
        try: driver.switch_to.frame("mainFrame")
        except: pass
        imgs = driver.find_elements(By.CSS_SELECTOR, ".se-image-resource, .se-component-image img")
        if not imgs: 
            print("   ❌ 본문에서 이미지를 찾을 수 없습니다.")
            return False
        
        target_img = imgs[-1] 
        try: ActionChains(driver).move_to_element(target_img).click().perform()
        except: driver.execute_script("arguments[0].click();", target_img)
        time.sleep(1.0)
        
        link_btn = None
        selectors = ["button.se-toolbar-item-link", "button[data-name='link']", ".se-toolbar-item-image-link"]
        for sel in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                if el.is_displayed():
                    link_btn = el
                    break
            if link_btn: break
            
        if not link_btn:
            print("   ❌ 링크 버튼을 찾지 못했습니다.")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
            
        try: link_btn.click()
        except: ActionChains(driver).click(link_btn).perform()
        time.sleep(1.0)
        
        url_input = driver.find_element(By.CSS_SELECTOR, "input.se-custom-layer-link-input")
        url_input.click()
        time.sleep(0.5)
        url_input.send_keys(link_url)
        time.sleep(0.5)
        url_input.send_keys(Keys.ENTER)
        time.sleep(1.5)
        
        # 대표님 지시: 엔터 한번 더 눌러서 탈출
        ActionChains(driver).send_keys(Keys.ENTER).perform()
        time.sleep(0.5)
        
        print("   ✅ 이미지 링크 맵핑 및 탈출 완료!")
        return True
    except Exception as e:
        print(f"   ⚠️ 이미지 링크 상세 로직 실패: {e}")
        return False
"""

new_image_block = """            elif itype == "image":
                print("\\n" + "="*70)
                print("🔍 [IMAGE] 이미지 클립보드 직행 프로세스 시작")
                print("="*70)
                
                try:
                    driver.find_element(By.CSS_SELECTOR, ".se-main-container")
                except:
                    try:
                        driver.switch_to.default_content()
                        iframe = driver.find_element(By.ID, "mainFrame")
                        driver.switch_to.frame(iframe)
                    except Exception as e:
                        print(f"❌ [FRAME] 프레임 재진입 실패: {e}")
                        continue
                
                try:
                    existing_imgs = driver.find_elements(By.TAG_NAME, "img")
                    processed_path = image_utils.process_image(content) or content
                    abs_path = os.path.abspath(processed_path)
                    print(f"   📁 파일: {os.path.basename(abs_path)}")
                    
                    human.ensure_editor_focus(driver)
                    time.sleep(1.0)
                    
                    uploaded = False
                    
                    # 곧바로 클립보드(Method 2 방식)로 직행하여 딜레이 최소화
                    print("   🎯 클립보드 복붙 단일 방식 시도...")
                    if human.copy_image_to_clipboard(abs_path):
                        human.human_paste(driver, "") # 순수 Ctrl+V
                        time.sleep(2.0)
                        
                        new_imgs = driver.find_elements(By.TAG_NAME, "img")
                        if len(new_imgs) > len(existing_imgs):
                            uploaded = True
                            print("   ✅ 클립보드 붙여넣기 성공!")
                        else:
                            print("   ⚠️ 이미지 증가 없음")
                    
                    if not uploaded:
                        print("   ❌ 이미지 삽입 실패 (클립보드)")
                        continue
                        
                    print("   ⏳ 서버 업로드 대기 중...")
                    wait_for_image_upload(driver, timeout=30)
                    
                    image_link = item.get("link", "")
                    if image_link and image_link.strip():
                        apply_image_link_for_new_project(driver, image_link)
                    else:
                        print("   ✅ 일반 이미지 (링크 없음)")
                        ActionChains(driver).send_keys(Keys.ENTER).perform() # 탈출
                        
                    time.sleep(random.uniform(1.0, 2.0))
                    
                except Exception as e:
                    print(f"\\n❌ [IMAGE] 이미지 삽입 중 에러: {e}")
                    import traceback
                    traceback.print_exc()
"""

# Replace apply_image_link_for_new_project
start_func_idx = -1
end_func_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def apply_image_link_for_new_project"):
        start_func_idx = i
        break
if start_func_idx != -1:
    for i in range(start_func_idx + 1, len(lines)):
        if line.startswith("def ") or "elif itype == " in lines[i]:
            # Actually, let's just find the `def write_post` which is the next major function
            if lines[i].startswith("def write_post"):
                end_func_idx = i
                break

if start_func_idx != -1 and end_func_idx != -1:
    lines[start_func_idx:end_func_idx] = [new_apply_link_func + "\\n"]

# Replace image insertion block
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'elif itype == "image":' in line:
        start_idx = i
        break
if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if "time.sleep(random.uniform(0.8, 1.5))" in line or "elif itype == " in lines[i] or "except Exception" in lines[i] and "test_mode" not in lines[i]:
            # Wait, better logic to find the end:
            pass

# Let's do a reliable replacement for the `elif itype == "image":` block
start_block = -1
end_block = -1

for i, line in enumerate(lines):
    if 'elif itype == "image":' in line:
        start_block = i
        break

if start_block != -1:
    # Find the next sleep or end of loop
    for i in range(start_block + 1, len(lines)):
        # Look for the un-indented or matching indent block, e.g., the final `time.sleep`
        if "time.sleep(random.uniform(0.8, 1.5))" in lines[i]:
            end_block = i
            break

if start_block != -1 and end_block != -1:
    lines[start_block:end_block] = [new_image_block + "\\n"]

with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
    print("Optimization success")
