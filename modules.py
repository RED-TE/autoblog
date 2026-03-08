
# -*- coding: utf-8 -*-
# modules.py
# RealCar Bot V48.7 Core Engine (Windows Edition)
# [Fix] AI 모델 자동 탐색 + 이미지 OFF + Selectors + Anti-Detection + Quote + [NEW] Kin & Nurturing

import time
import random
import os
import shutil
import numpy as np
import pyperclip
import re
import sys
import glob
import json
import unicodedata
import platform
from datetime import datetime
from PIL import Image, ImageEnhance, ImageDraw, ImageFont

# 설정 파일 불러오기
import config
import log_manager
from plan_manager import PlanLevel
import ui_selectors as selectors

# Selenium & Undetected Chromedriver
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("❌ Selenium Import Error")
    sys.exit(1)

# ... (Previous helper functions: slow_down, get_sys_info, human_typing, human_paste, human_scroll, human_move_and_click, safe_navigate, get_driver, naver_login, insert_quote, naver_write_flow)

# [NOTE] I am appending the new functions at the end of the file for this update.
# In a real scenario, I would ensure the full file is maintained. 
# Here I will write the FULL file content with the new functions added.

# ==========================================
# 0. Helper Functions (Human Mimicry)
# ==========================================
def slow_down(context="Action"):
    delay = random.randint(2, 5)
    print(f"   ☕ [Slow Mode] {context} 후 {delay}초 대기 중...")
    time.sleep(delay)

def get_sys_info():
    uname = platform.uname()
    return f"{uname.system} {uname.release} ({uname.machine})"

def human_typing(driver, element, text, speed_range=(0.05, 0.12), use_action_chains=False):
    """
    [NEW] 휴먼 타이핑 2.0: 오타 및 자연스러운 속도 변화
    use_action_chains=True 시 요소 지정 없이 현재 포커스에 입력
    """
    try:
        # Modifier Key Stuck 방지
        try: ActionChains(driver).key_up(Keys.CONTROL).key_up(Keys.ALT).key_up(Keys.SHIFT).perform()
        except: pass
        
        actions = ActionChains(driver)
        
        for char in text:
            # 5% 확률로 오타 발생 시뮬레이션
            if random.random() < 0.05:
                wrong_char = chr(ord(char) + 1) # 인접 문자 대충 시뮬레이션
                
                if use_action_chains:
                    actions.send_keys(wrong_char).perform()
                    time.sleep(random.uniform(0.1, 0.3))
                    actions.send_keys(Keys.BACKSPACE).perform()
                else:
                    element.send_keys(wrong_char)
                    time.sleep(random.uniform(0.1, 0.3))
                    element.send_keys(Keys.BACKSPACE)
                    
                time.sleep(random.uniform(0.1, 0.2))
            
            # 입력
            if use_action_chains:
                actions.send_keys(char).perform()
            else:
                element.send_keys(char)
                
            # 가우시안 분포로 속도 조절 (자연스러움)
            delay = abs(random.gauss((speed_range[0] + speed_range[1]) / 2, 0.02))
            time.sleep(delay)
            
    except Exception as e:
        print(f"   ⚠️ Typing Error: {e}")

def human_paste(driver, text):
    try:
        pyperclip.copy(text)
        time.sleep(random.uniform(0.5, 1.0))
        act = ActionChains(driver)
        if platform.system() == "Darwin":
            key = Keys.COMMAND
        else:
            key = Keys.CONTROL
        act.key_down(key).send_keys('v').key_up(key).perform()
        time.sleep(random.uniform(0.8, 1.5))
    except: pass

def human_scroll(driver, min_scroll=200, max_scroll=600):
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_pos = 0
        while current_pos < total_height:
            scroll_amount = random.randint(min_scroll, max_scroll)
            current_pos += scroll_amount
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            if random.random() < 0.1:
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, -100);")
                time.sleep(0.5)
                driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(random.uniform(0.5, 1.5))
            if current_pos > 2000 and random.random() < 0.3:
                break
    except: pass

def human_move_and_click(driver, element):
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(0.2, 0.5))
        actions.click()
        actions.perform()
    except:
        element.click()

def safe_navigate(driver, url):
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
    except:
        try: driver.execute_script("window.stop();")
        except: pass

# ==========================================
# 1. 브라우저 제어 (get_driver)
# ==========================================
def get_driver(profile_name, debug_port=9222):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # 2. Image OFF (요청 사항) -> 리얼 유저 모드를 위해 주석 처리
    # [FIX] 이전 실행으로 인해 프로필에 '이미지 차단'이 저장되었을 수 있으므로 명시적으로 '허용(1)'으로 설정
    # options.add_argument("--blink-settings=imagesEnabled=true") # 기본값
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 1})

    # 3. [NEW] Anti-Detection (AutomationControlled 제거)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    system = platform.system()
    if system == "Darwin":
        binary_locations = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for path in binary_locations:
            if os.path.exists(path):
                options.binary_location = path
                break
                
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        default_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ua = getattr(config, 'USER_AGENTS', [default_ua])[0]
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ua})
        print("   ✅ Driver initialized with Stealth Mode (CDP injected)")
        return driver
    except Exception as e:
        print(f"   ❌ Driver init failed: {e}")
        return None

# ==========================================
# 2. 로그인 (Login)
# ==========================================
def naver_login(driver, user_id, user_pw):
    print("   🔐 [Login] 로그인 시도...")
    try:
        safe_navigate(driver, "https://www.naver.com")
        time.sleep(random.uniform(2, 3))
        
        sels_main = selectors.SELECTORS["MAIN"]
        if "LOGIN_BTN" in sels_main:
            try:
                login_gate_btn = driver.find_element(By.CSS_SELECTOR, sels_main["LOGIN_BTN"])
                human_move_and_click(driver, login_gate_btn)
                time.sleep(2)
            except:
                safe_navigate(driver, "https://nid.naver.com/nidlogin.login")
        else:
            safe_navigate(driver, "https://nid.naver.com/nidlogin.login")

        sels = selectors.SELECTORS["LOGIN"]
        
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, sels["ID_INPUT"]))
        )
        human_move_and_click(driver, id_input)
        human_paste(driver, user_id)
        time.sleep(random.uniform(0.5, 1.2))
        
        pw_input = driver.find_element(By.CSS_SELECTOR, sels["PW_INPUT"])
        human_move_and_click(driver, pw_input)
        human_paste(driver, user_pw)
        time.sleep(random.uniform(0.5, 1.2))
        
        try:
             login_selector = sels["SUBMIT_BTN"].replace(".", "\\.") if "#" in sels["SUBMIT_BTN"] and "\\" not in sels["SUBMIT_BTN"] else sels["SUBMIT_BTN"]
             if "log.login" in sels["SUBMIT_BTN"]:
                 login_btn = driver.find_element(By.ID, "log.login")
             else:
                 login_btn = driver.find_element(By.CSS_SELECTOR, login_selector)
        except:
             login_btn = driver.find_element(By.ID, "log.login")

        human_move_and_click(driver, login_btn)
        
        print("   ✅ 로그인 동작 완료")
        time.sleep(3)
        
    except Exception as e:
        print(f"   ⚠️ 로그인 실패: {e}")

# ==========================================
# 3. 글쓰기 흐름 (Write Flow)
# ==========================================
def insert_quote(driver, style="default", text=""):
    print(f"   💬 [Quote] 인용구 삽입 시도 ({style})...")
    try:
        sels_editor = selectors.SELECTORS["EDITOR"]
        try:
            quote_btn = driver.find_element(By.CSS_SELECTOR, sels_editor["QUOTE_BTN"])
            human_move_and_click(driver, quote_btn)
            time.sleep(random.uniform(0.5, 1.0))
        except:
            print("   ⚠️ 인용구 버튼 찾기 실패")
            return

        style_key = "QUOTE_OPT_" + style.upper()
        if style == "quotation_line": style_key = "QUOTE_OPT_LINE"
        elif style == "quotation_corner": style_key = "QUOTE_OPT_CORNER"
        else: style_key = "QUOTE_OPT_DEFAULT"
            
        try:
            opt_btn = driver.find_element(By.CSS_SELECTOR, sels_editor.get(style_key, sels_editor["QUOTE_OPT_DEFAULT"]))
            human_move_and_click(driver, opt_btn)
            time.sleep(random.uniform(0.5, 1.0))
        except:
            print(f"   ⚠️ 인용구 옵션({style}) 클릭 실패")
            return
            
        # 3. 텍스트 입력
        if text:
            # [FIX] 버튼 클릭 후 포커스가 유지되도록 ActionChains 사용
            time.sleep(1)
            try:
                human_typing(driver, None, text, use_action_chains=True)
            except Exception as e:
                print(f"   ⚠️ 텍스트 입력 실패: {e}")
                
            time.sleep(random.uniform(0.5, 1.0))
            ActionChains(driver).send_keys(Keys.ENTER).perform()
            
    except Exception as e:
        print(f"   ⚠️ 인용구 삽입 실패: {e}")

def naver_write_flow(driver, title, content_items):
    print("   ✍️ [Write] 글쓰기 시작...")
    try:
        safe_navigate(driver, "https://section.blog.naver.com")
        time.sleep(random.uniform(2, 4))
        sels_main = selectors.SELECTORS["MAIN"]
        try:
            if "WRITE_BTN_BLOG_HOME" in sels_main:
                btn = driver.find_element(By.CSS_SELECTOR, sels_main["WRITE_BTN_BLOG_HOME"])
                human_move_and_click(driver, btn)
            else:
                btn = driver.find_element(By.CSS_SELECTOR, sels_main["WRITE_BTN_PC"])
                human_move_and_click(driver, btn)
        except:
            print("   🔗 글쓰기 버튼 미발견, 직접 URL 이동")
            safe_navigate(driver, "https://blog.naver.com/GoBlogWrite.naver")
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        try: driver.switch_to.alert.accept()
        except: pass
    except Exception as e:
        print(f"   ⚠️ 글쓰기 진입 실패: {e}")
        return

    try:
        sels_frame = selectors.SELECTORS["EDITOR_FRAME"]
        if sels_frame["MAIN_FRAME"]:
            driver.switch_to.frame(sels_frame["MAIN_FRAME"])
    except: pass

    # 제목
    sels_editor = selectors.SELECTORS["EDITOR"]
    try:
        # [NEW] 작성 중인 글 팝업 처리 (취소)
        if "SAVED_DRAFT_CANCEL_BTN" in sels_editor:
            try:
                popup_cancel = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, sels_editor["SAVED_DRAFT_CANCEL_BTN"]))
                )
                print("   ⚠️ 작성 중인 글 팝업 감지 -> '취소' 클릭")
                human_move_and_click(driver, popup_cancel)
                time.sleep(1)
            except: pass

        title_selectors = sels_editor["TITLE_INPUT"].split(",")
        title_found = False
        for sel in title_selectors:
            try:
                title_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel.strip()))
                )
                human_move_and_click(driver, title_elem)
                title_found = True
                break
            except: continue
        if not title_found: print("   ⚠️ 제목 영역 못 찾음, 활성 요소에 입력 시도")
        
        human_typing(driver, driver.switch_to.active_element, title) 
        time.sleep(1)
        print("   ✅ 제목 작성 완료")
    except Exception as e:
        print(f"   ⚠️ 제목 작성 실패: {e}")

    # 본문 Loop
    try:
        content_selectors = sels_editor["CONTENT_AREA"].split(",")
        for sel in content_selectors:
            try:
                content_area = driver.find_element(By.CSS_SELECTOR, sel.strip())
                human_move_and_click(driver, content_area)
                break
            except: continue
        time.sleep(1)
        
        for item in content_items:
            if isinstance(item, str): item = {"type": "text", "content": item}
            itype = item.get("type", "text")
            content = item.get("content", "")
            
            if itype == "text":
                human_typing(driver, driver.switch_to.active_element, content)
                ActionChains(driver).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
            elif itype == "quote":
                insert_quote(driver, item.get("style", "default"), content)
                ActionChains(driver).send_keys(Keys.ENTER).perform()
            time.sleep(random.uniform(1.0, 2.0))
            human_scroll(driver, 50, 150)
        print("   ✅ 본문 작성 완료")
    except Exception as e:
        print(f"   ⚠️ 본문 작성 실패: {e}")

    # 발행
    sels_pub = selectors.SELECTORS["PUBLISH"]
    try:
        pub_btn = driver.find_element(By.CSS_SELECTOR, sels_pub["PUBLISH_BTN_1"])
        human_move_and_click(driver, pub_btn)
        time.sleep(random.uniform(1, 1.5))
        final_btn = driver.find_element(By.CSS_SELECTOR, sels_pub["PUBLISH_BTN_FINAL"])
        print("   ✅ 발행 버튼 찾음 (클릭은 보류)")
    except Exception as e:
        print(f"   ⚠️ 발행 실패: {e}")

# ==========================================
# 4. [NEW] 계정 육성 (Account Nurturing)
# ==========================================
def account_nurturing(driver, action_type="news", duration_min=5):
    """
    일반인 코스프레: 뉴스 읽기, 쇼핑 검색 등
    """
    print(f"   🌱 [Nurturing] 계정 육성 시작 ({action_type}, {duration_min}분)...")
    end_time = time.time() + (duration_min * 60)
    
    while time.time() < end_time:
        try:
            if action_type == "news":
                safe_navigate(driver, "https://news.naver.com")
                time.sleep(random.uniform(2, 4))
                
                # 랜덤 기사 클릭
                sels = selectors.SELECTORS["NEWS"]
                articles = driver.find_elements(By.CSS_SELECTOR, sels["MAIN_ARTICLE_LINK"])
                if articles:
                    target = random.choice(articles[:5]) # 상위 5개 중 하나
                    human_move_and_click(driver, target)
                    time.sleep(3)
                    
                    # 읽는 척 스크롤
                    human_scroll(driver, min_scroll=100, max_scroll=300)
                    time.sleep(random.uniform(5, 10))
                    
                    # 가끔 좋아요 누르기 (10% 확률)
                    if random.random() < 0.1:
                        try:
                             like_btn = driver.find_element(By.CSS_SELECTOR, sels["LIKE_BTN"])
                             human_move_and_click(driver, like_btn)
                             print("   👍 뉴스 좋아요 클릭")
                        except: pass
                
            elif action_type == "shopping":
                safe_navigate(driver, "https://shopping.naver.com/home")
                time.sleep(random.uniform(2, 4))
                human_scroll(driver)
                # (상세 로직은 추가 구현 가능)
                
            print(f"   ⏳ 육성 진행 중... {int(end_time - time.time())}초 남음")
        except Exception as e:
            print(f"   ⚠️ 육성 중 에러: {e}")
            time.sleep(5)

# ==========================================
# 5. [NEW] 지식인 전문가 (Naver Kin Solver)
# ==========================================
def naver_kin_solver(driver, keyword, blog_link):
    """
    지식 기부형 전문가: 답변이 없는 질문에 답변 + 블로그 홍보
    """
    print(f"   🎓 [Kin] 지식인 활동 시작: '{keyword}'")
    try:
        # 1. 지식인 검색
        url = f"https://kin.naver.com/search/list.naver?query={keyword}"
        safe_navigate(driver, url)
        time.sleep(2)
        
        # 2. 답변 0개인 질문 찾기 (정렬: 최신순/답변적은순 등 옵션 필요할 수 있음)
        # 여기서는 상세 검색 옵션 URL 파라미터 활용 권장 (&sort=date)
        
        sels = selectors.SELECTORS["KIN"]
        questions = driver.find_elements(By.CSS_SELECTOR, sels["QUESTION_LIST_ITEM"])
        
        target_url = None
        for q in questions:
            # 답변 수 확인 로직 필요 (텍스트 파싱)
            # 예: "답변 0" 텍스트 포함 여부 체크
            if "답변 0" in q.text:
                try:
                    link = q.find_element(By.TAG_NAME, "a").get_attribute("href")
                    target_url = link
                    break
                except: continue
        
        if not target_url:
            print("   ℹ️ 답변 0개인 질문을 찾지 못했습니다.")
            return

        print(f"   🎯 타겟 질문 발견: {target_url}")
        safe_navigate(driver, target_url)
        time.sleep(3)
        
        # 3. 답변하기 버튼 클릭
        try:
            ans_btn = driver.find_element(By.CSS_SELECTOR, sels["ANSWER_BTN"])
            human_move_and_click(driver, ans_btn)
        except:
             print("   ⚠️ 답변 버튼을 찾을 수 없거나 이미 답변함")
             return
             
        time.sleep(2)
        
        # 4. 답변 작성 (Gemini API 연동 필요, 여기서는 템플릿)
        # TODO: 실제 답변 생성 로직 연동
        answer_text = f"""
안녕하세요, {keyword} 관련해서 궁금해 하시는군요.
전문적인 견적이나 상세 비교가 필요하시면 차종별로 잘 정리된 자료를 참고해보시는 게 좋습니다.

더 자세한 정보는 제 블로그에 정리해 두었으니 확인해 보세요.
🔗 {blog_link}

도움이 되셨길 바랍니다!
        """
        
        # 에디터 프레임 전환 (지식인은 스마트에디터 2.0 사용 경우가 많음)
        try:
             driver.switch_to.frame("smart_editor2_content") # ID 가정
        except: pass
        
        human_typing(driver, driver.switch_to.active_element, answer_text)
        time.sleep(2)
        
        # 5. 등록 (실제 등록은 주의)
        # submit_btn = driver.find_element(By.CSS_SELECTOR, sels["SUBMIT_BTN"])
        # human_move_and_click(driver, submit_btn)
        print("   ✅ 답변 작성 완료 (등록 버튼 클릭은 보류)")
        
    except Exception as e:
        print(f"   ⚠️ 지식인 활동 실패: {e}")
