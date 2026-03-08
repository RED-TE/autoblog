# -*- coding: utf-8 -*-
# naver_nurture.py — 네이버 계정 육성 전담 모듈
# [리팩토링] naver_core.py에서 계정 육성/지식인 코드를 분리

import time
import random
from selenium.webdriver.common.by import By

import browser_core as browser
import human_action as human
import ui_selectors as selectors


def account_nurturing(driver, action_type="news", duration_min=5):
    """일반인 코스프레: 뉴스 읽기, 쇼핑 검색 등"""
    print(f"   🌱 [Nurture] ({action_type}, {duration_min}m)")
    end_time = time.time() + (duration_min * 60)
    
    while time.time() < end_time:
        try:
            if action_type == "news":
                browser.safe_navigate(driver, "https://news.naver.com")
                time.sleep(random.uniform(2, 4))
                sels = selectors.SELECTORS["NEWS"]
                articles = driver.find_elements(By.CSS_SELECTOR, sels["MAIN_ARTICLE_LINK"])
                if articles:
                    target = random.choice(articles[:5])
                    human.human_move_and_click(driver, target)
                    time.sleep(3)
                    human.human_scroll(driver, 100, 300)
                    time.sleep(random.uniform(5, 10))
            print(f"   ⏳ {int(end_time - time.time())}s")
        except: time.sleep(5)


def kin_solver(driver, keyword, blog_link):
    """지식 기부형 전문가: 답변이 없는 질문에 답변 + 블로그 홍보"""
    print(f"   🎓 [Kin] '{keyword}'")
    try:
        url = f"https://kin.naver.com/search/list.naver?query={keyword}"
        browser.safe_navigate(driver, url)
        time.sleep(2)
        
        sels = selectors.SELECTORS["KIN"]
        questions = driver.find_elements(By.CSS_SELECTOR, sels["QUESTION_LIST_ITEM"])
        target_url = None
        for q in questions:
            if "답변 0" in q.text:
                try:
                    target_url = q.find_element(By.TAG_NAME, "a").get_attribute("href")
                    break
                except: continue
        
        if not target_url:
            print("   ℹ️ No questions")
            return

        print(f"   🎯 Target: {target_url}")
        browser.safe_navigate(driver, target_url)
        time.sleep(3)
        
        try:
            ans_btn = driver.find_element(By.CSS_SELECTOR, sels["ANSWER_BTN"])
            human.human_move_and_click(driver, ans_btn)
        except: return
             
        time.sleep(2)
        answer_text = f"안녕하세요. {keyword} 정보입니다.\n🔗 {blog_link}"
        
        try: driver.switch_to.frame("smart_editor2_content")
        except: pass
        
        human.human_typing(driver, driver.switch_to.active_element, answer_text)
        time.sleep(2)
        print("   ✅ 답변 완료")
        
    except Exception as e:
        print(f"   ⚠️ Kin 실패: {e}")
