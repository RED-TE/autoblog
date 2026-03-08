# -*- coding: utf-8 -*-
# dwell_bot.py — 체류 시간 시뮬레이터
# 발행 후 3~5분간 사람이 글을 읽는 행동을 정밀하게 재현합니다.
# D.I.A+ 알고리즘의 핵심 지표: 체류 시간 + 스크롤 깊이 + 유의미한 액션

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def _smooth_scroll(driver, delta: int, steps: int = 8):
    """부드러운 스크롤 — 한 번에 픽셀이 아니라 나눠서 내립니다."""
    step_size = delta // steps
    for _ in range(steps):
        driver.execute_script(f"window.scrollBy(0, {step_size});")
        time.sleep(random.uniform(0.05, 0.15))


def _mouse_wander(driver):
    """마우스를 화면 중간쯤 랜덤하게 이동시킵니다."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        ac = ActionChains(driver)
        for _ in range(random.randint(2, 5)):
            x = random.randint(-200, 200)
            y = random.randint(-100, 100)
            ac.move_to_element_with_offset(body, x, y).pause(random.uniform(0.1, 0.5))
        ac.perform()
    except Exception:
        pass


def _pause_on_image(driver):
    """
    이미지 위에서 1~3초 멈춤.
    네이버 D.I.A+는 이미지 체류 시간을 '유의미한 액션'으로 인식합니다.
    """
    try:
        images = driver.find_elements(By.CSS_SELECTOR,
            "div.se-image-resource img, .se-module-image img, img.se_mediaImage")
        if not images:
            images = driver.find_elements(By.CSS_SELECTOR, "img")

        for img in images[:5]:  # 최대 5개 이미지
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", img)
                time.sleep(random.uniform(1.5, 3.5))
                # 이미지 위에 마우스 올리기
                ActionChains(driver).move_to_element(img).perform()
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                pass
    except Exception:
        pass


def simulate_reading(driver, post_url: str, duration_min: float = None):
    """
    발행된 블로그 포스트를 사람이 읽는 것처럼 시뮬레이션합니다.

    행동 순서:
    1. 포스트 URL로 이동
    2. 1~2초 대기 (로딩 인식)
    3. 천천히 스크롤 다운 (읽는 속도)
    4. 이미지 위에서 멈춤
    5. 중간에 위로 스크롤 (재독 행동)
    6. 마우스 랜덤 이동
    7. 다시 천천히 끝까지 스크롤
    8. 총 duration_min 분 유지
    """
    if duration_min is None:
        duration_min = random.uniform(3.0, 5.0)

    print(f"   ⏱️  [Dwell] 체류 시뮬레이션 시작 ({duration_min:.1f}분 목표): {post_url}")

    try:
        from browser_core import safe_navigate
        safe_navigate(driver, post_url)
    except Exception:
        driver.get(post_url)

    time.sleep(random.uniform(1.5, 2.5))

    end_time = time.time() + (duration_min * 60)
    scroll_pos = 0
    phase = "read"  # read → image → reread → end

    while time.time() < end_time:
        remaining = end_time - time.time()

        if phase == "read":
            # ── 1단계: 천천히 읽으며 스크롤 (200~400px씩) ──
            page_h = driver.execute_script("return document.body.scrollHeight")
            scroll_amount = random.randint(200, 400)
            _smooth_scroll(driver, scroll_amount)
            scroll_pos += scroll_amount

            # 읽는 중 멈춤 (500~2500ms)
            time.sleep(random.uniform(0.5, 2.5))

            if scroll_pos >= page_h * 0.6:
                # 60% 이상 읽었으면 이미지 phase로
                phase = "image"
                print("   👁️  [Dwell] 이미지 감상 구간...")

        elif phase == "image":
            # ── 2단계: 이미지 위에서 멈춤 ──
            _pause_on_image(driver)
            phase = "reread"

        elif phase == "reread":
            # ── 3단계: 위로 스크롤 (재독 행동) ──
            print("   🔄 [Dwell] 재독 시뮬레이션 (위로 스크롤)...")
            back_amount = random.randint(500, 1500)
            driver.execute_script(f"window.scrollBy(0, -{back_amount});")
            scroll_pos = max(0, scroll_pos - back_amount)
            time.sleep(random.uniform(2, 4))
            _mouse_wander(driver)
            phase = "finish"

        elif phase == "finish":
            # ── 4단계: 끝까지 스크롤 후 대기 ──
            page_h = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(3, 6))
            # 남은 시간은 그냥 대기 (자연스러운 체류)
            if remaining > 15:
                wait = min(remaining - 5, random.uniform(10, 20))
                print(f"   ⌛ [Dwell] 남은 체류 {remaining:.0f}초 중 {wait:.0f}초 대기...")
                time.sleep(wait)
            else:
                time.sleep(max(0, remaining))
                break

    elapsed = duration_min * 60 - max(0, end_time - time.time())
    print(f"   ✅ [Dwell] 체류 완료 ({elapsed:.0f}초 / {duration_min*60:.0f}초 목표)")
