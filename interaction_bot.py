# -*- coding: utf-8 -*-
# interaction_bot.py — 소통 자동화 모듈
# ① 내 포스트 댓글에 AI 답글  ② 이웃 포스트 공감/댓글
# C-Rank의 핵심: 진정성 있는 소통 → 인기도 점수 획득

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import gemini_core
import browser_core as browser
import human_action as human


# ── 헬퍼 ───────────────────────────────────────────────────────
def _gen_reply(comment_text: str, keyword: str = "") -> str:
    """댓글 내용을 읽고 Gemini로 자연스러운 답글 생성"""
    prompt = f"""
다음은 내 블로그 댓글입니다:
"{comment_text}"

블로그 주제: 자동차 장기렌트/리스 ({keyword})

이 댓글에 대한 자연스럽고 따뜻한 답글을 한국어로 작성하세요.
- 2~3문장 이내로 짧게
- 구체적인 정보가 필요하면 DM 유도
- 이모티콘 1~2개 사용
- 광고성 문구 없이 진심 어린 어조

답글만 출력하세요.
"""
    result = gemini_core.client.generate(prompt)
    return result.strip() if result else "감사합니다 😊 궁금한 점 있으시면 언제든지 연락 주세요!"


def _gen_comment(post_title: str) -> str:
    """이웃 포스트에 달 자연스러운 공감 댓글 생성"""
    prompt = f"""
다음 블로그 포스팅 제목에 어울리는 짧은 공감 댓글을 한국어로 작성하세요:
제목: "{post_title}"

조건:
- 1~2문장
- 진심 어린 공감 표현
- 광고/홍보 없이
- 자연스러운 이웃 댓글 스타일

댓글 텍스트만 출력하세요.
"""
    result = gemini_core.client.generate(prompt)
    return result.strip() if result else "정말 유익한 정보 감사해요! 잘 봤습니다 😊"


# ── 메인 기능 ────────────────────────────────────────────────────
def reply_to_comments(driver, blog_id: str, keyword: str = "장기렌트", max_reply: int = 5):
    """
    내 최근 포스트의 미답변 댓글에 AI 답글을 달아줍니다.
    C-Rank: 댓글 소통은 '콘텐츠 깊이(Context)'로 평가됩니다.
    """
    print(f"   💬 [Interaction] 댓글 답글 시작 (최대 {max_reply}개)...")
    try:
        # 내 블로그 댓글 관리 페이지 접속
        url = f"https://blog.naver.com/CommentManage.naver?blogId={blog_id}"
        browser.safe_navigate(driver, url)
        time.sleep(random.uniform(2, 3))

        # iframe 진입
        try:
            WebDriverWait(driver, 8).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
        except Exception:
            pass

        replied = 0
        # 미답변 댓글 찾기
        comment_rows = driver.find_elements(By.CSS_SELECTOR,
            ".comment_list_item, li.comment_item, .cmt_list li")

        for row in comment_rows[:max_reply * 2]:
            if replied >= max_reply:
                break
            try:
                # 이미 답변한 댓글 건너뜀
                if "답변완료" in row.text or "Re:" in row.text:
                    continue

                # 댓글 텍스트 추출
                try:
                    cmt_text_el = row.find_element(By.CSS_SELECTOR,
                        ".comment_text, .txt, .cmt_txt, p")
                    cmt_text = cmt_text_el.text.strip()
                except Exception:
                    continue

                if not cmt_text or len(cmt_text) < 5:
                    continue

                # 답글 버튼 클릭
                try:
                    reply_btn = row.find_element(By.CSS_SELECTOR,
                        "button.reply_btn, a.btn_reply, button[class*='reply']")
                    driver.execute_script("arguments[0].click();", reply_btn)
                    time.sleep(random.uniform(1, 2))
                except Exception:
                    continue

                # AI 답글 생성
                reply_text = _gen_reply(cmt_text, keyword)
                print(f"   📝 [Interaction] 답글: {reply_text[:40]}...")

                # 답글 입력
                try:
                    textarea = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                            "textarea.reply_input, textarea[placeholder*='답글'], textarea.cmt_input"))
                    )
                    textarea.click()
                    time.sleep(0.3)
                    human.human_typing(driver, textarea, reply_text)
                    time.sleep(0.5)
                    textarea.send_keys(Keys.CONTROL, Keys.RETURN)
                    time.sleep(random.uniform(1.5, 2.5))
                    replied += 1
                    print(f"   ✅ [Interaction] 답글 완료 [{replied}/{max_reply}]")
                except Exception as e:
                    print(f"   ⚠️ [Interaction] 답글 입력 실패: {e}")

            except Exception as e:
                print(f"   ⚠️ [Interaction] 행 처리 실패: {e}")
                continue

        print(f"   ✅ [Interaction] 총 {replied}개 답글 완료")
        driver.switch_to.default_content()

    except Exception as e:
        print(f"   ⚠️ [Interaction] 댓글 답글 오류: {e}")
        try: driver.switch_to.default_content()
        except: pass


def like_neighbor_posts(driver, blog_id: str, count: int = 5):
    """
    이웃의 최근 포스트에 공감을 눌러 '인기도 점수'를 획득합니다.
    C-Rank: 이웃 네트워크 활성도 → 신뢰도 지표로 반영
    """
    print(f"   👍 [Interaction] 이웃 공감 시작 ({count}개)...")
    try:
        url = f"https://blog.naver.com/NeighborPostList.naver?blogId={blog_id}"
        browser.safe_navigate(driver, url)
        time.sleep(random.uniform(2, 3))

        try:
            WebDriverWait(driver, 8).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
        except Exception:
            pass

        liked = 0
        post_links = driver.find_elements(By.CSS_SELECTOR,
            "a.item_title, .neighbor_post a.title, .blog_list a.title")

        for link in post_links[:count * 2]:
            if liked >= count:
                break
            try:
                href = link.get_attribute("href") or ""
                if "blog.naver.com" not in href:
                    continue
                title = link.text.strip()

                # 포스트 열기
                driver.execute_script("window.open(arguments[0]);", href)
                time.sleep(1)
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                time.sleep(random.uniform(2, 3))

                # 공감 버튼 클릭
                try:
                    like_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                            ".u_likeit_list_btn, button.like_btn, .sympathyBtn, button[class*='like']"))
                    )
                    driver.execute_script("arguments[0].click();", like_btn)
                    time.sleep(random.uniform(0.5, 1.5))
                    liked += 1
                    print(f"   ✅ [Interaction] 공감 [{liked}/{count}]: {title[:30]}")
                except Exception:
                    pass

                # 탭 닫기
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
                continue

        print(f"   ✅ [Interaction] 이웃 공감 완료: {liked}개")
        driver.switch_to.default_content()

    except Exception as e:
        print(f"   ⚠️ [Interaction] 이웃 공감 오류: {e}")
        try: driver.switch_to.default_content()
        except: pass


def run_interaction_session(driver, blog_id: str, keyword: str = "장기렌트"):
    """
    전체 소통 세션 실행:
    1. 댓글 답글 (최대 5개)
    2. 이웃 공감 (5개)
    """
    print(f"   🤝 [Interaction] 소통 세션 시작 (블로그: {blog_id})")
    reply_to_comments(driver, blog_id, keyword, max_reply=5)
    time.sleep(random.uniform(3, 6))
    like_neighbor_posts(driver, blog_id, count=5)
    print(f"   🎉 [Interaction] 소통 세션 완료")
