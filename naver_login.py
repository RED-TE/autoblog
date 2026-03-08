# -*- coding: utf-8 -*-
# naver_login.py — 네이버 로그인 전담 모듈
# [리팩토링] naver_core.py에서 로그인 관련 코드를 분리
# 외부 import: import naver_login 또는 기존 import naver_core as naver 모두 호환.

import time
import random
import platform
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import browser_core as browser
import human_action as human
import ui_selectors as selectors


# ==========================================
# 로그인 예외
# ==========================================

class LoginError(Exception):
    pass


# ==========================================
# 내부 헬퍼
# ==========================================

def _check_login_result(driver, deadline_sec=60) -> str:
    """로그인 버튼 클릭 후 결과 감지."""
    REMAIN_LOGIN_URLS = ["nidlogin.login", "nid.naver.com/nid/", "nid.naver.com/login"]
    FAIL_INDICATORS   = ["#err_common", "#new_err", ".login_error", "#err_pw"]
    CAPTCHA_PATTERNS  = ["captcha", "otp", "2step", "lock", "recaptcha",
                         "nidlogin.login?svctype", "nid.naver.com/login/sso"]

    deadline = time.time() + deadline_sec
    status   = "unknown"

    while time.time() < deadline:
        cur_url = driver.current_url
        if any(p in cur_url for p in CAPTCHA_PATTERNS):
            status = "captcha_or_2fa"; break
        for sel in FAIL_INDICATORS:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed() and el.text.strip():
                    print(f"   [Login] 에러 감지: {el.text.strip()[:60]}")
                    status = "error_shown"; break
            except: pass
        if status == "error_shown": break
        if not any(p in cur_url for p in REMAIN_LOGIN_URLS + ["nidlogin"]):
            status = "success"; break
        time.sleep(0.8)
    else:
        status = "timeout"

    return status


def _handle_captcha(driver):
    """캡차/2FA 감지 시 무한 대기"""
    try:
        import telegram_bot
        telegram_bot.send_message("🔐 [로그인 대기] 캡차 또는 2단계 인증 발생!")
    except: pass
    print("   ⏳ [캡차/2FA 발생] 수동 해결 대기...")

    STILL_BLOCKED = ["captcha", "otp", "2step", "lock", "nidlogin.login", "nid.naver.com/nid/"]
    wait_time = 0
    while True:
        if not any(p in driver.current_url for p in STILL_BLOCKED):
            print("   ✅ [캡차 해결] 로그인 완료")
            try:
                import telegram_bot
                telegram_bot.send_message("✅ 캡차 해결 완료")
            except: pass
            break
            
        time.sleep(5)
        wait_time += 5
        if wait_time % 60 == 0:
            print(f"   ⏳ 대기 중... ({wait_time}초)")


def _finalize_login(driver):
    """로그인 완료 처리"""
    time.sleep(1.5)
    browser.safe_navigate(driver, "https://www.naver.com")
    time.sleep(2)
    account_name = ""
    try:
        for sel in [".gnb_my_nameid", ".MyView-module__user_name___H0LVh", ".MyNaver__user_name"]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                account_name = el.text.strip()
                if account_name: break
            except: pass
    except: pass
    print(f"   ✅ [Login] 로그인 성공! 계정: {account_name or '(확인 불가)'}")
    
    try:
        print("   🔍 [Anti-Bot] 로그인 직후 웜업...")
        time.sleep(random.uniform(2.0, 4.0))
        for _ in range(2):
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 500)});")
            time.sleep(random.uniform(1.5, 3.0))
            
        print("   🧹 [Cleanup] 탭 정리...")
        all_handles = driver.window_handles
        if len(all_handles) > 1:
            main_handle = all_handles[0]
            for handle in all_handles[1:]:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except: pass
            driver.switch_to.window(main_handle)
            
        print("   ✅ [Anti-Bot] 웜업 완료")
    except Exception as e:
        print(f"   ⚠️ 웜업 오류: {e}")


# ==========================================
# 메인 로그인 함수
# ==========================================

def login(driver, user_id, user_pw):
    """로그인 3단계 전략"""
    print(f"   [Login] 로그인 시작 ({user_id})")

    try:
        # STEP 1: 세션 확인
        browser.safe_navigate(driver, "https://www.naver.com")
        time.sleep(random.uniform(1.5, 2.5))

        SESSION_SELECTORS = [".MyView-module__my_info___S24qY", ".gnb_my_nameid", ".MyNaver__user_name"]
        for sel in SESSION_SELECTORS:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    print(f"   ✅ [Login] 세션 유지 중")
                    return
            except: pass
        print("   [Login] 세션 없음 — 로그인 진행")

        # Pre-login 웜업
        def _behavior_warmup(driver, context="Pre-login"):
            try:
                print(f"   🔍 [Anti-Bot] 웜업({context})...")
                activities = []
                if random.random() < 0.6: activities.append("news")
                if random.random() < 0.5: activities.append("shopping")
                if random.random() < 0.4: activities.append("cafe")
                if not activities: activities = ["news"]
                
                for activity in activities:
                    try:
                        if activity == "news":
                            print(f"      📰 [{context}] 뉴스 탭...")
                            news_tab = driver.find_element(By.CSS_SELECTOR, "a[href*='news.naver.com']")
                            human.human_move_and_click(driver, news_tab)
                        elif activity == "shopping":
                            print(f"      🛒 [{context}] 쇼핑 탭...")
                            shop_tab = driver.find_element(By.CSS_SELECTOR, "a[href*='shopping.naver.com']")
                            human.human_move_and_click(driver, shop_tab)
                        elif activity == "cafe":
                            print(f"      ☕ [{context}] 카페 탭...")
                            cafe_tab = driver.find_element(By.CSS_SELECTOR, "a[href*='section.cafe.naver.com']")
                            human.human_move_and_click(driver, cafe_tab)
                            
                        time.sleep(random.uniform(2, 4))
                        for _ in range(random.randint(2, 3)):
                            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 600)});")
                            time.sleep(random.uniform(1.5, 3.0))
                        driver.back()
                        time.sleep(random.uniform(1.5, 2.5))
                    except: pass
                print(f"   ✅ [Anti-Bot] 웜업 완료")
            except Exception as e:
                print(f"   ⚠️ 웜업 중단: {e}")

        _behavior_warmup(driver, "Pre-login")
        
        # 탭 정리
        all_handles = driver.window_handles
        if len(all_handles) > 1:
            main_handle = all_handles[0]
            for handle in all_handles[1:]:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except: pass
            driver.switch_to.window(main_handle)
            print("   🧹 [Pre-login] 탭 정리")

        if "naver.com" not in driver.current_url or "nidlogin" in driver.current_url:
            browser.safe_navigate(driver, "https://www.naver.com")
            time.sleep(random.uniform(1.5, 2.5))

        # STEP 2: 로그인 버튼 클릭
        print("   [Login] 로그인 버튼 클릭...")
        login_btn_selectors = [
            ".MyView-module__link_login___HpHMW",
            "a.link_login",
            "a[href*='nid.naver.com/nidlogin.login']"
        ]
        clicked = False
        for s in login_btn_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, s)
                if btn.is_displayed():
                    human.human_move_and_click(driver, btn)
                    clicked = True
                    print(f"   [Login] 버튼 클릭 ({s})")
                    time.sleep(random.uniform(2.0, 3.5))
                    break
            except: pass
            
        if not clicked:
            print("   [Login] 직접 URL 이동")
            browser.safe_navigate(driver, "https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com%2F")
            time.sleep(random.uniform(2.0, 3.5))

        # STEP 2-A: 저장된 계정
        SAVED_ACCOUNT_SELECTORS = [".saved_id", ".keep_login_text", "a.id_keep", ".frmLoginBtn"]
        clicked_saved = False
        for s in SAVED_ACCOUNT_SELECTORS:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, s)
                if btn.is_displayed():
                    human.human_move_and_click(driver, btn)
                    print("   [Login] 저장 계정 클릭")
                    clicked_saved = True
                    break
            except: pass

        if clicked_saved:
            status = _check_login_result(driver, deadline_sec=20)
            if status == "success":
                print("   ✅ [Login] 저장 계정 성공")
                return _finalize_login(driver)
            elif status == "captcha_or_2fa":
                _handle_captcha(driver)
                return _finalize_login(driver)
            else:
                print(f"   [Login] 저장 계정 실패 → ID/PW 입력")
                browser.safe_navigate(driver, "https://nid.naver.com/nidlogin.login")
                time.sleep(random.uniform(1.5, 2.5))

        # STEP 3: 아이디/비밀번호
        sels = selectors.SELECTORS["LOGIN"]

        if "nidlogin" not in driver.current_url:
            print(f"   ⚠️ [Login] 강제 진입...")
            browser.safe_navigate(driver, "https://nid.naver.com/nidlogin.login?mode=form")
            time.sleep(random.uniform(1.5, 2.5))

        try:
            id_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sels["ID_INPUT"]))
            )
        except Exception:
            raise LoginError(f"아이디 입력창 없음")
        
        # 자동 완성 시도
        try:
            print("   💡 [Login] 자동 완성 확인...")
            for btn_sel in ["#log\\.login", "button[type=submit]", ".btn_login"]:
                try:
                    pre_btn = driver.find_element(By.CSS_SELECTOR, btn_sel)
                    if pre_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", pre_btn)
                        break
                except: pass
            
            time.sleep(2.0)
            
            try:
                alert = driver.switch_to.alert
                has_alert = True
                alert.dismiss()
            except:
                has_alert = False
                
            if not has_alert and "nidlogin.login" not in driver.current_url:
                print("   ✅ [Login] 자동 완성 성공!")
                status = _check_login_result(driver, deadline_sec=10)
                if status == "success":
                    return _finalize_login(driver)
                elif status == "captcha_or_2fa":
                    _handle_captcha(driver)
                    return _finalize_login(driver)
            else:
                print("   ⚠️ [Login] 수동 입력으로 전환")
        except: pass

        # 입력 헬퍼
        def _robust_input(element, text, field_name):
            try: element.click()
            except: driver.execute_script("arguments[0].click();", element)
            time.sleep(0.2)
            
            act = ActionChains(driver)
            act.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(0.1)
            ActionChains(driver).send_keys(Keys.DELETE).perform()
            time.sleep(0.1)
            
            human.human_paste(driver, text)
            
        print("   [Login] 아이디/비밀번호 입력")
        _robust_input(id_input, user_id, "아이디")
        
        pw_input = driver.find_element(By.CSS_SELECTOR, sels["PW_INPUT"])
        _robust_input(pw_input, user_pw, "비밀번호")

        driver.execute_script("document.body.click();")
        time.sleep(0.5)
        
        for btn_sel in ["#log\\.login", "button[type=submit]", ".btn_login"]:
            try:
                login_btn = driver.find_element(By.CSS_SELECTOR, btn_sel)
                if login_btn.is_displayed():
                    time.sleep(random.uniform(0.4, 0.9))
                    try:
                        human.human_move_and_click(driver, login_btn)
                    except:
                        driver.execute_script("arguments[0].click();", login_btn)
                    break
            except: pass

        status = _check_login_result(driver, deadline_sec=60)
        if status == "captcha_or_2fa":
            _handle_captcha(driver)
        elif status != "success":
            msg_map = {
                "error_shown": "아이디/비밀번호 오류",
                "timeout":     "60초 타임아웃",
                "unknown":     "상태 불명",
            }
            raise LoginError(msg_map.get(status, status))

        _finalize_login(driver)

    except LoginError:
        raise
    except Exception as e:
        raise LoginError(f"로그인 예외: {e}")
