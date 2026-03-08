# human_wanderer.py
# 네이버 봇 탐지 회피를 위한 '진짜 사람 같은 무작위 행동' 모듈 V2
# 압도적인 범위의 검색어와 쇼핑, 뉴스, 블로그, 이메일, 외부 사이트(유튜브 등) 방문 기능 총망라

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 100+ 일상 검색어 및 자동차 관련 키워드 풀
MASSIVE_KEYWORDS = [
    # 일상/이슈
    "오늘 날씨", "내일 날씨", "미세먼지 농도", "환율", "삼성전자 주가", "비트코인 시세", 
    "코스피 지수", "나스닥", "로또 당첨번호", "운세", "MBTI 궁합", "띠별 운세",
    "최신 영화 추천", "넷플릭스 신작", "디즈니플러스 추천", "티빙 오리지널", "유튜브 베스트",
    "프로야구 하이라이트", "프리미어리그 순위", "손흥민 골", "챔피언스리그", "올림픽",
    "맛집 베스트", "오마카세 추천", "가성비 오마카세", "강남역 맛집", "홍대 카페", "성수동 팝업스토어",
    "다이어트 식단", "저탄고지 밥상", "단백질 보충제 추천", "홈트레이닝 영상", "런닝화 추천",
    "부동산 전망", "청약 일정", "연말정산 꿀팁", "신용카드 추천", "마일리지 카드",
    "국내 여행지 추천", "제주도 항공권", "오사카 항공권", "도쿄 디즈니랜드", "호캉스 추천", "풀빌라 펜션",
    "캠핑장 예약", "차박 성지", "글램핑 추천", "아이폰 16 출시일", "갤럭시 S24 울트라", "아이패드 프로", 
    "맥북 에어 M3", "애플워치 스트랩", "다이슨 에어랩", "로봇청소기 추천", "식기세척기 이모님",
    "세일 정보", "올리브영 세일", "무신사 블랙프라이데이", "쿠팡 로켓배송", "마켓컬리 추천템",
    "토익 접수", "오픽 후기", "운전면허 필기시험", "한국사 능력검정시험", "면접 복장",
    "MBTI 테스트", "심리테스트", "퍼스널컬러 진단", "크로스핏 후기", "필라테스 가격",
    "편의점 신상", "먹방 유튜버", "asmr 수면", "플레이리스트", "출근길 팝송", "드라이브 음악",
    
    # 자동차/장기렌트 관련 (관심사 매칭)
    "쏘렌토 하이브리드 대기기간", "싼타페 풀체인지", "그랜저 GN7", "카니발 하이리무진", 
    "GV80 페이스리프트", "G80 전기차", "제네시스 GV70", "아반떼 N", "투싼 하이브리드",
    "벤츠 E클래스", "BMW 5시리즈", "아우디 A6", "포르쉐 카이엔", "테슬라 모델Y", "아이오닉 5",
    "기아 EV9", "토레스 EVX", "렉스턴 스포츠", "볼보 XC90", "폭스바겐 티구안", "포드 브롱코",
    "람보르기니 우루스", "마이바흐 S클래스", "레인지로버 보그", "디펜더 110",
    "장기렌트 장단점", "오토리스 비용처리", "신차 장기렌터카", "무보증 장기렌트", "법인 리스 혜택",
    "자동차 보험료 계산", "중고차 시세", "엔카 직영", "케이카 홈서비스", "헤이딜러 견적",
    "세차용품 추천", "블랙박스 2채널", "자동차 썬팅", "유리막 코팅", "차량용 방향제"
]

def random_sleep(min_s=1.5, max_s=4.0):
    """사람처럼 불규칙한 시간 대기"""
    time.sleep(random.uniform(min_s, max_s))

def scroll_randomly(driver, times=None):
    """마우스 휠을 굴리듯 페이지 위아래 무작위 탐색"""
    if times is None:
        times = random.randint(2, 6)
    for _ in range(times):
        scroll_amount = random.randint(200, 900)
        direction = random.choice([1, 1, 1, 1, -1])  # 80% 확률로 아래로 스크롤
        try:
            driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction});")
        except:
            pass
        random_sleep(0.5, 2.0)

def human_typing(element, text):
    """사람처럼 한글자씩 리듬을 타며 입력. 간혹 약간 쉬기도 함."""
    for char in text:
        element.send_keys(char)
        if random.random() < 0.1:  # 10% 확률로 잠깐 멈춤 (생각하는 척)
            time.sleep(random.uniform(0.3, 0.7))
        else:
            time.sleep(random.uniform(0.03, 0.2))

# ==========================================
# 행동 패턴 (Actions)
# ==========================================

def search_and_browse_blogs(driver):
    """네이버 메인 검색 후 블로그/뷰 탭으로 이동해 글 하나 읽기"""
    keyword = random.choice(MASSIVE_KEYWORDS)
    print(f"   🚶‍♂️ [스텔스] 검색 및 블로그 탐색: '{keyword}'")
    try:
        driver.get("https://www.naver.com")
        random_sleep(2, 4)
        
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#query"))
        )
        search_box.clear()
        human_typing(search_box, keyword)
        random_sleep(0.5, 1.5)
        search_box.send_keys(Keys.RETURN)
        
        random_sleep(3, 5)
        scroll_randomly(driver, times=2)
        
        # 'VIEW' 또는 '블로그' 탭 클릭 시도
        try:
            tabs = driver.find_elements(By.CSS_SELECTOR, ".api_flicking_wrap .tab")
            for tab in tabs:
                if "뷰" in tab.text or "VIEW" in tab.text or "블로그" in tab.text:
                    driver.execute_script("arguments[0].click();", tab)
                    break
            random_sleep(3, 5)
            scroll_randomly(driver, times=3)
        except:
            pass
            
        # 아무 글이나 클릭해서 들어가기
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a.api_txt_lines.total_tit, a.title_link")
            if links:
                target = random.choice(links[:7])
                original_tabs = len(driver.window_handles)
                
                # 중앙에 맞추어 놓고 클릭
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", target)
                
                random_sleep(2, 4)
                if len(driver.window_handles) > original_tabs:
                    driver.switch_to.window(driver.window_handles[-1])
                    random_sleep(5, 12)  # 글을 꽤 오래 읽음
                    scroll_randomly(driver, times=5)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        except:
            pass
            
    except Exception:
        pass

def read_news(driver):
    """네이버 뉴스 정독 (메인에서 클릭해서 진입)"""
    print("   🚶‍♂️ [스텔스] 네이버 뉴스 정독 중...")
    try:
        driver.get("https://www.naver.com")
        random_sleep(2, 4)
        
        # 메인 메뉴에서 '뉴스' 클릭
        try:
            news_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'nav') and span[contains(text(), '뉴스')]]")
            driver.execute_script("arguments[0].click();", news_btn)
        except:
            driver.get("https://news.naver.com") # 클릭 실패시 폴백
            
        random_sleep(3, 6)
        scroll_randomly(driver, times=2)
        
        articles = driver.find_elements(By.CSS_SELECTOR, ".cjs_t, .sa_text_title")
        if articles:
            article = random.choice(articles[:10])
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", article)
            random_sleep(1, 2)
            driver.execute_script("arguments[0].click();", article)
            
            # 기사 본문 체류 시간
            random_sleep(8, 15)
            scroll_randomly(driver, times=6)
            random_sleep(4, 7)
    except Exception:
        pass

def browse_shopping(driver):
    """네이버 쇼핑 둘러보기 (메인에서 클릭해서 진입)"""
    print("   🚶‍♂️ [스텔스] 네이버 쇼핑 아이쇼핑 중...")
    try:
        driver.get("https://www.naver.com")
        random_sleep(2, 4)
        
        # 메인 메뉴에서 '쇼핑' 클릭
        try:
            shop_btn = driver.find_element(By.XPATH, "//a[contains(@class, 'nav') and span[contains(text(), '쇼핑')]]")
            original_tabs = len(driver.window_handles)
            driver.execute_script("arguments[0].click();", shop_btn)
            random_sleep(2, 4)
            # 쇼핑이 새 탭으로 열렸다면 탭 전환
            if len(driver.window_handles) > original_tabs:
                driver.switch_to.window(driver.window_handles[-1])
        except:
            driver.get("https://shopping.naver.com/home") # 폴백
            
        random_sleep(3, 6)
        scroll_randomly(driver, times=4)
        
        items = driver.find_elements(By.CSS_SELECTOR, "a[data-nclick^='N=a:rec'], a._itemSection_item_link_")
        if items:
            item = random.choice(items)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", item)
            random_sleep(1, 2)
            
            original_tabs = len(driver.window_handles)
            driver.execute_script("arguments[0].click();", item)
            random_sleep(2, 4)
            
            if len(driver.window_handles) > original_tabs:
                driver.switch_to.window(driver.window_handles[-1])
                random_sleep(6, 15)  # 상품 상세페이지 체류
                scroll_randomly(driver, times=5)
                # 옵션 클릭 흉내 내기 (가상)
                random_sleep(2, 4)
                driver.close()
                driver.switch_to.window(driver.window_handles[-1]) # 이전 탭(쇼핑 메인)으로 복귀
            else:
                random_sleep(5, 10)
                scroll_randomly(driver, times=3)
    except Exception:
        pass

def check_naver_mail(driver):
    """네이버 메일함 방문 (버튼 클릭 기반)"""
    print("   🚶‍♂️ [스텔스] 네이버 메일함 확인 중...")
    try:
        driver.get("https://www.naver.com")
        random_sleep(2, 4)
        
        # 메인 좌측 또는 상단의 메일 버튼 클릭
        try:
            mail_btn = driver.find_element(By.CSS_SELECTOR, "a.my_pi_info, a[data-clk='svc.mail']")
            driver.execute_script("arguments[0].click();", mail_btn)
        except:
            driver.get("https://mail.naver.com")
            
        random_sleep(5, 10)
        # 메일 리스트 훑기
        scroll_randomly(driver, times=3)
        random_sleep(3, 6)
    except Exception:
        pass


def random_rest(driver):
    """가만히 멍때리기 (커피 타오는 시간, 화장실 가는 시간 등)"""
    rest_time = random.randint(15, 60)
    print(f"   ☕ [스텔스] 인간적인 휴식 중... (가만히 {rest_time}초 대기)")
    time.sleep(rest_time)

# ==========================================
# 실행 제어기 (Execution Controller)
# ==========================================

def perform_wandering(driver, is_first_account=False, short_mode=False):
    """
    주어진 상황에 맞게 랜덤 행동 시퀀스를 실행합니다.
    - 첫 계정(실행 직후): 3 ~ 10 번 행동
    - 다음 계정 대기 중: 7 ~ 20 번 행동
    - 포스팅 사이 대기 중 (short_mode): 2 ~ 4 번 행동
    """
    if short_mode:
        min_actions, max_actions = 2, 4
        phase = "포스팅 사이 휴식"
    else:
        min_actions = 3 if is_first_account else 7
        max_actions = 10 if is_first_account else 20
        phase = "최초 웜업" if is_first_account else "계정 교체 대기 기간"
        
    num_actions = random.randint(min_actions, max_actions)
    
    print(f"\n   🕵️ [스텔스] 진짜 사람 같은 사전 행동({phase}) 시작! 총 {num_actions}개의 랜덤 행동을 수행합니다.")
    
    actions_pool = [
        search_and_browse_blogs, search_and_browse_blogs,  # 블로그 구경 확률 높임
        read_news, read_news,                              # 뉴스 확률 높임
        browse_shopping, browse_shopping,
        check_naver_mail,
        random_rest
    ]
    
    for i in range(num_actions):
        print(f"   ▶️ [행동 {i+1}/{num_actions}] ", end="")
        action = random.choice(actions_pool)
        action(driver)
        
        # 각 행동 사이에 짧은 휴식
        random_sleep(3, 8)
        
    print(f"   ✅ [스텔스] {num_actions}개의 무작위 행동 완료. 봇탐지 회피율이 극대화되었습니다.\n")

# 단독 테스트용
if __name__ == "__main__":
    import browser_core
    d = browser_core.get_driver("test_wander")
    if d:
        perform_wandering(d, is_first_account=True)
        d.quit()
