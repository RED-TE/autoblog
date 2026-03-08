import os
import sys

with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

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
                
                # 2. 현재 상태 출력
                print(f"🔗 [DEBUG] 현재 URL: {driver.current_url}")
                
                try:
                    existing_imgs = driver.find_elements(By.TAG_NAME, "img")
                    visible_imgs = [img for img in existing_imgs if img.is_displayed()]
                    print(f"📊 [DEBUG] 삽입 전 이미지: 전체 {len(existing_imgs)}개, 표시 {len(visible_imgs)}개")
                except Exception as e:
                    print(f"⚠️ [DEBUG] 이미지 개수 확인 실패: {e}")
                
                print("="*70 + "\\n")
                # ==================== 디버깅 코드 끝 ====================
                
                try:
                    # 이미지 고유화 처리
                    processed_path = image_utils.process_image(content) or content
                    abs_path = os.path.abspath(processed_path)
                    print(f"   📁 [IMAGE] 파일: {os.path.basename(abs_path)}")
                    
                    # 에디터 포커스 확보
                    human.ensure_editor_focus(driver)
                    time.sleep(1.0)
                    
                    # ============================================================
                    # 업로드 방법 시도 (우선순위 순서)
                    # ============================================================
                    uploaded = False
                    upload_method = "none"
                    
                    # ────────────────────────────────────────────────────────────
                    # 방법 1: 파일 인풋 직접 전송 (가장 안정적!)
                    # ────────────────────────────────────────────────────────────
                    print("   🎯 [METHOD 1] 파일 인풋 방식 시도...")
                    try:
                        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                        print(f"      📊 발견된 파일 인풋: {len(file_inputs)}개")
                        
                        for idx, fi in enumerate(file_inputs):
                            try:
                                accept = fi.get_attribute("accept") or ""
                                is_visible = fi.is_displayed()
                                print(f"         [{idx}] accept='{accept}', visible={is_visible}")
                                
                                # 이미지 관련 인풋 찾기
                                if "image" in accept.lower() or accept == "":
                                    print(f"      🎯 파일 인풋 [{idx}] 사용 시도...")
                                    fi.send_keys(abs_path)
                                    time.sleep(2.0)
                                    
                                    # 전송 확인 (이미지 개수 증가 확인)
                                    new_imgs = driver.find_elements(By.TAG_NAME, "img")
                                    if len(new_imgs) > len(existing_imgs):
                                        uploaded = True
                                        upload_method = "file_input"
                                        print(f"      ✅ 파일 인풋 전송 성공! (이미지 {len(existing_imgs)} → {len(new_imgs)}개)")
                                        break
                                    else:
                                        print(f"      ⚠️ 파일 전송했으나 이미지 증가 없음")
                                        
                            except Exception as e:
                                print(f"         ⚠️ [{idx}] 실패: {e}")
                                continue
                        
                        if uploaded:
                            print("   ✅ [METHOD 1] 파일 인풋 방식 성공!")
                        else:
                            print("   ⚠️ [METHOD 1] 파일 인풋 방식 실패")
                            
                    except Exception as e:
                        print(f"   ❌ [METHOD 1] 파일 인풋 에러: {e}")
                    
                    # ────────────────────────────────────────────────────────────
                    # 방법 2: 클립보드 붙여넣기 (Windows)
                    # ────────────────────────────────────────────────────────────
                    if not uploaded:
                        print("   🎯 [METHOD 2] 클립보드 방식 시도...")
                        try:
                            if human.copy_image_to_clipboard(abs_path):
                                print("      ✅ 클립보드 복사 완료")
                                
                                # 본문 클릭
                                try:
                                    b_area = ui.find_body_area()
                                    if b_area:
                                        try:
                                            b_area.click()
                                        except:
                                            driver.execute_script("arguments[0].click();", b_area)
                                        time.sleep(0.5)
                                        print("      ✅ 본문 클릭 완료")
                                except Exception as e:
                                    print(f"      ⚠️ 본문 클릭 실패: {e}")
                                
                                # Ctrl+V 실행
                                print("      🖱️ Ctrl+V 실행...")
                                human.human_paste(driver, "")
                                time.sleep(2.0)
                                
                                # 붙여넣기 확인
                                new_imgs = driver.find_elements(By.TAG_NAME, "img")
                                if len(new_imgs) > len(existing_imgs):
                                    uploaded = True
                                    upload_method = "clipboard"
                                    print(f"      ✅ 클립보드 붙여넣기 성공! (이미지 {len(existing_imgs)} → {len(new_imgs)}개)")
                                else:
                                    print(f"      ⚠️ Ctrl+V 실행했으나 이미지 증가 없음")
                            else:
                                print("      ❌ 클립보드 복사 실패")
                                
                            if uploaded:
                                print("   ✅ [METHOD 2] 클립보드 방식 성공!")
                            else:
                                print("   ⚠️ [METHOD 2] 클립보드 방식 실패")
                                
                        except Exception as e:
                            print(f"   ❌ [METHOD 2] 클립보드 에러: {e}")
                    
                    # ────────────────────────────────────────────────────────────
                    # 방법 3: 이미지 버튼 클릭 후 파일 선택
                    # ────────────────────────────────────────────────────────────
                    if not uploaded:
                        print("   🎯 [METHOD 3] 이미지 버튼 방식 시도...")
                        try:
                            img_btn_selectors = [
                                "button[data-name='image']",
                                "button.se-toolbar-image",
                                "//button[contains(@title, '이미지')]",
                                "//button[contains(@aria-label, '이미지')]"
                            ]
                            
                            btn_clicked = False
                            for sel in img_btn_selectors:
                                try:
                                    if sel.startswith("//"):
                                        btn = driver.find_element(By.XPATH, sel)
                                    else:
                                        btn = driver.find_element(By.CSS_SELECTOR, sel)
                                    
                                    if btn.is_displayed():
                                        btn.click()
                                        print(f"      ✅ 이미지 버튼 클릭: {sel}")
                                        time.sleep(1.5)
                                        btn_clicked = True
                                        break
                                except:
                                    continue
                            
                            if btn_clicked:
                                # 파일 다이얼로그에 파일 경로 전송
                                file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                                for fi in file_inputs:
                                    try:
                                        fi.send_keys(abs_path)
                                        time.sleep(2.0)
                                        
                                        new_imgs = driver.find_elements(By.TAG_NAME, "img")
                                        if len(new_imgs) > len(existing_imgs):
                                            uploaded = True
                                            upload_method = "button_click"
                                            print(f"      ✅ 이미지 버튼 방식 성공!")
                                            break
                                    except:
                                        continue
                            
                            if not uploaded:
                                print("   ⚠️ [METHOD 3] 이미지 버튼 방식 실패")
                                
                        except Exception as e:
                            print(f"   ❌ [METHOD 3] 이미지 버튼 에러: {e}")
                    
                    # ────────────────────────────────────────────────────────────
                    # 업로드 실패 처리
                    # ────────────────────────────────────────────────────────────
                    if not uploaded:
                        print("\\n" + "!"*70)
                        print("❌ [IMAGE] 모든 업로드 방법 실패!")
                        print("   시도한 방법: 파일 인풋, 클립보드, 이미지 버튼")
                        print("!"*70 + "\\n")
                        
                        # HTML 저장 (디버깅용)
                        try:
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            html_path = f"/tmp/upload_fail_{timestamp}.html"
                            screenshot_path = f"/tmp/upload_fail_{timestamp}.png"
                            
                            with open(html_path, "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                            driver.save_screenshot(screenshot_path)
                            
                            print(f"   💾 [DEBUG] HTML: {html_path}")
                            print(f"   📸 [DEBUG] 스크린샷: {screenshot_path}")
                        except:
                            pass
                        
                        continue  # 다음 아이템으로
                    
                    # ────────────────────────────────────────────────────────────
                    # 업로드 성공! 업로드 완료 대기
                    # ────────────────────────────────────────────────────────────
                    print(f"\\n   ✅ [IMAGE] 업로드 시작 성공! (방법: {upload_method})")
                    print(f"   ⏳ [UPLOAD] 서버 업로드 완료 대기 중...")
                    
                    # 업로드 완료 대기 (프레임 유지!)
                    wait_for_image_upload(driver, timeout=30)
                    
                    # ────────────────────────────────────────────────────────────
                    # DOM에서 이미지 찾기
                    # ────────────────────────────────────────────────────────────
                    print("   🔍 [FIND] 업로드된 이미지 찾기 시작...")
                    inserted_image = find_last_uploaded_image(driver, retry=3)
                    
                    if not inserted_image:
                        print("   ❌ [IMAGE] DOM에서 이미지 찾기 실패")
                        
                        # 디버깅 정보
                        try:
                            final_imgs = driver.find_elements(By.TAG_NAME, "img")
                            print(f"   📊 [DEBUG] 최종 이미지 개수: {len(final_imgs)}개")
                            print(f"   📊 [DEBUG] 증가량: +{len(final_imgs) - len(existing_imgs)}개")
                        except:
                            pass
                        
                        continue  # 다음 아이템으로
                    
                    print(f"   ✅ [IMAGE] 이미지 찾기 성공!")
                    
                    # ────────────────────────────────────────────────────────────
                    # 링크 삽입 (선택)
                    # ────────────────────────────────────────────────────────────
                    image_link = item.get("link", "")
                    if image_link and image_link.strip():
                        print(f"   🔗 [LINK] 링크 삽입 시도: {image_link}")
                        link_success = add_link_to_image(driver, inserted_image, image_link)
                        
                        if link_success:
                            print(f"   ✅ [LINK] 링크 삽입 완료!")
                        else:
                            print(f"   ⚠️ [LINK] 링크 삽입 실패 (이미지는 유지됨)")
                    
                    # ────────────────────────────────────────────────────────────
                    # 정리 작업
                    # ────────────────────────────────────────────────────────────
                    # ESC로 선택 해제
                    for _ in range(3):
                        human.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(0.1)
                    
                    # Ctrl+End로 문서 끝 이동
                    cmd = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
                    for _ in range(3):
                        human.ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
                        time.sleep(0.1)
                    
                    # 줄바꿈 (다음 콘텐츠와 분리)
                    for _ in range(3):
                        human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                        time.sleep(0.1)
                    
                    # 안정화 대기
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

if start_idx != -1 and end_idx != -1:
    # 덮어쓰기 수행
    lines[start_idx:end_idx] = [new_block + "\n"]
    with open(r"c:\Users\jhxox\Desktop\blolg_aoto\naver_core.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Replace success")
else:
    print(f"Failed. start_idx={start_idx}, end_idx={end_idx}")
    sys.exit(1)
