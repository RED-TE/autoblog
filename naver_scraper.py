# -*- coding: utf-8 -*-
# naver_scraper.py
# Naver Blog Scraper for Benchmarking

import time
import random
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import browser_core as browser
import human_action


# 유효한 포스트 URL 판별 (블로그 홈·섹션 제외)
import re as _re
_POST_PATTERN = _re.compile(
    r"^https?://blog\.naver\.com/[A-Za-z0-9_\-]+/\d{6,}$"
)

def _is_valid_post_url(url: str) -> bool:
    """blog.naver.com/{user}/{postId} 형태만 허용"""
    if not url:
        return False
    if "section.blog.naver.com" in url:
        return False
    if "MyBlog.naver" in url:
        return False
    return bool(_POST_PATTERN.match(url.split("?")[0].rstrip("/")))


def search_top_blogs(driver, keyword, count=3):
    """
    네이버 블로그 탭에서 상위 N개 포스트 URL 반환.
    전략: 블로그 탭 → 제목 클릭 셀렉터로 실제 포스트 링크 추출 → 숫자 ID 검증
    """
    print(f"   🔍 [Scraper] '{keyword}' 블로그 검색 시작 (목표: {count}개)", flush=True)

    direct_url = f"https://search.naver.com/search.naver?where=blog&query={keyword}"
    browser.safe_navigate(driver, direct_url)
    time.sleep(random.uniform(2.5, 3.5))
    print(f"   🌐 URL: {direct_url}", flush=True)

    blog_links = []
    page = 1

    while len(blog_links) < count and page <= 3:
        if page > 1:
            next_url = (f"https://search.naver.com/search.naver"
                        f"?where=blog&query={keyword}&start={1+(page-1)*10}")
            browser.safe_navigate(driver, next_url)
            time.sleep(random.uniform(1.5, 2.5))
            print(f"   📄 [Scraper] 페이지 {page} 로드", flush=True)

        new_links = _extract_post_links(driver, count - len(blog_links))
        if not new_links:
            print(f"   ⚠️ 페이지 {page}: 포스트 링크 없음 — HTML 저장", flush=True)
            try:
                with open(f"debug_scraper_p{page}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except: pass
            break

        for link in new_links:
            if link not in blog_links:
                blog_links.append(link)
                print(f"   ✅ 포스트 [{len(blog_links)}]: {link}", flush=True)
            if len(blog_links) >= count:
                break

        page += 1

    print(f"   ✅ [Scraper] 최종 {len(blog_links)}개 확보", flush=True)
    return blog_links


def _extract_post_links(driver, needed: int) -> list:
    """
    현재 검색 결과 페이지에서 실제 포스트 URL만 추출.
    우선순위:
      A) 검색 결과 제목 링크 셀렉터 (가장 정확)
      B) 결과 컨테이너별 첫 번째 유효 href
      C) 전체 페이지에서 정규식 필터링
    """
    links = []

    # ── A: 제목 링크 셀렉터 ────────────────────────────────────────────
    TITLE_SELS = [
        # 블로그 탭 2024+ 구조
        "a.title_link",
        "a.api_txt_lines",
        ".total_area a.title",
        # 이전 구조
        "a.total_tit",
        "a.link_tit",
        # SDS 컴포넌트 구조
        ".sds-comps-text-type-headline1 a",
        "a[href*='blog.naver.com'][class*='title']",
    ]
    for sel in TITLE_SELS:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elems:
                href = e.get_attribute("href") or ""
                if _is_valid_post_url(href) and href not in links:
                    links.append(href)
            if links:
                print(f"   🎯 셀렉터 '{sel}'으로 {len(links)}개 추출", flush=True)
        except: pass
        if len(links) >= needed:
            return links[:needed]

    # ── B: 컨테이너별 첫 번째 유효 링크 ─────────────────────────────
    CONTAINER_SELS = [
        "li.bx",
        ".view_wrap",
        ".lst_total > li",
        ".lst_view > li",
        "div[class*='fds-ugc-block-mod']",
    ]
    for con_sel in CONTAINER_SELS:
        try:
            containers = driver.find_elements(By.CSS_SELECTOR, con_sel)
            if not containers:
                continue
            found_in_con = 0
            for con in containers:
                if len(links) >= needed:
                    break
                try:
                    anchors = con.find_elements(By.TAG_NAME, "a")
                    for a in anchors:
                        href = a.get_attribute("href") or ""
                        if _is_valid_post_url(href) and href not in links:
                            links.append(href)
                            found_in_con += 1
                            break  # 컨테이너당 1개만
                except: pass
            if found_in_con:
                print(f"   🎯 컨테이너 '{con_sel}'에서 {found_in_con}개 추출", flush=True)
        except: pass
        if len(links) >= needed:
            return links[:needed]

    # ── C: 전체 페이지 정규식 필터 ───────────────────────────────────
    if len(links) < needed:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if _is_valid_post_url(href) and href not in links:
                    links.append(href)
                if len(links) >= needed:
                    break
            print(f"   🎯 BeautifulSoup 폴백: {len(links)}개", flush=True)
        except Exception as e:
            print(f"   ⚠️ BS4 오류: {e}", flush=True)

    return links[:needed]




def extract_blog_content(driver, url):
    """
    블로그 포스트 내용을 스크레이핑합니다.
    iframe 내부 접근 포함.
    """
    print(f"   📖 [Scraper] 콘텐츠 추출: {url}", flush=True)
    
    browser.safe_navigate(driver, url)
    time.sleep(random.uniform(1.0, 2.0))  # 초기 로딩 대기 시간 단축

    result = {"url": url, "text": "", "tags": [], "title": ""}

    try:
        # iframe 시도 (네이버 블로그는 mainFrame 안에 실제 콘텐츠가 있음)
        try:
            frame = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(frame)
            time.sleep(1)
        except:
            pass  # iframe 없으면 현재 페이지 그대로

        # ── 사람처럼 본문 스크롤하며 이미지(게으른 로딩) 및 텍스트 렌더링 ──
        print("   🖱️ [Scraper] 본문 스크롤 탐색 중... (휴먼 액션)", flush=True)
        try:
            human_action.human_scroll(driver, min_scroll=400, max_scroll=900)
        except Exception as e:
            print(f"   ⚠️ 스크롤 중 오류: {e}", flush=True)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 제목
        title_tag = (
            soup.find("div", class_=re.compile(r"se-title-text|title_area|post-title"))
            or soup.find("h3", class_=re.compile(r"title|제목"))
            or soup.find("title")
        )
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

        # 본문
        body_tag = (
            soup.find("div", class_=re.compile(r"se-main-container|post-content|se_doc_viewer"))
            or soup.find("div", {"id": re.compile(r"viewTypeSelector|postViewArea")})
            or soup.find("div", class_=re.compile(r"post_ct|blog-post"))
        )
        if body_tag:
            text = body_tag.get_text(separator="\n", strip=True)
            result["text"] = text[:5000]  # 최대 5000자
        else:
            # 폴백: body 전체
            result["text"] = soup.body.get_text(separator="\n", strip=True)[:3000] if soup.body else ""

        # 태그
        tag_elems = soup.find_all("span", class_=re.compile(r"tag|pcol2"))
        result["tags"] = [t.get_text(strip=True) for t in tag_elems[:10] if t.get_text(strip=True)]

        print(f"   📄 [Scraper] 텍스트 {len(result['text'])}자, 태그 {len(result['tags'])}개", flush=True)

    except Exception as e:
        print(f"   ⚠️ [Scraper] 콘텐츠 추출 오류: {e}", flush=True)
    finally:
        # 메인 프레임으로 복귀
        try:
            driver.switch_to.default_content()
        except:
            pass

    return result
