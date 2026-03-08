# -*- coding: utf-8 -*-
# naver_writer.py — 네이버 블로그 글쓰기 전담 모듈
# [리팩토링] naver_core.py에서 글쓰기 관련 코드를 분리
# 외부 import: import naver_writer 또는 기존 import naver_core as naver 모두 호환.

import time
import random
import os
import re
import platform
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import browser_core as browser
import human_action as human
import image_utils
import ui_selectors as selectors


# ==========================================
# 이미지 관련 헬퍼
# ==========================================

def count_images_in_body(driver):
    """✅ 본문 영역 내 실제 이미지만 정밀 카운트 (JS 엔진 활용)"""
    try:
        js_count = driver.execute_script("""
            var imgs = document.querySelectorAll('img');
            var bodyImages = [];
            var seenLocs = new Set();
            for (var i = 0; i < imgs.length; i++) {
                var img = imgs[i];
                var src = (img.src || '').toLowerCase();
                var cls = (img.className || '').toLowerCase();
                var w = img.offsetWidth;
                var h = img.offsetHeight;
                
                var isReal = src.includes('postfiles') || src.includes('blogfiles') || 
                             cls.includes('se-image') || cls.includes('se-module') || cls.includes('se-resource');
                
                if (isReal && w > 20 && h > 20) {
                    var rect = img.getBoundingClientRect();
                    var locKey = Math.round(rect.left) + ',' + Math.round(rect.top);
                    if (!seenLocs.has(locKey)) {
                        bodyImages.push(img);
                        seenLocs.add(locKey);
                    }
                }
            }
            return bodyImages.length;
        """)
        return int(js_count)
    except Exception as e:
        print(f"      ⚠️ [Count JS Error] {e} (Falling back to Selenium)")
        try:
            found = driver.find_elements(By.CSS_SELECTOR, "img[src*='postfiles'], img[src*='blogfiles'], .se-image-resource img")
            return len([i for i in found if i.is_displayed()])
        except:
            return 0


def wait_for_upload_complete(driver, timeout=30):
    """✅ Progress bar 사라질 때까지 + 최소 4초 강제 대기"""
    print(f"   ⏳ [Upload] 업로드 완료 대기 (최대 {timeout}초)...")
    
    try:
        driver.switch_to.default_content()
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
            print("      ✅ mainFrame으로 일시 전환")
        except:
            print("      ⚠️ mainFrame 없음")
        
        progress_selectors = [
            ".se-image-progress",
            ".se-progress",
            "[class*='progress']",
            ".se-uploading",
            ".se-image-resource.se-is-progress"
        ]
        
        for sel in progress_selectors:
            try:
                WebDriverWait(driver, timeout).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, sel))
                )
            except:
                continue
        
        time.sleep(4.0)  # 최소 대기
        print("   ✅ [Upload] 업로드 완료!")
        return True
        
    except Exception as e:
        print(f"   ⚠️ [Upload] 대기 오류: {e}")
        time.sleep(4.0)
        return False


def apply_image_link(driver, link_url):
    """✅ modules.py 검증된 링크 로직 (3단계 탐색)"""
    if not link_url or not link_url.strip():
        return False
    
    print(f"🔗 [Image Link] 링크 삽입: {link_url}")
    
    try:
        driver.switch_to.default_content()
        try:
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
        except:
            pass
        
        image_selectors = [
            ".se-image-resource",
            ".se-module-image img",
            "img[src*='postfiles']",
            "img[class*='se-image']"
        ]
        
        images = []
        for sel in image_selectors:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            for img in found:
                try:
                    if img.is_displayed() and img.size.get('width', 0) > 50:
                        images.append(img)
                except:
                    continue
        
        if not images:
            print("   ⚠️ 링크 걸 이미지 없음")
            return False
        
        images.sort(key=lambda x: x.location.get('y', 0))
        target_img = images[-1]
        
        print(f"   ✅ 타겟 이미지 (Y={target_img.location['y']})")
        
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', behavior:'smooth'});",
                target_img
            )
            time.sleep(1.5)
            
            ActionChains(driver).move_to_element(target_img).click().perform()
            time.sleep(2.5)
            
            print("   ✅ 이미지 클릭 완료")
            
        except Exception as e:
            print(f"   ⚠️ 클릭 실패: {e}")
            return False
        
        # 링크 버튼 3단계 탐색
        link_btn = None
        
        # 1단계: 플로팅 툴바
        print("   🔍 [단계1] 플로팅 툴바 및 아이콘 대기 탐색 (5초)...")
        floating_selectors = [
            ".se-toolbar-container button[data-name='link']",
            ".se-image-toolbar button[data-name='link']",
            ".se-toolbar-container .se-toolbar-item-link",
            ".se-toolbar-container button.se-toolbar-item-link",
            "button.se-toolbar-item-link",
            "span.se-toolbar-icon"
        ]
        
        start_wait = time.time()
        while time.time() - start_wait < 5:
            for sel in floating_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        if sel == "span.se-toolbar-icon":
                            try:
                                parent_html = btn.find_element(By.XPATH, "..").get_attribute("outerHTML").lower()
                                if "link" not in parent_html and "url" not in parent_html:
                                    continue
                            except: pass
                        
                        link_btn = btn; break
                except: continue
            if link_btn: break
            time.sleep(0.5)
        
        if link_btn:
            print(f"   ✅ [단계1 성공] 버튼 발견!")
        
        # 2단계: 메인 툴바
        if not link_btn:
            print("   🔍 [단계2] 메인 툴바 탐색...")
            main_selectors = [
                "button[data-name='link']",
                "button[data-command='link']",
                "li.se-toolbar-item-link button",
                ".se-toolbar-item.se-toolbar-item-link button",
                ".se-toolbar-item-image-link button"
            ]
            for sel in main_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        link_btn = btn
                        print(f"   ✅ [단계2 성공] {sel}")
                        break
                except:
                    continue
        
        # 3단계: XPath
        if not link_btn:
            print("   🔍 [단계3] XPath 탐색...")
            xpath_selectors = [
                "//button[contains(@title, '링크')]",
                "//button[contains(@aria-label, '링크')]",
                "//button[contains(@class, 'link')]",
                "//button[contains(@data-name, 'link')]"
            ]
            for xpath in xpath_selectors:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    if btn.is_displayed():
                        link_btn = btn
                        print(f"   ✅ [단계3 성공] {xpath}")
                        break
                except:
                    continue
        
        if not link_btn:
            print("   ❌ 링크 버튼 찾기 실패 (3단계 모두 실패)")
            try:
                toolbars = driver.find_elements(By.CSS_SELECTOR, "[class*='toolbar']")
                for tb in toolbars[:3]:
                    if tb.is_displayed():
                        print(f"      - {tb.get_attribute('class')}")
            except:
                pass
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
        
        # 링크 버튼 클릭
        try:
            link_btn.click()
        except:
            driver.execute_script("arguments[0].click();", link_btn)
        
        time.sleep(2.0)
        print("   ✅ 링크 버튼 클릭")
        
        # URL 입력창
        url_input = None
        input_selectors = [
            "input.se-popup-link-url",
            "input.se-custom-layer-link-input",
            "input[placeholder*='URL']",
            ".se-custom-layer-link-container input"
        ]
        
        for sel in input_selectors:
            try:
                inp = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, sel))
                )
                url_input = inp
                print(f"   ✅ URL 입력창: {sel}")
                break
            except:
                continue
        
        if not url_input:
            print("   ❌ URL 입력창 없음")
            return False
        
        url_input.click()
        time.sleep(0.3)
        url_input.clear()
        url_input.send_keys(link_url)
        time.sleep(0.5)
        
        print(f"   ✅ URL 입력: {link_url}")
        
        # 확인 버튼
        confirm_clicked = False
        confirm_selectors = [
            "button.se-popup-button-confirm",
            "button.se-popup-button-submit",
            "button.se-popup-button-apply",
            "button[data-role='confirm']"
        ]
        
        for sel in confirm_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    btn.click()
                    confirm_clicked = True
                    print("   ✅ 확인 버튼")
                    break
            except:
                continue
        
        if not confirm_clicked:
            url_input.send_keys(Keys.ENTER)
            print("   ✅ Enter 확인")
        
        time.sleep(1.0)
        
        cmd = Keys.COMMAND if platform.system() == 'Darwin' else Keys.CONTROL
        
        for _ in range(3):
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
        
        for _ in range(3):
            ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
            time.sleep(0.1)
        
        for _ in range(2):
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(0.1)
        
        print("   ✅ 링크 완료 및 탈출!")
        return True
        
    except Exception as e:
        print(f"   ❌ 링크 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# 인용구 삽입
# ==========================================

def insert_quote(driver, style="default", text=""):
    print(f"   💬 [Quote] 인용구 삽입 ({style})...")
    try:
        sels_editor = selectors.SELECTORS["EDITOR"]
        quote_btn_sel = sels_editor["QUOTE_BTN"]
        
        if not browser.click_element(driver, quote_btn_sel):
            print("   ⚠️ Quote button failed")
            return

        time.sleep(0.5)

        if style == "quotation_line": style_key = "QUOTE_OPT_LINE"
        elif style == "quotation_corner": style_key = "QUOTE_OPT_CORNER"
        else: style_key = "QUOTE_OPT_DEFAULT"
            
        opt_sel = sels_editor.get(style_key, sels_editor["QUOTE_OPT_DEFAULT"])
        browser.click_element(driver, opt_sel)
        time.sleep(1)
            
        if text:
            human.human_typing(driver, None, text, use_action_chains=True)
                
        time.sleep(0.5)
        
        # 출처 제거
        try:
            driver.execute_script("""
                var cites = document.querySelectorAll('.se-quote-source, .se-quote-cite, cite');
                if(cites.length > 0) cites[cites.length - 1].click();
            """)
            time.sleep(0.5)
            human.ActionChains(driver).send_keys(" ").perform()
            time.sleep(0.5)
        except: pass
        
        # 탈출
        print("   🚪 [Quote] 커서 인용구 블록 탈출 중...")
        try:
            # 1. iframe 재진입 확인
            try:
                driver.switch_to.default_content()
                iframe = driver.find_element(By.ID, "mainFrame")
                driver.switch_to.frame(iframe)
            except: pass

            # 2. ESC x3 (선택 해제)
            time.sleep(0.3)
            for _ in range(3):
                human.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.1)

            # 3. 화살표 아래 5번 (인용구 블록 밖으로 확실히 빠져나가기)
            for _ in range(5):
                human.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(0.05)

            # 4. ENTER x2 (기본 구역 확보)
            for _ in range(2):
                human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.2)
                
            print("   ✅ [Quote] 완전 탈출 완료 (ESCx3, ↓x5, Enterx2)")
        except Exception as e:
            print(f"   ⚠️ [Quote] 탈출 실패: {e}")
            
    except Exception as e:
        print(f"   ⚠️ Quote Error: {e}")


# ==========================================
# 네이버 블로그 UI 유틸리티
# ==========================================

class NaverBlogUI:
    """네이버 블로그 UI 유틸리티"""
    def __init__(self, driver):
        self.driver = driver
        
    def find_title_area(self):
        _sels = [".se-documentTitle", ".se-title-text", ".seff-documentTitle"]
        for sel in _sels:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, sel)
                if element.is_displayed(): return element
            except: continue
        return None

    def find_body_area(self):
        _sels = [".se-main-container", ".se-content", ".se-component-content"]
        for sel in _sels:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, sel)
                if element.is_displayed(): return element
            except: continue
        return None

    def find_tag_input(self):
        _sels = ["#tags_input", "input.tag_input", ".tag_input_wrap__zQUUR input", "input[placeholder*='태그']"]
        for _ in range(5):
            for sel in _sels:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el.is_displayed(): return el
                except: continue
            time.sleep(1)
        return None

    def find_publish_buttons(self):
        """발행 버튼 탐색 — (1차 버튼, 2차 버튼) 반환"""
        FIRST_BTN_SELS = [
            "button.publish_btn__m9KHH",
            "button.se-publish-button",
            "button[class*='publish_btn']",
            "button[data-action='publish']",
        ]
        SECOND_BTN_SELS = [
            "button.confirm_btn__WEaBq",
            "button[class*='confirm_btn']",
            "button.se-confirm-publish-button",
        ]
        
        first_btn = None
        for sel in FIRST_BTN_SELS:
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                human.ActionChains(self.driver).move_to_element(btn).pause(0.3).perform()
                time.sleep(0.3)
                try:
                    btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", btn)
                first_btn = btn
                print(f"   ✅ 1차 발행 버튼 ({sel})")
                break
            except: continue
        
        if not first_btn:
            return None, None
        
        time.sleep(2.0)
        
        second_btn = None
        for sel in SECOND_BTN_SELS:
            try:
                btn = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                second_btn = btn
                print(f"   ✅ 2차 발행 버튼 ({sel})")
                break
            except: continue
        
        return first_btn, second_btn


# ==========================================
# 글쓰기 메인 함수
# ==========================================

def write_post(driver, title, content_items, tags=None, publish=True, schedule_time=None, test_mode=False, align="기본", advanced_format=True):
    """글쓰기 메인 함수"""
    print(f"   ✍️ [Write] 글쓰기 시작... (정렬: {align}, 고급서식: {advanced_format})")
    if tags is None: tags = []
    
    orig_sleep = time.sleep
    if test_mode:
        print("   ⚡ [Test Mode] 딜레이 단축")
        time.sleep = lambda x: orig_sleep(0.01) if x < 3.5 else orig_sleep(x)
        
    sels_editor = selectors.SELECTORS["EDITOR"]
    ui = NaverBlogUI(driver)
    
    # 1. 진입
    try:
        browser.safe_navigate(driver, "https://blog.naver.com/GoBlogWrite.naver")
        time.sleep(random.uniform(3, 5))
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        try: driver.switch_to.alert.accept()
        except: pass
    except Exception as e:
        print(f"   ⚠️ 진입 실패: {e}"); return

    # 2. iframe
    try:
        driver.switch_to.default_content()
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
        )
        print("   ✅ [Frame] mainFrame 진입")
    except:
        print("   ℹ️ [Frame] default_content")
        driver.switch_to.default_content()

    # 3. 팝업 처리
    try:
        cancel_span = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(@class, 'se-popup-button-text') and (contains(text(),'취소') or contains(text(),'새 글'))]")
            )
        )
        print("   ⚠️ [Popup] 저장된 글 팝업 -> 취소")
        try: cancel_span.find_element(By.XPATH, "./parent::button").click()
        except: cancel_span.click()
        time.sleep(1.5)
    except: pass

    # 4. 제목
    try:
        print(f"   🖱️ [Write] 제목: {title[:20]}...")
        title_area = ui.find_title_area()
        
        if title_area:
            try: title_area.click()
            except: driver.execute_script("arguments[0].click();", title_area)
            time.sleep(0.8)
            human.ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            time.sleep(0.3)
            human.human_typing(driver, None, title, use_action_chains=True)
            print("   ✅ 제목 완료")
        else:
            print("   ⚠️ 제목 영역 실패")
    except Exception as e:
        print(f"   ⚠️ 제목 에러: {e}")

    time.sleep(1)

    # 5. 본문 진입
    try:
        print("   🖱️ [Write] 본문 이동...")
        human.ActionChains(driver).send_keys(Keys.TAB).perform()
        time.sleep(1)
    except: pass

    body_area = ui.find_body_area()
    if body_area:
        try: body_area.click()
        except: driver.execute_script("arguments[0].click();", body_area)
    else:
        print("   ⚠️ 본문 영역 실패")
    time.sleep(1)
    
    # [NEW] 본문 진입 직후 정렬 적용
    if align in ["왼쪽", "가운데", "오른쪽"]:
        print(f"   🔠 [Align] 텍스트 정렬 적용: {align}")
        align_key = {"왼쪽": "l", "가운데": "c", "오른쪽": "r"}[align]
        try:
            IS_MAC = __import__('platform').system() == 'Darwin'
            cmd = Keys.COMMAND if IS_MAC else Keys.CONTROL
            # Ctrl + Alt + L/C/R
            human.ActionChains(driver).key_down(cmd).key_down(Keys.ALT).send_keys(align_key).key_up(Keys.ALT).key_up(cmd).perform()
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ 정렬 단축키 적용 실패: {e}")

    # 6. 본문 아이템
    try:
        # ── 이미지 완료 후 편집기 복구 헬퍼 (꼬임 방지 핵심) ────────
        def _recover_editor_after_image():
            """✅ 이미지 삽입 완료 후 커서를 이미지 블록 밖으로 이동
            핵심: 클릭 금지 (이미지 인식 시 body.click() → 이미지 삭제)
            탈출 시케: ESC → ↓ 5회(이미지 블록 아래) → ENTER"""
            print("   🔄 [Recover] 커서 이미지 블록 탈출 중...")
            try:
                # 1. iframe 재진입
                try:
                    driver.switch_to.default_content()
                    iframe = driver.find_element(By.ID, "mainFrame")
                    driver.switch_to.frame(iframe)
                except:
                    pass

                # 2. ESC — 이미지 선택 해제 (커서 모드로)
                time.sleep(0.3)
                for _ in range(3):
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(0.1)

                # 3. ↓ 화살표 5회 — 이미지 블록 커서를 아래로 이동
                #    (클릭 없이 타이핑 모드만 사용 — 이미지 블록 삭제 방지)
                for _ in range(5):
                    ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                    time.sleep(0.05)

                # 4. ENTER 1번 — 새 단락
                ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.3)
                print("   ✅ [Recover] 커서 탈출 완료")
            except Exception as _e:
                print(f"   ⚠️ [Recover] 실패: {_e}")

        def _ensure_cursor_at_end():
            # 텍스트, 인용구 삽입 시 커서 정렬 (클릭 배제!)
            print("   🔄 [Focus] 커서 끝 정렬 확인 중...")
            try:
                human.ensure_editor_focus(driver)
                # 무작위 클릭(body area) 제거: 글 중간에 커서가 꼽히는 원인
                time.sleep(0.1)
                
                # 혹시 블록 지정되어 있을 수 있으니 ESC 2회
                for _ in range(2):
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(0.05)
                    
                IS_MAC = __import__('platform').system() == 'Darwin'
                cmd = Keys.COMMAND if IS_MAC else Keys.CONTROL
                for _ in range(3):
                    ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
                    time.sleep(0.1)
                # ENTER는 치지 않음 (공란 무한 생성 및 단락 쪼개짐 방지)
            except Exception as e:
                print(f"   ⚠️ 커서 정렬 예외: {e}")

        def _recover_editor_after_image():
            """✅ 이미지 삽입 완료 후 커서를 이미지 블록 밖으로 이동
            (사용자 지침: ESC x3 → Ctrl+End x3 → Enter x2 강제 탈출 로직 적용)"""
            print("   🔄 [Recover] 커서 이미지 블록 탈출 중...")
            try:
                # 1. iframe 재진입
                try:
                    driver.switch_to.default_content()
                    iframe = driver.find_element(By.ID, "mainFrame")
                    driver.switch_to.frame(iframe)
                except:
                    pass

                # 2. ESC x3 (이미지 선택 해제)
                time.sleep(0.3)
                for _ in range(3):
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(0.1)

                # 3. Ctrl+End x3 (강제 문서 끝 이동)
                IS_MAC = __import__('platform').system() == 'Darwin'
                cmd = Keys.COMMAND if IS_MAC else Keys.CONTROL
                for _ in range(3):
                    ActionChains(driver).key_down(cmd).send_keys(Keys.END).key_up(cmd).perform()
                    time.sleep(0.1)

                # 4. ENTER x2 (확실한 공백/새 줄 확보)
                for _ in range(2):
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.2)
                    
                print("   ✅ [Recover] 커서 완전 탈출 완료 (ESCx3, Ctrl+Endx3, Enterx2)")
            except Exception as _e:
                print(f"   ⚠️ [Recover] 실패: {_e}")

        # ── [NEW] 표(Table) 삽입 헬퍼 ──────────────────────────────
        def _insert_table(rows):
            print("   📊 [Table] 표 삽입 (3x3 기반)")
            try:
                # 표 툴바 버튼 찾기
                table_btn_sel = sels_editor.get("TABLE_BTN", "button[data-name='table']")
                if not browser.click_element(driver, table_btn_sel):
                    print("   ⚠️ 표 버튼 클릭 실패")
                    return
                time.sleep(1)
                
                # 표 내용 채우기 (최대 9칸, 3x3)
                flat_cells = []
                for row in rows:
                    for cell in row:
                        flat_cells.append(cell)
                
                # Naver Editor 기본 표는 3x3 (총 9칸)
                for i in range(9):
                    cell_text = flat_cells[i] if i < len(flat_cells) else ""
                    if cell_text:
                        human.human_typing(driver, None, cell_text, use_action_chains=True)
                    time.sleep(0.1)
                    # 다음 칸으로 이동 (마지막 칸에선 이동 대신 엔터 후 탈출)
                    if i < 8:
                        human.ActionChains(driver).send_keys(Keys.ARROW_RIGHT).perform()
                        time.sleep(0.1)
                        
                # 표 탈출 방향키 밑으로 3번 후 엔터
                time.sleep(0.5)
                for _ in range(3):
                    human.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                    time.sleep(0.1)
                human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                print("   ✅ [Table] 표 작성 완료")
            except Exception as e:
                print(f"   ⚠️ [Table] 오류: {e}")

        # 목록 상태 추적 ("bullet", "decimal", None)
        current_list_state = None

        for idx_item, item in enumerate(content_items):
            if isinstance(item, str): item = {"type": "text", "content": item}
            itype = item.get("type", "text")
            content = item.get("content", "")
            if not content and itype not in ["image"]: continue
            
            print(f"   📝 [Insert {idx_item+1}/{len(content_items)}] 블록 작성 중: {itype.upper()} (길이: {len(str(content))}자)")
            
            # 모든 아이템 삽입 직전, 무조건 커서를 문서 절대적인 가장 아래로 뺌
            _ensure_cursor_at_end()
            
            # 리스트 상태 탈출 로직 (이전 아이템이 리스트였는데 지금은 아닐 경우)
            if current_list_state and itype != "list":
                print(f"   ⭕ [List] 리스트 모드 종료 (현재 블록: {itype})")
                # 엔터를 두 번 연속 입력하여 리스트 모드를 확실히 탈출
                for _ in range(2):
                    human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.1)
                current_list_state = None
                time.sleep(0.5)

            if itype == "text":
                if test_mode and len(content) > 50:
                    content = content[:50] + " ... (테스트)"
                    
                human.human_typing(driver, None, content, use_action_chains=True)
                for _ in range(random.randint(3, 5)):
                    human.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                    time.sleep(0.05)
                # 시원한 가독성을 위해 단락 사이에 엔터 2~3회 삽입
                for _ in range(random.randint(2, 3)):
                    human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.1)
                
            elif itype == "list" and advanced_format:
                list_style = item.get("style", "bullet")  # bullet or decimal
                
                # 리스트 진입 시 마크다운 자동 변환 트리거 (1. 또는 - 입력)
                if current_list_state != list_style:
                    print(f"   ⏺️ [List] 리스트 모드 진입 ({list_style})")
                    prefix = "1. " if list_style == "decimal" else "- "
                    human.human_typing(driver, None, prefix, use_action_chains=True)
                    time.sleep(0.4)
                    current_list_state = list_style
                
                human.human_typing(driver, None, content, use_action_chains=True)
                human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.2)
                
            elif itype == "table" and advanced_format:
                _insert_table(content)
                time.sleep(0.5)
                
            elif itype == "quote":
                insert_quote(driver, item.get("style", "default"), content)
                time.sleep(0.5)

            elif itype == "image":
                print("\n" + "="*70)
                print("🖼️ [IMAGE] 이미지 삽입")
                print("="*70)
                
                try:
                    driver.switch_to.default_content()
                    try:
                        iframe = driver.find_element(By.ID, "mainFrame")
                        driver.switch_to.frame(iframe)
                    except:
                        pass
                    
                    img_before = count_images_in_body(driver)
                    print(f"   📊 삽입 전: {img_before}개")
                    
                    processed = image_utils.process_image(content) or content
                    abs_path = os.path.abspath(processed)
                    print(f"   📁 파일: {os.path.basename(abs_path)}")
                    
                    # 다시 한 번 포커스 정리 (이미지 처리 중 이탈 대비)
                    _ensure_cursor_at_end()
                    
                    # 클립보드 1차
                    print("   🎯 [METHOD 1] 클립보드...")
                    uploaded = False
                    
                    if human.copy_image_to_clipboard(abs_path):
                        human.human_paste(driver, "")
                        time.sleep(3.5)
                        
                        img_after_1 = count_images_in_body(driver)
                        
                        if img_after_1 > img_before:
                            uploaded = True
                            print(f"   ✅ 1차 성공! ({img_before} → {img_after_1})")
                        else:
                            print("   ⚠️ 1차 실패, 재시도...")
                            
                            try:
                                b_area = ui.find_body_area()
                                ActionChains(driver).move_to_element(b_area).click().perform()
                                time.sleep(0.5)
                            except: pass
                            
                            human.ensure_editor_focus(driver)
                            human.human_paste(driver, "")
                            time.sleep(2.0)
                            
                            img_after_2 = count_images_in_body(driver)
                            
                            if img_after_2 > img_before:
                                uploaded = True
                                print(f"   ✅ 2차 성공! ({img_before} → {img_after_2})")
                            else:
                                print(f"   ❌ 클립보드 실패 (이미지 수 변화 없음: {img_before} -> {img_after_2})")
                    
                    if not uploaded:
                        print("   ❌ 이미지 삽입 실패")
                        continue
                    
                    print("   ⏳ 서버 업로드 대기...")
                    wait_for_upload_complete(driver, timeout=30)
                    # ── [핵심 원리] 업로드 완료 판단 후 4초 강제 대기 ──
                    time.sleep(4.0)
                    
                    # ── [핵심 원리] 다시 한 번 카운트 검증 ──
                    img_after_wait = count_images_in_body(driver)
                    
                    if img_after_wait > img_before:
                        link_url = item.get("link", "")
                        if link_url and link_url.strip():
                            print(f"   🔗 링크 적용: {link_url}")
                            apply_image_link(driver, link_url)
                            
                        # ── [핵심 원리] 꼬임 방지를 위한 완벽 탈출 ──
                        _recover_editor_after_image()
                    else:
                        print(f"   ❌ 업로드 대기 후 이미지 증가 확인 안됨 ({img_before} -> {img_after_wait})")
                    
                    time.sleep(0.8)
                    
                    img_final = count_images_in_body(driver)
                    print(f"   📊 최종: {img_final}개 (+{img_final - img_before})")
                    
                    print("="*70)
                    print("✅ [IMAGE] 완료!")
                    print("="*70 + "\n")
                    
                except Exception as e:
                    print(f"\n❌ [IMAGE] 오류: {e}")
                    import traceback
                    traceback.print_exc()
                
                time.sleep(random.uniform(1.0, 2.0))

            if itype != "image":
                human.human_scroll(driver, 30, 100)
                
        # 문서 끝에 도달했는데 리스트 상태가 안 닫혀있으면 닫기
        if current_list_state:
            print("   ⭕ [List] 문서 종료 전 리스트 모드 최종 강제 종료")
            # 엔터 2번으로 리스트 블록 탈출
            for _ in range(2):
                human.ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.1)
            current_list_state = None

        print("   ✅ 본문 완료")
    except Exception as e:
        print(f"   ⚠️ 본문 실패: {e}")

    # 7. 발행
    try:
        print("   🚀 [Publish] 발행 시작...")
        
        if not test_mode:
            time.sleep(random.uniform(3.5, 5.5))
        
        try: human.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except: pass
        time.sleep(1.0)
        
        first_btn, second_btn = ui.find_publish_buttons()
        if not first_btn:
            print("   ❌ 1차 버튼 없음")
            return False
            
        print("   ✅ 1차 발행 팝업 열기")
        
        # 태그
        if tags:
            try:
                print(f"   🏷️ [Tags] 태그 입력")
                
                final_tags = []
                seen = set()
                
                for t in tags:
                    clean = re.sub(r"[^\w가-힣]", "", t)
                    if clean and clean not in seen and len(final_tags) < 30:
                        final_tags.append(clean)
                        seen.add(clean)
                        
                supplement = ["신차출고", "즉시출고", "프로모션", "할인", "최저가", "장기렌트", "오토리스"]
                random.shuffle(supplement)
                for kw in supplement:
                    if len(final_tags) >= 25: break
                    clean = kw.replace(" ", "")
                    if clean and clean not in seen:
                        final_tags.append(clean)
                        seen.add(clean)
                        
                final_tags = final_tags[:30]
                
                tag_input = ui.find_tag_input()
                
                if tag_input:
                    try: tag_input.click()
                    except: driver.execute_script("arguments[0].click();", tag_input)
                    time.sleep(0.5)
                    
                    added_count = 0
                    for tag in final_tags:
                        try:
                            human.human_typing(driver, tag_input, tag)
                            time.sleep(0.3)
                            tag_input.send_keys(" ") # 명시적 스페이스 문법
                            time.sleep(0.2)
                            tag_input.send_keys(Keys.ENTER)
                            time.sleep(0.4)
                            added_count += 1
                        except: continue
                    print(f"   ✅ 태그 {added_count}개")
                else:
                    print("   ⚠️ 태그 입력창 없음")
            except Exception as e:
                print(f"   ⚠️ 태그 에러: {e}")

        # 예약 발행
        if schedule_time:
            try:
                print(f"   🕰️ [Publish] 예약: {schedule_time}")
                reserve_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='radio_time2']"))
                )
                try: human.ActionChains(driver).move_to_element(reserve_btn).pause(0.2).click().perform()
                except: driver.execute_script("arguments[0].click();", reserve_btn)
                time.sleep(1.2)
                
                import re as _re
                _nums = _re.findall(r'\d+', schedule_time)
                # _nums 예: ['2026', '03', '25', '18', '30']
                if len(_nums) < 4:
                    print(f"   ❌ [Date] 날짜 형식 파싱 실패: {schedule_time}")
                    raise ValueError(f"날짜 파싱 실패: {schedule_time}")
                year_val  = _nums[0]
                month_val = _nums[1].zfill(2)
                day_val   = _nums[2].zfill(2)
                hour_val  = _nums[3].zfill(2) if len(_nums) > 3 else "14"
                min_val   = _nums[4].zfill(2) if len(_nums) > 4 else "00"

                print(f"   📅 날짜 설정: {year_val}.{month_val}.{day_val} {hour_val}:{min_val}")
                target_date_str = f"{year_val}. {month_val}. {day_val}."
                
                # ===========================================================
                # 달력 팝업 열기 (시간 선택기가 팝업 안에 있을 수 있으므로 무조건 엽니다)
                # ===========================================================
                try:
                    date_input = driver.execute_script("""
                        var s=['input.input_date__QmA0s','input.date_option__p_7iA','input[class*="date"]'];
                        for(var i=0;i<s.length;i++){var e=document.querySelector(s[i]);if(e)return e;}
                        return null;
                    """)
                    if date_input:
                        driver.execute_script("arguments[0].removeAttribute('readonly'); arguments[0].click();", date_input)
                    time.sleep(1.0)
                except: pass

                js_set_ok = driver.execute_script(f"""
                    var selectors = [
                        'input.input_date__QmA0s',
                        'input.date_option__p_7iA',
                        'input[class*="date"]'
                    ];
                    var el = null;
                    for (var i = 0; i < selectors.length; i++) {{
                        el = document.querySelector(selectors[i]);
                        if (el) break;
                    }}
                    if (!el) return false;
                    
                    el.removeAttribute('readonly');
                    el.removeAttribute('disabled');
                    
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(el, '{target_date_str}');
                    
                    el.dispatchEvent(new Event('input',  {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    el.dispatchEvent(new Event('blur',   {{bubbles:true}}));
                    return el.value;
                """)
                
                # JS 주입 결과가 입력하려던 문자열(목표일)과 일치할 때만 성공 처리
                if js_set_ok and js_set_ok.strip() == target_date_str.strip():
                    print(f"   ✅ [Date] JS 직접 주입 성공: {js_set_ok}")
                else:
                    if js_set_ok:
                        print(f"   ⚠️ [Date] JS 주입 시도했으나 값이 변경됨 ({js_set_ok} != {target_date_str}) — 달력 UI 시도")
                    else:
                        print(f"   ⚠️ [Date] JS 직접 주입 실패 — 달력 UI 시도")
                    
                    # 달력 팝업 대기
                    for _ in range(8):
                        time.sleep(0.3)
                        _vis = driver.execute_script(
                            "var c=document.querySelector('.ui-datepicker,.datepicker'); return c && c.offsetHeight > 0;")
                        if _vis: break
                    
                    print(f"   📅 [Date] STEP2 — 연/월 탐색 및 날짜 버튼 클릭")
                    for _ in range(24):
                        curr_y = driver.execute_script(
                            "var el=document.querySelector('.ui-datepicker-year'); return el?parseInt(el.textContent.trim()):null;")
                        curr_m = driver.execute_script(
                            "var el=document.querySelector('.ui-datepicker-month'); return el?parseInt(el.textContent.replace(/[^0-9]/g,'').trim()):null;")
                        
                        if not curr_y or not curr_m:
                            print("   ⚠️ [Date] 달력 헤더 없음")
                            break
                        
                        ty, tm = int(year_val), int(month_val)
                        
                        if curr_y == ty and curr_m == tm:
                            clicked = driver.execute_script("""
                                var td = String(parseInt(arguments[0]));
                                var cells = document.querySelectorAll(
                                    '.ui-datepicker td button, .ui-datepicker td a, .datepicker td button, button.ui-state-default, a.ui-state-default, td button.ui-state-default');
                                for (var i = 0; i < cells.length; i++) {
                                    var txt = cells[i].textContent.trim().replace(/\\s/g,'');
                                    if (txt === td || txt === td.padStart(2,'0')) {
                                        cells[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                        if (cells[i].click) cells[i].click();
                                        return true;
                                    }
                                }
                                return false;
                            """, day_val)
                            
                            if clicked:
                                print(f"   ✅ [Date] 달력 클릭 성공! ({year_val}.{month_val}.{day_val})")
                            else:
                                print(f"   ⚠️ [Date] 달력 클릭 실패")
                            break
                        elif curr_y < ty or (curr_y == ty and curr_m < tm):
                            moved = driver.execute_script("""
                                var btn=document.querySelector('button.ui-datepicker-next, [title="다음달"], .ui-icon-circle-triangle-e');
                                if(btn){
                                    btn.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                    if(btn.click) btn.click();
                                    return true;
                                } return false;""")
                            if not moved: break
                        else:
                            moved = driver.execute_script("""
                                var btn=document.querySelector('button.ui-datepicker-prev, [title="이전달"], .ui-icon-circle-triangle-w');
                                if(btn){
                                    btn.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                                    if(btn.click) btn.click();
                                    return true;
                                } return false;""")
                            if not moved: break
                        time.sleep(0.4)
                
                # 달력 팝업 닫기 (아직 떠있다면)
                try:
                    driver.execute_script("""
                        var cal = document.querySelector('.ui-datepicker, .ui-datepicker-calendar');
                        if(cal && cal.offsetHeight > 0){
                            document.body.click();
                        }
                    """)
                    time.sleep(0.2)
                except: pass
                
                
                # 시간(시/분) 선택 — 위에서 정규식으로 추출한 hour_val, min_val 사용
                hh = hour_val
                mm_int = int(min_val)
                mm = str((mm_int // 10) * 10).zfill(2)
                print(f"   🕒 시간 선택: {hh}시 {mm}분")

                def _select_time(driver, type_str, val_str):
                    ko_type = "시간" if type_str == "hour" else "분"
                    # 1) 일반 select
                    for sel in [f"select[class*='{type_str}']", f"select[title*='{ko_type}']"]:
                        try:
                            el = driver.find_element(By.CSS_SELECTOR, sel)
                            Select(el).select_by_value(val_str)
                            return True
                        except: pass
                    
                    # 2) 커스텀 드롭다운 버튼
                    btn = driver.execute_script(f"""
                        var btns = document.querySelectorAll('button, a, div[role="button"]');
                        for(var i=0; i<btns.length; i++){{
                            var c = btns[i].className || "";
                            var t = btns[i].title || "";
                            if(typeof c === 'string' && c.toLowerCase().includes('{type_str}')) return btns[i];
                            if(typeof t === 'string' && t.includes('{ko_type}')) return btns[i];
                        }}
                        return null;
                    """)
                    
                    if btn:
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(0.5)
                            clicked = driver.execute_script(f"""
                                var items = document.querySelectorAll('li button, li a, [role="option"]');
                                var t1 = "{val_str}";
                                var t2 = "{int(val_str)}";
                                var t3 = "{val_str}" + (arguments[0] === 'hour' ? "시" : "분");
                                for(var i=0; i<items.length; i++){{
                                    var txt = items[i].textContent.trim();
                                    if(txt === t1 || txt === t2 || txt === t3){{
                                        items[i].click();
                                        return true;
                                    }}
                                }}
                                return false;
                            """, type_str)
                            if clicked: return True
                        except: pass
                    return False

                if _select_time(driver, "hour", hh):
                    print(f"   ✅ {hh}시 선택 완료")
                else:
                    print(f"   ⚠️ 시 선택 실패")
                
                time.sleep(0.3)
                
                if _select_time(driver, "minute", mm):
                    print(f"   ✅ {mm}분 선택 완료")
                else:
                    print(f"   ⚠️ 분 선택 실패")

                print(f"   ✅ 예약 완료")
                time.sleep(0.8)
            except Exception as e:
                print(f"   ⚠️ 예약 실패: {e}")

        # 멈춤 모드
        if not publish:
            print("   🛑 [멈춤] 발행 전 멈춤")
            print("   ✏️ 수동 발행 대기...")
            while True:
                try:
                    curr = driver.current_url.lower()
                    if "editor" not in curr and "write" not in curr:
                        print("   ✅ 수동 발행 완료")
                        break
                    time.sleep(3)
                except:
                    break
            return
            
        if not second_btn:
            print("   ❌ 2차 버튼 없음")
            return False
            
        try:
            human.ActionChains(driver).move_to_element(second_btn).pause(0.5).click().perform()
        except:
            driver.execute_script("arguments[0].click();", second_btn)
            
        print("   ✅ 발행 완료!")
        
        try:
            WebDriverWait(driver, 10).until(EC.url_contains("logNo="))
        except: pass
        time.sleep(2.0)
        
    except Exception as e:
        print(f"   ⚠️ 발행 에러: {e}")
