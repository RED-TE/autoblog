
# test_coupang.py
# 쿠팡 우회 접속 및 검색 테스트 (네이버 검색 -> 쿠팡 접속 -> 두쫀쿠)
# [리팩토링] modules.py 의존성 제거 → browser_core / human_action 사용

import time
import browser_core
import human_action
import ui_selectors as selectors
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_coupang():
    print("🚀 [Coupang Test] 쿠팡 접속 테스트 시작 (Organic Flow)...")
    
    # 1. 스텔스 브라우저 실행
    driver = browser_core.get_driver("coupang_profile")
    if not driver:
        print("❌ 브라우저 실행 실패")
        return

    try:
        # 2. 네이버 접속
        print("   🌐 네이버 접속 중...")
        browser_core.safe_navigate(driver, "https://www.naver.com")
        time.sleep(2)
        
        # 3. 네이버 검색창 찾기 & '쿠팡' 검색
        print("   🔍 네이버에서 '쿠팡' 검색...")
        sels_main = selectors.SELECTORS["MAIN"]
        
        try:
            naver_search = driver.find_element(By.ID, "query")
            human_action.human_move_and_click(driver, naver_search)
            human_action.human_typing(driver, naver_search, "쿠팡")
            time.sleep(0.5)
            naver_search.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"   ⚠️ 네이버 검색 실패: {e}")
            return
            
        time.sleep(3)
        
        # 4. 검색 결과에서 '쿠팡' 링크 찾기
        print("   👀 쿠팡 링크 찾는 중...")
        found_link = False
        try:
            link_candidates = [
                "a[href*='coupang.com']", 
                ".link_name", 
                ".total_tit"
            ]
            
            for selector in link_candidates:
                links = driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute("href")
                    if href and "coupang.com" in href:
                        print(f"   🔗 발견: {href}")
                        human_action.human_move_and_click(driver, link)
                        found_link = True
                        break
                if found_link: break
            
            if not found_link:
                print("   ⚠️ 쿠팡 링크를 못 찾음. 직접 이동.")
                browser_core.safe_navigate(driver, "https://www.coupang.com")
                
        except Exception as e:
             print(f"   ⚠️ 링크 클릭 실패: {e}")
             browser_core.safe_navigate(driver, "https://www.coupang.com")

        # 5. 탭 전환 (새 창으로 열릴 경우)
        time.sleep(5)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print("   🔀 새 탭으로 전환")
            
        print(f"   ✅ 현재 URL: {driver.current_url}")
        
        # 6. 쿠팡 검색창 찾기
        print("   🔍 쿠팡 검색창 찾는 중...")
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            human_action.human_move_and_click(driver, search_input)
            
            # 7. 검색어 입력 (두쫀쿠)
            keyword = "두쫀쿠"
            print(f"   ⌨️ 쿠팡 검색어 입력: {keyword}")
            human_action.human_typing(driver, search_input, keyword)
            time.sleep(1)
            
            # 8. 엔터
            search_input.send_keys(Keys.ENTER)
            
            print("   ✅ 쿠팡 검색 완료! 결과 페이지 대기 중...")
            time.sleep(10) 
            
        except Exception as e:
            print(f"   ⚠️ 쿠팡 검색창 찾기/입력 실패: {e}")
            
    except Exception as e:
        print(f"   ⚠️ 테스트 중 에러 발생: {e}")
        
    print("🎉 테스트 종료. (브라우저는 닫지 않고 유지합니다)")
    input("종료하려면 엔터를 누르세요...")
    driver.quit()

if __name__ == "__main__":
    test_coupang()
