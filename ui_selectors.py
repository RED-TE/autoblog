
# ui_selectors.py
# 전용 UI 요소 정의 (User Provided & Verified)

SELECTORS = {
    # 1. 로그인 (Login)
    "LOGIN": {
        "ID_INPUT": "#id",
        "PW_INPUT": "#pw",
        "SUBMIT_BTN": r"#log\.login"  # ID contains dot, needs escape or use ID selector
    },

    # 2. 메인 화면 & 블로그 홈
    "MAIN": {
        "LOGIN_BTN": ".MyView-module__link_login___HpHMW", 
        "WRITE_BTN_BLOG_HOME": "a[href*='GoBlogWrite.naver']", 
        "WRITE_BTN_PC": "a.btn_write",
    },
    
    # 3. 에디터 진입
    "EDITOR_FRAME": {
        "MAIN_FRAME": "mainFrame",
    },

    # 4. 글쓰기 (SmartEditor ONE)
    "EDITOR": {
        # 제목: 
        # User HTML: <p ...><span id="..."></span><span class="se-placeholder ...">제목</span></p>
        "TITLE_CONTAINER": "p.se-text-paragraph-align-left",
        "TITLE_PLACEHOLDER": "//span[contains(@class, 'se-placeholder') and contains(text(), '제목')]", 
        
        # 본문: 
        # User HTML: <p ...><span ...></span><span class="se-placeholder ...">글감과 함께...</span></p>
        "CONTENT_BODY": ".se-main-container",
        "CONTENT_PLACEHOLDER": "//span[contains(@class, 'se-placeholder') and contains(text(), '글감과 함께')]",
        
        # 툴바 버튼
        "QUOTE_BTN": "button[data-name='quotation']",
        "IMAGE_LINK_BTN": "button[title='링크 입력']",
        "LINK_INPUT": "input.se-custom-layer-link-input",
        "LINK_CONFIRM": "button.se-custom-layer-link-apply-button",
        
        # 인용구 옵션 (User HTML keys)
        "QUOTE_OPT_DEFAULT": "button[data-value='default']",
        "QUOTE_OPT_LINE": "button[data-value='quotation_line']",
        "QUOTE_OPT_CORNER": "button[data-value='quotation_corner']",
        
        # 목록 및 표 버튼
        "LIST_BULLET_BTN": "button[data-value='bullet']",
        "LIST_DECIMAL_BTN": "button[data-value='decimal']",
        "LIST_RESET_BTN": "button[data-value='reset']",
        "TABLE_BTN": "button[data-name='table']",
        
        # 발행 버튼
        "PUBLISH_BTN_1": "button.btn_publish, button.btn_upload", 
        "PUBLISH_BTN_FINAL": "button.confirm_submit, button.btn_confirm",
        "TAG_INPUT": "input.tag_input"
    },
    
    # 5. 검색 및 스크래핑
    "SEARCH": {
        "SEARCH_INPUT": "input#query",
        "BLOG_TAB": "a.tab[href*='blog']", 
        "VIEW_TAB": "a.tab[href*='view']"
    }
}
