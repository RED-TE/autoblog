
# -*- coding: utf-8 -*-
# human_action.py
# 인간 행동 모사 (타이핑, 마우스, 스크롤) 담당 (V2 Architecture)

import os
import time
import random
import platform
import pyperclip
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def slow_down(context="Action"):
    delay = random.randint(2, 5)
    print(f"   ☕ [Slow Mode] {context} 후 {delay}초 대기 중...")
    time.sleep(delay)

def human_typing(driver, element, text, speed=(0.05, 0.09), use_action_chains=True):
    """
    사람처럼 자연스럽게 타이핑 (600-800타/분 속도)
    
    Args:
        driver: Selenium WebDriver
        element: 입력할 요소 (사용 안 함, 호환성 유지)
        text: 입력할 텍스트
        speed: (최소, 최대) 타이핑 속도 (초)
    """
    try:
        # Ctrl 키 해제 (중요!)
        try:
            ActionChains(driver).key_up(Keys.CONTROL).key_up(Keys.ALT).key_up(Keys.SHIFT).perform()
        except: pass
        
        typo_chars = "qwertyuiopasdfghjklzxcvbnm"
        
        for i, char in enumerate(text):
            # 오타 로직 (첫/끝 글자 제외)
            if random.random() < 0.05 and 0 < i < len(text) - 1:
                wrong = random.choice(typo_chars)
                ActionChains(driver).send_keys(wrong).perform()
                time.sleep(random.uniform(0.1, 0.3))
                ActionChains(driver).send_keys(Keys.BACKSPACE).perform()
                time.sleep(random.uniform(0.1, 0.2))
            
            ActionChains(driver).send_keys(char).perform()
            
            delay = random.uniform(speed[0], speed[1])
            
            # 가속 구간
            if random.random() < 0.3:
                delay *= 0.4
            
            # 문장 부호 뒤 지연
            if char in ".?!,":
                delay += 0.2
            
            time.sleep(delay)
            
    except Exception as e:
        print(f"   ⚠️ Typing Error: {e}")

def human_paste(driver, text):
    """
    클립보드를 통한 빠른 붙여넣기 (텍스트 및 이미지)
    
    Args:
        driver: Selenium WebDriver
        text: 붙여넣을 텍스트 (이미지 복붙 등 텍스트가 필요 없을 때는 "" 빈 문자열 전달)
    """
    try:
        # text가 빈 문자열이 아닐 때만 클립보드를 오버라이드
        if text:
            text_str = str(text).strip()
            if text_str:
                pyperclip.copy(text_str)
                time.sleep(0.5)
        
        # OS별 붙여넣기 단축키 전송 (ActionChains 활용)
        IS_MAC = platform.system() == "Darwin"
        key = Keys.COMMAND if IS_MAC else Keys.CONTROL
        
        ActionChains(driver).key_down(key).send_keys('v').key_up(key).perform()
        time.sleep(random.uniform(0.5, 1.0))
        
    except Exception as e:
        print(f"   ⚠️ Paste Error: {e}")
        # fallback for text only
        if text and str(text).strip():
            try:
                from human_action import human_typing
                human_typing(driver, None, text)
            except: pass

def copy_image_to_clipboard(image_path: str) -> bool:
    """
    Windows PowerShell을 사용하여 이미지 파일을 클립보드에 복사합니다.
    (pyperclip은 텍스트만 지원하므로 PowerShell 활용)
    """
    if platform.system() != "Windows":
        print(f"   ⚠️ [Clipboard] Windows 외 운영체제 미지원: {platform.system()}")
        return False
        
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        print(f"   ⚠️ [Clipboard] 파일 없음: {abs_path}")
        return False
        
    try:
        import win32clipboard
        from PIL import Image
        import io

        # 1. 이미지를 BMP DIB 포맷으로 변환 (네이버가 잘 인식함)
        image = Image.open(abs_path)
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # BMP 헤더 제거
        output.close()

        # 2. 클립보드에 데이터 설정 (재시도 로직 포함)
        for attempt in range(3):
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                print(f"   📋 [Clipboard] DIB 포맷 복사 성공 (크기: {len(data)})")
                time.sleep(1.0)
                return True
            except Exception as clip_err:
                print(f"   ⚠️ [Clipboard] 재시도 {attempt+1}: {clip_err}")
                time.sleep(1.0)
                if attempt == 2:
                    raise clip_err
        return False
    except Exception as e:
        print(f"   ⚠️ [Clipboard] DIB 변환/복사 실패 - PowerShell로 폴백: {e}")
        try:
            import subprocess
            cmd = ["powershell", "-Command", f"Set-Clipboard -Path '{abs_path}'"]
            subprocess.run(cmd, check=True, capture_output=True, creationflags=0x08000000)
            time.sleep(1.0)
            print(f"   📋 [Clipboard] PowerShell 복사 성공")
            return True
        except Exception as pe:
            print(f"   ⚠️ [Clipboard] PowerShell 폴백도 실패: {pe}")
            return False

def human_scroll(driver, min_scroll=200, max_scroll=600):
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        current_pos = 0
        while current_pos < total_height:
            scroll_amount = random.randint(min_scroll, max_scroll)
            current_pos += scroll_amount
            
            # 부드러운 스크롤 (JS 활용)
            driver.execute_script(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}});")
            
            # 읽는 척 (10% 확률로 역스크롤)
            if random.random() < 0.1:
                time.sleep(random.uniform(1.0, 2.0))
                driver.execute_script("window.scrollBy({top: -100, behavior: 'smooth'});")
                time.sleep(0.5)
                driver.execute_script("window.scrollBy({top: 100, behavior: 'smooth'});")
                
            time.sleep(random.uniform(1.0, 3.0)) # 체류 시간 증가
            if current_pos > 2500 and random.random() < 0.2:
                break
    except: pass

def human_move_and_click(driver, element):
    try:
        actions = ActionChains(driver)
        # 미세하게 좌표 오프셋 추가
        actions.move_to_element_with_offset(element, random.randint(-5, 5), random.randint(-5, 5))
        actions.pause(random.uniform(0.3, 0.8)) # 망설임
        actions.click()
        actions.perform()
    except:
        time.sleep(random.uniform(0.2, 0.5))
        element.click()


def ensure_editor_focus(driver):
    """
    네이버 에디터의 커서를 문서 맨 끝으로 이동
    (이미지 클릭 해제 및 텍스트 입력 준비)
    
    Returns:
        bool: 성공 여부
    """
    try:
        IS_MAC = platform.system() == "Darwin"
        cmd = Keys.COMMAND if IS_MAC else Keys.CONTROL
        actions = ActionChains(driver)
        
        # 1. ESC 3번으로 모든 선택 해제
        for _ in range(3):
            actions.send_keys(Keys.ESCAPE).pause(0.1)
        
        # 2. Ctrl+End 3번으로 문서 끝 이동
        for _ in range(3):
            actions.key_down(cmd).send_keys(Keys.END).key_up(cmd).pause(0.1)
        
        actions.perform()
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"   ⚠️ 포커스 확보 실패: {e}")
        return False


def apply_final_alignment(driver, align_val):
    """
    본문 전체를 선택하여 정렬 적용
    
    Args:
        align_val: "왼쪽"/"가운데"/"오른쪽"
    
    단축키:
        - 왼쪽: Ctrl+Alt+L
        - 가운데: Ctrl+Alt+C
        - 오른쪽: Ctrl+Alt+R
    """
    print(f"   📏 [Alignment] 본문 전체 정렬 적용: {align_val}")
    
    IS_MAC = platform.system() == "Darwin"
    cmd = Keys.COMMAND if IS_MAC else Keys.CONTROL
    actions = ActionChains(driver)
    
    # 1. 전체 선택 (Ctrl+A)
    actions.key_down(cmd).send_keys('a').key_up(cmd).perform()
    time.sleep(0.5)
    
    # 2. 정렬 단축키
    key_map = {
        "왼쪽": 'l', "left": 'l',
        "가운데": 'c', "center": 'c',
        "오른쪽": 'r', "right": 'r'
    }
    char_code = key_map.get(str(align_val).lower(), 'l')
    
    actions.reset_actions()
    actions.key_down(Keys.CONTROL).key_down(Keys.ALT).send_keys(char_code).key_up(Keys.ALT).key_up(Keys.CONTROL).perform()
    time.sleep(1.0)
    
    # 3. 선택 해제
    actions.reset_actions()
    actions.send_keys(Keys.RIGHT).perform()

def inject_image_via_js(driver, image_path, target_element=None):
    """
    OS 포커스를 뺏기지 않고 순수 JavaScript를 통해 이미지를 붙여넣기하는 최후의 보루 함수.
    로컬 파일을 Base64로 읽은 뒤 브라우저 컨텍스트에서 File 객체를 만들고, 
    DataTransfer를 통해 Paste 이벤트를 발생시켜 스마트에디터에 직격합니다.
    """
    import base64
    import mimetypes
    
    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        print(f"   ⚠️ [JS Paste] 파일 없음: {abs_path}")
        return False
        
    mime_type, _ = mimetypes.guess_type(abs_path)
    if not mime_type:
        mime_type = 'image/jpeg'
        
    try:
        with open(abs_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"   ⚠️ [JS Paste] 파일 읽기 에러: {e}")
        return False
        
    filename = os.path.basename(abs_path)
    
    script = """
    var b64Data = arguments[0];
    var contentType = arguments[1];
    var filename = arguments[2];
    var target = arguments[3];
    
    try {
        var byteCharacters = atob(b64Data);
        var byteArrays = [];
        for (var offset = 0; offset < byteCharacters.length; offset += 512) {
            var slice = byteCharacters.slice(offset, offset + 512);
            var byteNumbers = new Array(slice.length);
            for (var i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            var byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }
        var blob = new Blob(byteArrays, {type: contentType});
        var file = new File([blob], filename, {type: contentType, lastModified: new Date().getTime()});
        
        var dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        
        var pasteEvent = new ClipboardEvent('paste', {
            clipboardData: dataTransfer,
            bubbles: true,
            cancelable: true
        });
        
        var el = target ? target : document.activeElement;
        el.dispatchEvent(pasteEvent);
        return true;
    } catch(e) {
        return e.toString();
    }
    """
    
    try:
        res = driver.execute_script(script, img_b64, mime_type, filename, target_element)
        if res is True:
            return True
        else:
            print(f"   ⚠️ [JS Paste] 브라우저 내 에러: {res}")
            return False
    except Exception as e:
        print(f"   ⚠️ [JS Paste] 파이썬 전송 에러: {e}")
        return False

