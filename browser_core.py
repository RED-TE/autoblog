# -*- coding: utf-8 -*-
# browser_core.py -- 브라우저 제어 v4
# UC(undetected-chromedriver) 우선, 실패 시 일반 Selenium 자동 폴백
# Chrome 버전 자동 감지, 잔존 프로세스 정리, 세션 유지

import os
import platform
import subprocess
import time
import random
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
import config

# -- 내장 User-Agent 풀 --
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
]

def _random_ua() -> str:
    return random.choice(_UA_POOL)


def get_sys_info():
    uname = platform.uname()
    return f"{uname.system} {uname.release} ({uname.machine})"


def safe_navigate(driver, url: str):
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
    except Exception:
        try: driver.execute_script("window.stop();")
        except: pass


def _kill_stale_chrome():
    """기존에 남아있는 봇용 Chrome/chromedriver 프로세스 정리"""
    print("   🧹 [Browser] 잔존 봇 전용 프로세스 정리 중 (사용자 일반 크롬은 보호됨)...")
    if platform.system() == "Windows":
        try:
            # 1. chromedriver는 무조건 정리
            subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"],
                           capture_output=True, timeout=3)
            # 2. 좀비 chrome.exe 정리: 사용자 일반 크롬은 죽이지 않고, 
            # 봇 프로필(browser_profiles)로 실행된 크롬만 선별 타격하여 Remote Debugging 포트 충돌 방지
            kill_cmd = 'wmic process where "name=\'chrome.exe\' and commandline like \'%browser_profiles%\'" call terminate'
            subprocess.run(kill_cmd, shell=True, capture_output=True, timeout=5)
        except Exception as e:
            print(f"   ⚠️ [Cleanup] 프로세스 정리 중 오류: {e}")
    else:
        try:
            subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True, timeout=3)
            subprocess.run("pkill -f 'chrome.*browser_profiles'", shell=True, capture_output=True, timeout=3)
        except Exception:
            pass
    time.sleep(0.5)


def _get_chrome_major_version() -> int | None:
    """설치된 Chrome 브라우저의 메이저 버전 번호를 자동으로 감지합니다."""
    # 1. Windows Registry 조회 (가장 정확함)
    if platform.system() == "Windows":
        try:
            import winreg
            reg_path = r"SOFTWARE\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}"
            for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    with winreg.OpenKey(root, reg_path) as key:
                        version_str, _ = winreg.QueryValueEx(key, "pv")
                        major = int(version_str.split(".")[0])
                        print(f"   [Browser] Registry에서 Chrome v{major} 감지")
                        return major
                except: continue
        except Exception: pass

    # 2. 파일 경로 탐색 (기존 방식)
    chrome_paths = {
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ],
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        "Linux":  ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"],
    }
    paths = chrome_paths.get(platform.system(), [])
    for path in paths:
        if os.path.exists(path):
            try:
                if platform.system() == "Windows":
                    # Windows에서는 wmic 또는 powershell로 확인하는 것이 더 안정적일 수 있음
                    cmd = f'powershell -command "(Get-Item \'{path}\').VersionInfo.ProductVersion"'
                    out = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
                    major = int(out.split(".")[0])
                    print(f"   [Browser] File에서 Chrome v{major} 감지: {path}")
                    return major
                else:
                    out = subprocess.check_output([path, "--version"], stderr=subprocess.DEVNULL, timeout=5)
                    version_str = out.decode().strip()
                    major = int(version_str.split()[-1].split(".")[0])
                    print(f"   [Browser] Chrome 감지: v{major} | {path}")
                    return major
            except Exception:
                pass
    return None


def _inject_fingerprint(driver):
    """Canvas/WebGL 노이즈 + Navigator 속성 조작으로 디지털 지문 변조"""
    fingerprint_js = f"""
        const _toDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function toDataURL(type) {{
            const ctx = this.getContext('2d');
            if (ctx) {{
                try {{
                    const noise = {random.uniform(0.00001, 0.0001):.6f};
                    const id = ctx.getImageData(0,0,1,1);
                    id.data[0] = (id.data[0] + noise*255) % 256;
                    ctx.putImageData(id,0,0);
                }} catch(e) {{}}
            }}
            return _toDataURL.apply(this, arguments);
        }};
        
        const _getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function getParameter(p) {{
            if (p === 37445) return 'Google Inc. ({random.choice(["NVIDIA","AMD","Intel"])})';
            if (p === 37446) return 'ANGLE ({random.choice(["NVIDIA GeForce RTX 3060","AMD Radeon RX 6600","Intel Iris Xe"])})';
            return _getParam.apply(this, arguments);
        }};
        
        // Anti-Bot: 우회 함수의 JS toString() [native code] 서명 위장
        const _toString = Function.prototype.toString;
        Function.prototype.toString = function toString() {{
            if (this === HTMLCanvasElement.prototype.toDataURL) return 'function toDataURL() {{ [native code] }}';
            if (this === WebGLRenderingContext.prototype.getParameter) return 'function getParameter() {{ [native code] }}';
            if (this === Function.prototype.toString) return 'function toString() {{ [native code] }}';
            return _toString.apply(this, arguments);
        }};
        
        // Anti-Bot: 자동화 제어 플래그(navigator.webdriver) 숨기기
        Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
        Object.defineProperty(navigator, 'languages', {{get: () => ['ko-KR','ko','en-US','en']}});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {random.choice([4,6,8,12])}}});
    """
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                               {"source": fingerprint_js})
    except Exception:
        pass


def get_driver(profile_name: str = "main_profile", headless: bool = False) -> webdriver.Chrome | None:
    """
    Chrome 드라이버를 반환합니다.
    - UC(undetected-chromedriver) 우선 시도: 자동화 탐지 차단
    - UC 실패 시 일반 Selenium으로 자동 폴백
    - 실행 전 잔존 chromedriver 프로세스 정리
    """
    _kill_stale_chrome()

    chrome_version = _get_chrome_major_version()
    w, h = random.choice(config.SCREEN_RESOLUTIONS)
    random_ua = _random_ua()

    profile_path = os.path.join(os.getcwd(), "browser_profiles", profile_name)
    os.makedirs(profile_path, exist_ok=True)

    # [안정성 강화] 비정상 종료 시 남아있는 프로필 Lock 파일 강제 삭제 (다중 계정 접속 오류 방지)
    try:
        for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket", "Lockfile"]:
            lock_p = os.path.join(profile_path, lock_file)
            if os.path.exists(lock_p):
                os.unlink(lock_p)
                print(f"   🧹 [Cleanup] 락 파일 삭제 완료 ({lock_file})")
    except Exception as e:
        print(f"   ⚠️ [Cleanup] 락 파일 삭제 실패: {e}")

    # =========================================================
    # [1차 시도] Subprocess + Remote Debugging (캡차 우회 최강 1티어)
    # =========================================================
    print(f"   [Browser] Remote Debugging 모드 시도... (Chrome v{chrome_version})")
    try:
        import subprocess
        chrome_path = None
        win_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
        for path in win_paths:
            if os.path.exists(path):
                chrome_path = path
                break
                
        if not chrome_path:
            try:
                chrome_path = subprocess.check_output(["where", "chrome"], shell=True).decode().strip().split('\n')[0]
            except: pass
            
        if not chrome_path or not os.path.exists(chrome_path):
            raise Exception("크롬 바이너리를 찾을 수 없습니다.")

        debug_port = random.randint(9222, 9299)
        cmd = [
            chrome_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={profile_path}",
            "--no-first-run",
            "--no-default-browser-check",
            f"--window-size={w},{h}",
            "--lang=ko-KR",
            "--accept-lang=ko-KR,ko,en-US,en"
        ]
        if headless:
            cmd.append("--headless=new")
            
        print(f"      ▶️ Chrome 일반 프로세스 실행 중 (Port: {debug_port}, Lang: ko-KR)")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        debug_options = webdriver.ChromeOptions()
        debug_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        
        driver = webdriver.Chrome(options=debug_options)
        driver.browser_proc = proc
        
        # 핑거프린트 주입
        _inject_fingerprint(driver)
        print(f"   ✅ [Browser] Remote Debugging 연결 성공! | Profile: {profile_name}")
        return driver

    except Exception as e:
        print(f"   ⚠️ [Browser] Remote Debugging 실패 ({e}) -> Selenium 폴백 시도")


    # =========================================================
    # [2차 시도] 일반 Selenium (자동화 플래그 숨김 적용)
    # =========================================================
    try:
        se_options = webdriver.ChromeOptions()
        se_options.add_argument(f"--window-size={w},{h}")
        se_options.add_argument("--no-sandbox")
        se_options.add_argument("--disable-dev-shm-usage")
        se_options.add_argument("--lang=ko-KR")
        se_options.add_argument("--accept-lang=ko-KR,ko,en-US,en")
        se_options.add_argument("--disable-blink-features=AutomationControlled")
        se_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        se_options.add_experimental_option("useAutomationExtension", False)
        se_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 1,
        })
        if headless:
            se_options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=se_options)
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": random_ua})
        _inject_fingerprint(driver)
        print(f"   [Browser] Selenium 폴백 성공 | {w}x{h}")
        return driver

    except Exception as e:
        print(f"   [Browser] Selenium 폴백도 실패: {e}")
        return None


def close_session(driver):
    """세션 종료: 프로세스만 닫고, 쿠키와 스토리지(프로필)는 영구 보존"""
    try:
        driver.quit()
        print("   [Browser] 프로세스 종료 (세션/쿠키는 보존됨)")
    except Exception:
        pass


def click_element(driver, selector: str, timeout: int = 10) -> bool:
    """
    범용 클릭 헬퍼:
    1. CSS / XPath 자동 감지
    2. 스크롤 후 클릭
    3. JS 클릭 폴백
    """
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        by = (By.XPATH
              if selector.startswith("//") or selector.startswith("(") or selector.startswith("./")
              else By.CSS_SELECTOR)

        elem = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
        time.sleep(0.4)
        try:
            elem.click()
        except Exception:
            driver.execute_script("arguments[0].click();", elem)
        return True

    except Exception as e:
        print(f"   [Browser] 클릭 실패 ({selector[:40]}): {e}")
        return False
