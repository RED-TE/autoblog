import os
import sys

with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

apply_link_func = """
def apply_image_link_for_new_project(driver, link_url):
    import time
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    print(f"🔗 [Image Link] 이미지 하이퍼링크 삽입 시작: {link_url}")
    # [Step 1] 네이버 서버 이미지 렌더링 100% 보장 대기
    time.sleep(5.0)
    try:
        # [Step 2] 액자(iframe) 안으로 시선 이동 후, 방금 올린 이미지 타겟팅
        try: driver.switch_to.frame("mainFrame")
        except: pass
        imgs = driver.find_elements(By.CSS_SELECTOR, ".se-image-resource, .se-component-image img")
        if not imgs: 
            print("   ❌ 본문에서 이미지를 찾을 수 없습니다. (렌더링 실패 혹은 iframe 문제)")
            return False
        
        target_img = imgs[-1] 
        try: ActionChains(driver).move_to_element(target_img).click().perform()
        except: driver.execute_script("arguments[0].click();", target_img)
        time.sleep(1.0)
        
        # [Step 3] 툴바의 '링크(사슬모양)' 아이콘 클릭
        link_btn_selectors = [
             "button.se-toolbar-item-link", 
             "button[data-name='link']",
             "button[data-name='image-link']",             
             ".se-toolbar-item-image-link"
        ]
        link_btn = None
        for sel in link_btn_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                if el.is_displayed():
                    link_btn = el
                    break
            if link_btn: break
            
        if not link_btn:
            print("   ❌ 플로팅 툴바에서 링크 버튼을 찾지 못했습니다.")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
            
        try: link_btn.click()
        except: ActionChains(driver).click(link_btn).perform()
        time.sleep(1.0)
        
        # [Step 4] URL 주소 입력 및 적용(엔터)
        input_selectors = [
            "input.se-custom-layer-link-input",
            "input[placeholder='URL을 입력하세요']",
            ".se-popup-link-input"
        ]
        url_input = None
        for sel in input_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            if elements and elements[0].is_displayed():
                url_input = elements[0]
                break
        
        if not url_input:
            print("   ❌ URL 입력창(text box)을 찾지 못했습니다.")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
            
        url_input.click()
        time.sleep(0.5)
        url_input.send_keys(link_url)
        time.sleep(0.5)
        url_input.send_keys(Keys.ENTER)
        time.sleep(1.0)
        print("   ✅ 이미지 링크 맵핑 완료!")
        
        # [Step 5] 링크 상태 초기화 및 안전한 다음 문단 생성
        cmd = Keys.COMMAND if "Mac" in driver.capabilities.get('platformName', '') else Keys.CONTROL
        for _ in range(3):
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            try: ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
            except: pass
            time.sleep(0.1)
            
        for _ in range(5):
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(0.1)
            
        print("   ✅ 링크 블록 완벽 탈출 (새 문단 확보 완료)")
        return True
    except Exception as e:
        print(f"   ⚠️ 이미지 링크 상세 로직 실패: {e}")
        return False
"""

new_block = """            elif itype == "image":
                # ==================== 디버깅 코드 시작 ====================
                print("\\n" + "="*70)
                print("🔍 [IMAGE DEBUG] 이미지 삽입 프로세스 시작")
                print("="*70)
                
                # 1. 프레임 상태 확인
                in_frame = False
                try:
                    driver.find_element(By.CSS_SELECTOR, ".se-main-container")
                    in_frame = True
                    print("✅ [FRAME] mainFrame 안에 있음")
                except:
                    print("❌ [FRAME] mainFrame 밖에 있음!")
                    try:
                        driver.switch_to.default_content()
                        iframe = driver.find_element(By.ID, "mainFrame")
                        driver.switch_to.frame(iframe)
                        in_frame = True
                        print("✅ [FRAME] mainFrame 재진입 성공")
                    except Exception as e:
                        print(f"❌ [FRAME] mainFrame 재진입 실패: {e}")
                
                if not in_frame:
                    print("❌ [IMAGE] 프레임 진입 실패, 이미지 건너뜀")
                    continue
                
                print(f"🔗 [DEBUG] 현재 URL: {driver.current_url}")
                
                try:
                    existing_imgs = driver.find_elements(By.TAG_NAME, "img")
                    visible_imgs = [img for img in existing_imgs if img.is_displayed()]
                    print(f"📊 [DEBUG] 삽입 전 이미지: 전체 {len(existing_imgs)}개, 표시 {len(visible_imgs)}개")
                except Exception as e:
                    print(f"⚠️ [DEBUG] 이미지 개수 확인 실패: {e}")
                print("="*70 + "\\n")
                
                try:
                    # 이미지 고유화 처리
                    processed_path = image_utils.process_image(content) or content
                    abs_path = os.path.abspath(processed_path)
                    print(f"   📁 [IMAGE] 파일: {os.path.basename(abs_path)}")
                    
                    # 🚨 에디터 포커스 확보 (문서 맨 끝으로 이동)
                    human.ensure_editor_focus(driver)
                    time.sleep(1.0)
                    
                    uploaded = False
                    upload_method = "none"
                    
                    # ────────────────────────────────────────────────────────────
                    # 방법 1: 파일 인풋 직접 전송
                    # ────────────────────────────────────────────────────────────
                    print("   🎯 [METHOD 1] 파일 인풋 방식 시도...")
                    try:
                        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                        if file_inputs:
                            for idx, fi in enumerate(file_inputs):
                                try:
                                    accept = fi.get_attribute("accept") or ""
                                    if "image" in accept.lower() or accept == "":
                                        fi.send_keys(abs_path)
                                        time.sleep(2.0)
                                        new_imgs = driver.find_elements(By.TAG_NAME, "img")
                                        if len(new_imgs) > len(existing_imgs):
                                            uploaded = True
                                            upload_method = "file_input"
                                            print(f"      ✅ 파일 인풋 전송 성공! (이미지 증가 확인)")
                                            break
                                except Exception:
                                    continue
                        if not uploaded:
                            print("   ⚠️ [METHOD 1] 파일 인풋 전송 실패")
                    except Exception as e:
                        print(f"   ❌ [METHOD 1] 파일 인풋 에러: {e}")
                    
                    # ────────────────────────────────────────────────────────────
                    # 방법 2: 클립보드 붙여넣기 (순서 꼬임 방지 버전)
                    # ────────────────────────────────────────────────────────────
                    if not uploaded:
                        print("   🎯 [METHOD 2] 클립보드 방식 시도...")
                        try:
                            if human.copy_image_to_clipboard(abs_path):
                                print("      ✅ 클립보드 복사 완료 (DIB)")
                                
                                # 🚨 기존에 있던 본문 임의 클릭 로직 제거! (중앙 클릭으로 인한 순서 꼬임의 주범)
                                # 앞서 호출한 human.ensure_editor_focus(driver) 덕분에 커서는 이미 문서의 맨 끝에 안전하게 위치함.
                                
                                print("      🖱️ 순수 Ctrl+V 실행...")
                                human.human_paste(driver, "") # 텍스트 없는 순수 Ctrl+V
                                time.sleep(2.0)
                                
                                new_imgs = driver.find_elements(By.TAG_NAME, "img")
                                if len(new_imgs) > len(existing_imgs):
                                    uploaded = True
                                    upload_method = "clipboard"
                                    print(f"      ✅ 클립보드 붙여넣기 성공!")
                                else:
                                    print(f"      ⚠️ Ctrl+V 실행했으나 이미지 증가 없음")
                            else:
                                print("      ❌ 클립보드 복사 실패")
                        except Exception as e:
                            print(f"   ❌ [METHOD 2] 클립보드 에러: {e}")
                            
                    # ────────────────────────────────────────────────────────────
                    # 실패 시 예외처리
                    # ────────────────────────────────────────────────────────────
                    if not uploaded:
                        print("\\n" + "!"*70)
                        print("❌ [IMAGE] 모든 업로드 방법 실패!")
                        continue
                        
                    # ────────────────────────────────────────────────────────────
                    # 업로드 완료 및 링크 삽입
                    # ────────────────────────────────────────────────────────────
                    print(f"\\n   ✅ [IMAGE] 업로드 시작 성공! (방법: {upload_method})")
                    print(f"   ⏳ [UPLOAD] 서버 업로드 완료 대기 중...")
                    
                    wait_for_image_upload(driver, timeout=30)
                    
                    image_link = item.get("link", "")
                    if image_link and image_link.strip():
                        # 새로 정의한 완전판 링크 삽입 함수 호출
                        apply_image_link_for_new_project(driver, image_link)
                    else:
                        print("   🔍 [FIND] 단순 업로드된 이미지 찾기 및 정리...")
                        
                        # 링크가 없는 일반 이미지도 유사한 탈출 과정 거침 (사진 중간에 글씨 끼임 방지)
                        cmd = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
                        for _ in range(3):
                            human.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                            time.sleep(0.1)
                        for _ in range(3):
                            human.ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
                            time.sleep(0.1)
                        for _ in range(3):
                            human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                            time.sleep(0.1)
                        print("   ✅ 일반 이미지 삽입 탈출 완료")
                        
                    wait_time = random.uniform(2.0, 4.0)
                    print(f"   ⏳ [IMAGE] 안정화 대기 {wait_time:.1f}초...\\n")
                    time.sleep(wait_time)
                    
                    print("="*70)
                    print("✅ [IMAGE] 이미지 삽입 프로세스 완료!")
                    print("="*70 + "\\n")
                    
                except Exception as e:
                    print(f"\\n❌ [IMAGE] 이미지 삽입 중 에러: {e}")
                    import traceback
                    traceback.print_exc()
                    print("")
"""


# FIND TARGET BLOCK #
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'elif itype == "image":' in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if 'time.sleep(random.uniform(0.8, 1.5))' in line or "time.sleep(random.uniform(" in lines[i] and 'itype != "image":' in lines[i+1]:
            end_idx = i
            break

# INSERTION
if start_idx != -1 and end_idx != -1:
    # 1. apply_image_link_for_new_project 전역 함수 삽입 (write_post 직전에 넣기 위해 위쪽 상단 찾기)
    # import sys 다음 부분 등 안전한 모듈 최상단에 주입
    import_idx = 0
    for i, line in enumerate(lines):
        if "def write_post" in line:
            import_idx = i - 1
            break
            
    if import_idx > 0:
        lines.insert(import_idx, apply_link_func + "\\n")
        # 줄 번호가 밀렸으므로 start_idx와 end_idx 갱신
        start_idx = -1
        end_idx = -1
        for i, line in enumerate(lines):
            if 'elif itype == "image":' in line:
                start_idx = i
                break
        if start_idx != -1:
            for i in range(start_idx + 1, len(lines)):
                if 'time.sleep(random.uniform(0.8, 1.5))' in line or "time.sleep(random.uniform(" in lines[i] and 'itype != "image":' in lines[i+1]:
                    end_idx = i
                    break

    # 2. 이미지 삽입 본문 블록 교체
    lines[start_idx:end_idx] = [new_block + "\n"]
    
    with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Replace success")
else:
    print(f"Failed to find target bounds. start_idx={start_idx}, end_idx={end_idx}")
    sys.exit(1)
