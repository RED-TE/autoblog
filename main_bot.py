# main_bot.py
# 네이버 블로그 자동화 메인 - V2 Modular Architecture
# Workflow: Environment -> Warm-up -> Content -> Posting -> Finalize

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import time
import random
import json
import os
import functools

# ── stdout 즉시 출력 강제 (subprocess 버퍼 문제 방지) ──────────
import builtins
_orig_print = builtins.print
builtins.print = functools.partial(_orig_print, flush=True)

# V2 Modules
import browser_core as browser
import naver_core as naver
import image_utils
import gemini_core
import naver_scraper
import ip_manager
import telegram_bot
import rank_tracker
import dwell_bot        # 체류 시간 시뮬레이션
import interaction_bot  # 댓글/이웃 소통
from image_processor import ImageEvasionProcessor
import human_wanderer   # [NEW] 사람처럼 랜덤 서핑 

# [설정] 실행 모드 (TEST / BENCHMARK / SEMIAUTO / NURTURE / KIN)
RUN_MODE = "BENCHMARK" 


# Global account loading removed. Will use config.


# ═══════════════════════════════════════════════════════════════
# 유사성 회피 랜덤 레이아웃 생성기
# ═══════════════════════════════════════════════════════════════
def build_random_layout(body_text: str, image_paths: list, persona: str, keyword: str, cta: str = "", image_link: str = "", link_image: str = "", link_pos: str = "하단") -> list:
    Q_STYLES = ["quotation_line", "quotation_corner"]
    lines = [p.strip() for p in body_text.split('\n') if p.strip()]

    parsed = []
    in_table = False
    table_rows = []

    for line in lines:
        if line == "[표]":
            in_table = True; table_rows = []; continue
        elif line == "[/표]":
            in_table = False
            if table_rows:
                parsed.append({"type": "table", "content": list(table_rows)})
            continue
        if in_table:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells and set(line.replace('|','').replace('-','').replace(' ','')) != set():
                table_rows.append(cells)
            continue

        is_quote, is_list, list_style = False, False, ""
        if line.startswith('- ') or line.startswith('* '):
            is_list, list_style = True, "bullet"; line = line[2:].strip()
        elif len(line) > 2 and line[0].isdigit() and line[1] == '.':
            is_list, list_style = True, "decimal"; line = line[line.find('.')+1:].strip()
        if line.startswith('>') or line.startswith('"') or line.startswith('“') or line.startswith('[인용구]'):
            is_quote = True
            line = line.lstrip('>').lstrip('"').lstrip('“').rstrip('"').rstrip('”').replace('[인용구]', '').strip()

        if is_quote and len(line) > 3:
            parsed.append({"type": "quote", "style": random.choice(Q_STYLES), "content": line})
        elif is_list:
            parsed.append({"type": "list", "style": list_style, "content": line})
        else:
            parsed.append({"type": "text", "content": line})

    # 단락 순서 완전 셔플
    text_items  = [it for it in parsed if it["type"] in ("text", "list", "table")]
    quote_items = [it for it in parsed if it["type"] == "quote"]

    random.shuffle(text_items)
    random.shuffle(quote_items)

    chunk_size = random.randint(2, 3)
    chunks = [text_items[i:i+chunk_size] for i in range(0, len(text_items), chunk_size)]

    imgs = list(image_paths) if image_paths else []
    random.shuffle(imgs)

    link_img_at_chunk = -1
    if link_image and chunks:
        if link_pos == "상단":   link_img_at_chunk = 0
        elif link_pos == "중간": link_img_at_chunk = max(0, len(chunks) // 2)
        else:                    link_img_at_chunk = max(0, len(chunks) - 1)

    post_items = []
    q_idx, img_idx = 0, 0

    for ci, chunk in enumerate(chunks):
        if quote_items and q_idx < len(quote_items) and random.random() < 0.33:
            post_items.append(quote_items[q_idx]); q_idx += 1

        post_items.extend(chunk)

        if ci == link_img_at_chunk and link_image:
            post_items.append({"type": "image", "content": link_image, "link": image_link})

        if imgs and img_idx < len(imgs) and random.random() < 0.5:
            post_items.append({"type": "image", "content": imgs[img_idx]}); img_idx += 1

        if quote_items and q_idx < len(quote_items) and random.random() < 0.40:
            post_items.append(quote_items[q_idx]); q_idx += 1

    while img_idx < len(imgs):
        pos = random.randint(0, len(post_items))
        post_items.insert(pos, {"type": "image", "content": imgs[img_idx]}); img_idx += 1

    while q_idx < len(quote_items):
        post_items.append(quote_items[q_idx]); q_idx += 1

    if cta:
        post_items.append({"type": "quote", "style": random.choice(Q_STYLES), "content": cta})

    layout = ' → '.join(it['type'] for it in post_items)
    print(f"   🎲 {len(post_items)}블록 랜덤 배치 | {layout[:80]}{'...' if len(layout)>80 else ''}")
    return post_items


# ═══════════════════════════════════════════════════════════════
# 내부 헬퍼 함수들 (process_account 오케스트레이터에서 호출)
# ═══════════════════════════════════════════════════════════════

def _load_ui_config() -> dict:
    """_ui_config.json 로드 및 파싱. 실패 시 빈 dict 반환."""
    ui_cfg = {}
    ui_cfg_path = os.path.join(os.getcwd(), "_ui_config.json")
    if os.path.exists(ui_cfg_path):
        try:
            with open(ui_cfg_path, "r", encoding="utf-8") as f:
                ui_cfg = json.load(f)
            print(f"   📋 UI 설정 로드 완료")
        except Exception as e:
            print(f"   ⚠️ UI 설정 로드 실패: {e}")
    return ui_cfg


def _collect_image_paths(images_dir: str) -> list:
    """이미지 디렉토리에서 유효한 이미지 경로 목록 반환."""
    if not images_dir or not os.path.isdir(images_dir):
        return []
    exts = (".jpg", ".jpeg", ".png", ".webp")
    paths = [
        os.path.join(images_dir, f)
        for f in sorted(os.listdir(images_dir))
        if f.lower().endswith(exts)
    ]
    print(f"   📷 이미지 {len(paths)}장 로드")
    return paths


def _collect_link_image(link_image_dir: str) -> str:
    """링크 전용 이미지 디렉토리에서 첫 번째 이미지 경로 반환."""
    if not link_image_dir or not os.path.exists(link_image_dir):
        return ""
    link_files = [
        os.path.join(link_image_dir, f)
        for f in os.listdir(link_image_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ]
    return link_files[0] if link_files else ""


def _run_benchmark(driver, keyword: str, blog_count: int, biz_name: str) -> str:
    """상위 블로그 스크레이핑 후 Gemini로 팩트 추출 → benchmark_facts 문자열 반환."""
    print(f"   🔍 네이버 '{keyword}' 블로그 검색 시작...")
    links = []
    try:
        links = naver_scraper.search_top_blogs(driver, keyword, count=blog_count)
        print(f"   ✅ 링크 {len(links)}개 확보: {links}")
    except Exception as e:
        print(f"   ⚠️ 스크레이퍼 실패 → AI 단독 모드: {e}")

    benchmark_facts = ""
    if links:
        print(f"\n   📚 [벤치마킹] {len(links)}개 블로그 전체 분석 시작...")
        all_extracted = []
        for i, url in enumerate(links):
            print(f"   🔬 [{i+1}/{len(links)}] 분석 중: {url}")
            try:
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
                driver.switch_to.default_content()

                scraped = naver_scraper.extract_blog_content(driver, url)
                raw_text = scraped.get("text", "")
                print(f"       텍스트: {len(raw_text)}자")
                if len(raw_text) > 100:
                    extracted = gemini_core.client.extract_info(raw_text)
                    if extracted:
                        all_extracted.append(f"[소스 {i+1}: {url}]\n{extracted}")
                        print(f"       팩트: {len(extracted)}자 추출")
                time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                print(f"       ⚠️ 분석 실패 (무시): {e}")

        if all_extracted:
            benchmark_facts = (
                f"[키워드: {keyword}]\n"
                + (f"[업체명: {biz_name}]\n" if biz_name else "")
                + f"[분석 블로그 수: {len(all_extracted)}개]\n\n"
                + "\n\n━━━\n\n".join(all_extracted)
            )
            print(f"\n   ✅ [벤치마킹] 통합 팩트 {len(benchmark_facts)}자 생성 완료")
        else:
            print("   ⚠️ 추출된 팩트 없음 → AI 단독 모드")
    else:
        print("   🤖 링크 없음 → AI 단독 모드")

    # AI 단독 모드 팩트
    if not benchmark_facts:
        benchmark_facts = (
            f"[키워드: {keyword}]\n"
            + (f"[업체명: {biz_name}]\n" if biz_name else "")
            + f"키워드 '{keyword}'에 대한 상세하고 정보성 높은 블로그 포스팅을 작성해주세요."
        )
    return benchmark_facts


def _wash_images(image_paths: list, post_idx: int,
                 watermark_enable: bool, watermark_text: str) -> list:
    """이미지 워터마크 세탁 처리. 처리된 경로 목록 반환."""
    if not image_paths:
        return []
    print(f"   🛁 이미지 세탁 및 워터마크 처리 중 ({len(image_paths)}장)...")
    final_paths = []
    for p_idx, p in enumerate(image_paths):
        if watermark_enable:
            ext = os.path.splitext(p)[1]  # .jpg / .png / .jpeg
            out_p = p.replace(ext, f"_washed_{post_idx}_{p_idx}{ext}")
            success = ImageEvasionProcessor.wash_and_watermark(p, out_p, watermark_text)
            final_paths.append(out_p if (success and os.path.exists(out_p)) else p)
        else:
            final_paths.append(p)
    return final_paths


def _get_schedule_time(ui_cfg: dict, keyword: str, ai_time_from_json: str) -> str:
    """예약 발행 시간 결정: UI 직접 입력 > AI-JSON 내장 > AI-Flash 순."""
    ui_schedule_time = ui_cfg.get("schedule_time", "").strip()
    if ui_schedule_time:
        print(f"   🕰️ [UI] 예약 발행 시간 (직접 지정): {ui_schedule_time}")
        return ui_schedule_time
    if ai_time_from_json and len(ai_time_from_json) >= 15:
        print(f"   🕰️ [AI-JSON] 본문 포함 발행 시간 사용: {ai_time_from_json}")
        return ai_time_from_json
    print(f"   🤖 [AI-Flash] 최적 발행 시간 질의 중...")
    result = gemini_core.client.get_best_publish_time(keyword)
    print(f"   🕰️ [AI-Flash] 추천 발행 시간: {result}")
    return result


def _post_single(driver, post_idx: int, total: int, ui_cfg: dict,
                 benchmark_facts: str, image_paths: list,
                 link_image_path: str, persona: str, keyword: str,
                 biz_name: str, required_tags: list, manual_title: str,
                 watermark_enable: bool, watermark_text: str,
                 image_link: str, link_pos: str, schedule_publish: bool,
                 pause_before_publish: bool, USER_ID: str, post_length: str,
                 align: str, advanced_format: bool, car_model: str) -> None:
    """BENCHMARK 모드 포스팅 1개 생성 + 발행."""
    print(f"\n   ═══ [{post_idx+1}/{total}] 포스팅 시작 ═══")
    # 브라우저 탭 리셋
    try:
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.default_content()
        print(f"   🔄 브라우저 탭 리셋 완료")
    except Exception as e:
        print(f"   ⚠️ 탭 리셋 실패 (무시): {e}")

    EXPOSURE_KEYS = list(gemini_core.EXPOSURE_PERSONAS.keys())
    _selected_persona = random.choice(EXPOSURE_KEYS) if persona == "random_exposure" else persona
    
    # ── [TEST 모드 분기] ──────────────────────────────────────────
    if RUN_MODE == "TEST":
        print(f"   🧪 [TEST 모드] Gemini 원격 호출 스킵 — 더미 데이터 사용")
        title = f"[테스트] {keyword} 빠른 테스트 포스팅 {post_idx+1}"
        body_text = (
            f"이 글은 테스트 모드에서 자동 생성된 더미 본문입니다.\n\n"
            f"키워드: {keyword}\n에디터 테스트를 위해 생성된 짧은 문장입니다.\n"
            f"이미지 삽입, 링크 삽입, 예약 발행 등의 기능 테스트에 사용됩니다.\n"
            f"1. 줄바꿈 테스트\n2. 특수문자 !@# 테스트\n\n완료."
        )
        cta = "테스트용 CTA 문구입니다. 클릭하세요."
        ai_publish_time = ""
        ai_seo_tags = []
    else:
        print(f"   ✍️ Gemini 생성 중... (페르소나: {_selected_persona})")
        raw_json = gemini_core.client.rewrite_content(
            benchmark_facts,
            persona=_selected_persona,
            biz_name=biz_name,
            keyword=keyword,
            car_model=car_model,
            must_phrase=ui_cfg.get("must_phrase", ""),
            must_pos=ui_cfg.get("must_pos", []),
            persona_type="exposure",
            post_length=post_length,
            advanced_format=advanced_format
        )
        
        # [NEW] 사용량 카운팅 (AI API 호출 성공 시)
        if raw_json and "user_uid" in ui_cfg and "user_token" in ui_cfg:
            try:
                from firebase_db import FirestoreClient
                db = FirestoreClient(ui_cfg["user_token"])
                is_trial = ui_cfg.get("is_trial", False)
                usage_type = "freeTrial" if is_trial else "total"
                db.increment_usage_count(ui_cfg["user_uid"], usage_type=usage_type)
                print(f"   📊 [발행 카운트] 사용량 기록 완료")
            except Exception as e:
                print(f"   ⚠️ [Usage] 발행량 계획 추가 실패: {e}")
                raise Exception("발행량 계획 추가에 실패하여 안정성 사유로 포스팅을 강제 중단합니다.")

        if not raw_json:
            print(f"   ❌ Gemini 응답 없음, 건너뜀")
            return
        print(f"   ✅ Gemini 응답 수신 ({len(raw_json)}자)")

        try:
            s  = raw_json.find('{')
            e2 = raw_json.rfind('}')
            if s == -1 or e2 == -1:
                print(f"   ❌ JSON 파싱 실패 [{post_idx+1}]")
                return
            obj = json.loads(raw_json[s:e2+1])
            title     = manual_title if manual_title else obj.get("title", f"{keyword} {post_idx+1}")
            body_text = obj.get("content", "")
            cta = obj.get("cta_text", "").strip()
            ai_publish_time = obj.get("optimal_publish_time", "").strip()
            ai_seo_tags = obj.get("seo_tags", [])
            
            candidates = obj.get("title_candidates", [])
            for ci, ct in enumerate(candidates):
                print(f"       후보{ci+1}: {ct}")
        except Exception as _eparse:
            print(f"   ❌ JSON 파싱 에러: {_eparse}")
            return
            
    # ─────────────────────────────────────────────────────────────
    
    print(f"   📝 예약/선택 제목: {title}")
    print(f"   📄 본문 내용 길이: {len(body_text)}자")

    # 이미지 워터마크 세탁
    final_image_paths = _wash_images(image_paths, post_idx, watermark_enable, watermark_text)

    # 레이아웃 빌드
    post_items = build_random_layout(body_text, final_image_paths, _selected_persona,
                                     keyword, cta, image_link, link_image_path, link_pos)
    print(f"   📦 아이템 {len(post_items)}개 구성 완료")

    # 예약 시간 결정
    schedule_time = None
    if schedule_publish:
        schedule_time = _get_schedule_time(ui_cfg, keyword, ai_publish_time)

    # 태그 병합 (UI 요구 태그 + AI 생성 25+ SEO 태그)
    final_tags = list(set(required_tags + ai_seo_tags))
    if len(final_tags) > 30: # 네이버 최대 30개 제한 처리
        final_tags = final_tags[:30]

    # 발행
    print(f"   🚀 블로그 에디터 입력 중... ({post_idx+1}/{total})")
    naver.write_post(driver, title, post_items, tags=final_tags,
                     publish=not pause_before_publish, schedule_time=schedule_time,
                     align=align, advanced_format=advanced_format)
    if pause_before_publish:
        print(f"   🛑 [{post_idx+1}/{total}] 멈춤 — 발행 버튼을 직접 눌러주세요")
    else:
        print(f"   ✅ [{post_idx+1}/{total}] 발행 완료!")
        try:
            post_url = driver.current_url
            if "blog.naver.com" in post_url:
                print(f"   ⏱️  체류 시뮬레이션 시작...")
                dwell_bot.simulate_reading(driver, post_url)
        except Exception as dw_e:
            print(f"   ⚠️ 체류 시뮬레이션 실패 (무시): {dw_e}")

    telegram_bot.notify_status(USER_ID, f"포스팅({keyword}) [{post_idx+1}/{total}]", "SUCCESS")

    if post_idx < total - 1:
        wait = random.randint(5, 10)
        print(f"   ⏳ 다음 포스팅 준비... (자연스러운 휴식 및 딴짓 수행)")
        time.sleep(wait)
        import human_wanderer
        try:
            # 다음 블로그 글을 쓰기 전, 2~4번의 검색/쇼핑 등 딴짓 수행
            human_wanderer.perform_wandering(driver, short_mode=True)
            # 딴짓이 끝난 후 다시 안정을 위해 5~10초 추가 대기
            time.sleep(random.randint(5, 10))
        except Exception as we:
            print(f"   ⚠️ 포스팅 간 딴짓 중 오류 (안전 대기로 대체): {we}")
            time.sleep(15)


# ═══════════════════════════════════════════════════════════════
# 계정 메인 실행 오케스트레이터
# ═══════════════════════════════════════════════════════════════

def process_account(acc_cfg, dashboard_data={}, is_first_account=False):
    global RUN_MODE
    USER_ID = acc_cfg.get("naver_id", "").strip()
    USER_PW = acc_cfg.get("naver_pw", "").strip()
    RUN_MODE = acc_cfg.get("MODE", "BENCHMARK").upper()
    
    print(f"\n{'='*60}\n🤖 [계정 실행] {USER_ID} | 모드: {RUN_MODE}\n{'='*60}")
    telegram_bot.send_message(f"🤖 [Bot Started] 모드: {RUN_MODE}, 계정: {USER_ID}")

    # 0. IP Rotation
    if RUN_MODE in ["BENCHMARK", "SEMIAUTO", "NURTURE"]:
        if ip_manager.check_adb_connection():
            ip_manager.toggle_airplane_mode()
        else:
            print("   ⚠️ ADB 미연결: IP 변경 건너뜀")
    
    # 1. Browser
    safe_profile = USER_ID.split('@')[0] if USER_ID else "main_profile"
    profile_name = f"profile_{safe_profile}"
    print(f"   🌐 브라우저 초기화 중... (프로필: {profile_name})")
    driver = browser.get_driver(profile_name)
    if not driver:
        print("❌ Browser Init Failed")
        telegram_bot.send_message("❌ 브라우저 초기화 실패")
        return
    print("   ✅ 브라우저 초기화 완료")

    try:
        # 2. Login
        print("   🔑 네이버 로그인 중...")
        try:
            naver.login(driver, USER_ID, USER_PW)
        except naver.LoginError as le:
            print(f"   ❌ 로그인 실패: {le}")
            telegram_bot.send_message(f"❌ 로그인 실패: {le}")
            return
        telegram_bot.notify_status(USER_ID, "로그인", "SUCCESS")
        print("   ✅ 로그인 성공")

        # [NEW] 봇 탐지 회피용 랜덤 스텔스 행동 (검색/뉴스/쇼핑 등)
        import human_wanderer
        human_wanderer.perform_wandering(driver, is_first_account=is_first_account)

        # BENCHMARK & TEST 모드는 흐름이 동일 (UI Config 로드, 루프 실행)
        if RUN_MODE in ["BENCHMARK", "TEST"]:
            # ── UI config 로드 ───────────────────────────────────
            ui_cfg = _load_ui_config()

            # 키워드
            if ui_cfg.get("keyword"):
                keyword = ui_cfg["keyword"]
            elif "input" in dashboard_data:
                keyword = dashboard_data["input"]
            else:
                print("   ⚠️ UI에서 설정된 키워드가 없습니다! 임시 테스트 키워드로 대체하여 강제 진행합니다.")
                keyword = "테스트키워드"

            manual_title         = ui_cfg.get("manual_title", "")
            car_model            = ui_cfg.get("car_model", "")
            required_tags        = ui_cfg.get("tags", [])
            biz_name             = ui_cfg.get("biz_name", "")
            blog_count           = int(ui_cfg.get("blog_count", 5))
            watermark_enable     = bool(ui_cfg.get("watermark_enable", True))
            watermark_text       = ui_cfg.get("watermark_text", biz_name or "네이버 블로그")
            image_link           = ui_cfg.get("image_link", "")
            link_pos             = ui_cfg.get("link_pos", "하단")
            schedule_publish     = bool(ui_cfg.get("schedule_publish", False))
            pause_before_publish = bool(ui_cfg.get("pause_before_publish", False))
            post_length          = ui_cfg.get("post_length", "일반형 (1500~1800자)")
            align                = ui_cfg.get("align", "기본")
            advanced_format      = bool(ui_cfg.get("advanced_format", True))
            if pause_before_publish:
                print("   🛑 [모드] 발행 전 멈춤 ON — 에디터에서 직접 발행 버튼 클릭 필요")

            # 페르소나 (노출형 강제 잠금)
            raw_p = ui_cfg.get("persona", "random_exposure")
            EXPOSURE_KEYS = list(gemini_core.EXPOSURE_PERSONAS.keys())
            persona = raw_p if raw_p not in ("random_exposure", "random") and raw_p in EXPOSURE_KEYS else "random_exposure"
            print(f"   🎭 [트랙1] 노출형 페르소나 잠금: {persona}")

            print(f"   🔍 키워드: [{keyword}] | 포스팅 목표: {blog_count}개") 
            if required_tags:
                print(f"   🏷️  태그: {', '.join(required_tags)}")

            # 이미지 수집
            image_paths    = _collect_image_paths(ui_cfg.get("images_dir", ""))
            link_image_path = _collect_link_image(ui_cfg.get("link_image", ""))

            # 벤치마킹 (사전 스크레이핑) - TEST 모드면 통과
            benchmark_facts = ""
            if RUN_MODE == "TEST":
                print("   🧪 테스트 모드: 네이버 검색 스킵")
            else:
                print(f"   🔎 네이버 상위 블로그 분석 시작...")
                benchmark_facts = _run_benchmark(driver, keyword, blog_count, biz_name)

            # 포스팅 루프
            final_title = ""
            for post_idx in range(blog_count):
                try:
                    _post_single(
                        driver, post_idx, blog_count, ui_cfg,
                        benchmark_facts, image_paths, link_image_path,
                        persona, keyword, biz_name, required_tags,
                        manual_title, watermark_enable, watermark_text,
                        image_link, link_pos, schedule_publish,
                        pause_before_publish, USER_ID, post_length,
                        align, advanced_format, car_model
                    )
                except Exception as e:
                    print(f"   ⚠️ [{post_idx+1}] 전체 실패: {e}")
                    telegram_bot.send_message(f"⚠️ 포스팅 {post_idx+1} 실패: {e}")

            print(f"\n   🎉 {blog_count}개 포스팅 모두 완료!")
            telegram_bot.send_message(f"🎉 [{keyword}] {blog_count}개 완료!")

            if final_title:
                rank = rank_tracker.check_rank(driver, keyword, USER_ID)
                if rank:
                    telegram_bot.send_message(f"🎉 '{keyword}' {rank}위 진입!")
                else:
                    telegram_bot.send_message(f"📉 '{keyword}' 30위권 밖")

        elif RUN_MODE == "SEMIAUTO":
            # ══════════════════════════════════════════════════
            # 트랙 2 — 반자동 (직접 입력 + 딜러형 페르소나 전용)
            # 벤치마킹 없음 | 노출형 페르소나 절대 금지
            # ══════════════════════════════════════════════════
            ui_cfg_sa = {}
            try:
                with open("_ui_config.json", "r", encoding="utf-8") as f:
                    ui_cfg_sa = json.load(f)
                print("   📋 [트랙2] UI 설정 로드 완료")
            except Exception as e:
                print(f"   ⚠️ UI 설정 로드 실패: {e}")

            facts = ui_cfg_sa.get("manual_facts", "").strip()
            if not facts:
                print("   ❌ [트랙2] 팩트 없음 — 트랙2 팩트 입력란을 채워주세요")
                raise ValueError("manual_facts 없음")

            biz_sa    = ui_cfg_sa.get("biz_name", "")
            kw_sa     = ui_cfg_sa.get("keyword", "")
            car_model_sa = ui_cfg_sa.get("car_model", "")
            title_sa_manual = ui_cfg_sa.get("manual_title", "")
            tags_sa   = ui_cfg_sa.get("tags", [])
            imgdir_sa = ui_cfg_sa.get("images_dir", "")
            wm_enable_sa = bool(ui_cfg_sa.get("watermark_enable", True))
            wm_text_sa   = ui_cfg_sa.get("watermark_text", biz_sa or "네이버 블로그")
            link_sa      = ui_cfg_sa.get("image_link", "")
            link_pos_sa  = ui_cfg_sa.get("link_pos", "하단")
            link_dir_sa  = ui_cfg_sa.get("link_image", "")
            link_img_sa  = ""
            if link_dir_sa and os.path.exists(link_dir_sa):
                link_fs = [os.path.join(link_dir_sa, f) for f in os.listdir(link_dir_sa) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                if link_fs: link_img_sa = link_fs[0]
                
            sched_sa     = bool(ui_cfg_sa.get("schedule_publish", False))
            pause_sa  = bool(ui_cfg_sa.get("pause_before_publish", False))
            post_length_sa = ui_cfg_sa.get("post_length", "일반형 (1500~1800자)")
            align_sa       = ui_cfg_sa.get("align", "기본")
            adv_format_sa  = bool(ui_cfg_sa.get("advanced_format", True))

            # 딜러형 강제 잠금 (노출형 차단)
            DEALER_KEYS = list(gemini_core.DEALER_PERSONAS.keys())
            persona_sa = ui_cfg_sa.get("persona", "veteran_dealer")
            if persona_sa not in DEALER_KEYS:
                persona_sa = "veteran_dealer"
            print(f"   🎭 [트랙2] 딜러형 잠금: {persona_sa}")

            imgs_sa = []
            if imgdir_sa and os.path.isdir(imgdir_sa):
                exts = (".jpg", ".jpeg", ".png", ".webp")
                imgs_sa = [image_utils.process_image(os.path.join(imgdir_sa, f)) or os.path.join(imgdir_sa, f)
                           for f in sorted(os.listdir(imgdir_sa)) if f.lower().endswith(exts)]
                print(f"   📷 [트랙2] 이미지 {len(imgs_sa)}장")

            content_type_sa = ui_cfg_sa.get("content_type", "inquiry")  # inquiry | review
            ct_label_sa = "문의 전환형" if content_type_sa == "inquiry" else "후기형"
            print(f"   🎓 [트랙2] 콘텐츠 유형: {ct_label_sa}")

            print(f"   ✍️ [트랙2-{ct_label_sa}] Gemini 생성 ({persona_sa})...")
            
            raw_json_sa = gemini_core.client.rewrite_content(
                    facts, persona=persona_sa, biz_name=biz_sa,
                    keyword=kw_sa, car_model=car_model_sa, 
                    must_phrase=ui_cfg_sa.get("must_phrase", ""),
                    must_pos=ui_cfg_sa.get("must_pos", []),
                    persona_type="conversion", 
                    post_length=post_length_sa, advanced_format=adv_format_sa)

            # [NEW] 사용량 카운팅 (AI API 호출 성공 시)
            if raw_json_sa and "user_uid" in ui_cfg_sa and "user_token" in ui_cfg_sa:
                try:
                    from firebase_db import FirestoreClient
                    db = FirestoreClient(ui_cfg_sa["user_token"])
                    is_trial = ui_cfg_sa.get("is_trial", False)
                    usage_type = "freeTrial" if is_trial else "total"
                    db.increment_usage_count(ui_cfg_sa["user_uid"], usage_type=usage_type)
                    print(f"   📊 [발행 카운트] 사용량 기록 완료")
                except Exception as e:
                    print(f"   ⚠️ [Usage] 발행량 계획 추가 실패: {e}")
                    raise Exception("발행량 계획 추가에 실패하여 안정성 사유로 포스팅을 강제 중단합니다.")
                
            if not raw_json_sa:
                raise ValueError("Gemini 응답 없음")

            try:
                s = raw_json_sa.find('{'); e2 = raw_json_sa.rfind('}')
                if s != -1 and e2 != -1:
                    obj = json.loads(raw_json_sa[s:e2+1])
                    title_sa = title_sa_manual or obj.get("title", "자동 제목")
                    body_sa  = obj.get("content", "")
                    print(f"   📝 [트랙2] 제목: {title_sa} | 본문 {len(body_sa)}자")
                    cta_sa = ""
                    # 후기형은 CTA 없음 / 문의전환형만 CTA 삽입
                    if content_type_sa == "inquiry":
                        cta_sa = obj.get("cta_text", "").strip()
                    ai_time_from_json_sa = obj.get("optimal_publish_time", "").strip()
                    ai_seo_tags_sa = obj.get('seo_tags', [])
                    final_tags_sa = list(set(tags_sa + ai_seo_tags_sa))
                    if len(final_tags_sa) > 30:
                        final_tags_sa = final_tags_sa[:30]
                        
                    # 트랙2 이미지 워터마크 세탁
                    final_imgs_sa = _wash_images(imgs_sa, 0, wm_enable_sa, wm_text_sa)
                                
                    post_items_sa = build_random_layout(body_sa, final_imgs_sa, persona_sa, kw_sa, cta_sa, link_sa, link_img_sa, link_pos_sa)
                    print(f"   🚀 [트랙2] 에디터 진입...")
                    
                    sched_time_sa = None
                    if sched_sa:
                        sched_time_sa = _get_schedule_time(ui_cfg_sa, kw_sa or "네이버 블로그", ai_time_from_json_sa)

                    naver.write_post(driver, title_sa, post_items_sa, tags=final_tags_sa,
                                     publish=not pause_sa, schedule_time=sched_time_sa,
                                     align=align_sa, advanced_format=adv_format_sa)
                    if pause_sa:
                        print("   🛑 [트랙2] 멈춤 — 발행 버튼을 직접 눌러주세요")
                    else:
                        print("   ✅ [트랙2] 발행 완료!")
                        try:
                            pu = driver.current_url
                            if "blog.naver.com" in pu:
                                dwell_bot.simulate_reading(driver, pu)
                        except Exception as de: print(f"   ⚠️ 체류 실패: {de}")
                    
                    telegram_bot.notify_status(USER_ID, "반자동 포스팅", "SUCCESS")
                    
                    print(f"   ⏳ 포스팅 완료 후 휴먼 라이크 활동 시작... (검색/쇼핑 등)")
                    try:
                        import human_wanderer
                        human_wanderer.perform_wandering(driver, short_mode=True)
                        time.sleep(random.randint(5, 10))
                    except Exception as we:
                        print(f"   ⚠️ 포스팅 후 딴짓 중 오류 (안전 대기로 대체): {we}")
                        time.sleep(10)

                else:
                    print("   ❌ [트랙2] JSON 파싱 실패")
            except Exception as e:
                print(f"   ❌ [트랙2] 생성 실패: {e}")

        elif RUN_MODE == "NURTURE":
            naver.account_nurturing(driver, "news", 5)
            telegram_bot.notify_status(USER_ID, "계정 육성", "SUCCESS")
            
        elif RUN_MODE == "KIN":
            naver.kin_solver(driver, "장기렌트", "https://blog.naver.com/my_blog")
            telegram_bot.notify_status(USER_ID, "지식인 활동", "SUCCESS")
            
        # [NEW] 모든 모드 종료 직전, 계정 전환을 앞두고 마지막 인간적 스크롤링/대기
        print("   ⏳ 계정 작업 마무리 중... (인간적인 대기)")
        time.sleep(random.randint(5, 10))
        
    except Exception as e:
        print(f"   ⚠️ Global Error: {e}")
        import traceback; traceback.print_exc()
        telegram_bot.send_message(f"❌ 치명적 오류: {e}")
        
    finally:
        print("🎉 계정 프로세스 완료.")
        # Open-Close 원칙: 세션 흔적 완전 제거
        try:
            browser.close_session(driver)
        except Exception:
            try: driver.quit()
            except: pass
def main():
    import auth_client
    global RUN_MODE
    print(f"🤖 [Multi-Account Bot V4] Starting...")
    
    # ── [1] Firebase 인증 및 플랜 확인 ──────────────────────────
    success, plan_obj = auth_client.auth_flow()
    if not success or not plan_obj:
        print("❌ 인증에 실패하였습니다. 봇을 종료합니다.")
        sys.exit(1)
        
    print(f"🔑 [Login Success] 현재 플랜: {plan_obj.name} (최대 {plan_obj.max_accounts}계정)")
    
    # Read _ui_config.json
    config_data = {}
    try:
        with open("_ui_config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"   ⚠️ config 읽기 실패: {e}")
        sys.exit(1)

    dashboard_data = {}
    if len(sys.argv) > 2: dashboard_data["input"] = sys.argv[2]
        
    if config_data.get("MODE") == "MULTI_ACCOUNT":
        accounts = config_data.get("accounts", [])
        
        # ── [2] 플랜 허용 계정 수 제한 ─────────────────────────────────
        if len(accounts) > plan_obj.max_accounts:
            print(f"   ⚠️ [플랜 제한] 현재 플랜({plan_obj.name})은 최대 {plan_obj.max_accounts}개 계정까지만 실행 가능합니다.")
            accounts = accounts[:plan_obj.max_accounts]
            
        print(f"   📋 총 {len(accounts)}개 계정 순차 작업 시작")
        for idx, acc in enumerate(accounts):
            print(f"\n▶️ [{idx+1}/{len(accounts)}] 계정 준비 중: {acc.get('naver_id')}")
            # account 정보를 UI config에 임시로 덮어씌워서 내부 호환성 유지
            try:
                with open("_ui_config.json", "w", encoding="utf-8") as f:
                    json.dump(acc, f, ensure_ascii=False, indent=2)
            except: pass
            
            # 첫 번째 계정 판단 플래그 전달
            is_first = (idx == 0)
            process_account(acc, dashboard_data, is_first_account=is_first)
            
            # 계정 간 대기 (IP 쿨타임 등)
            if idx < len(accounts) - 1:
                acc_delay_skip = acc.get("acc_delay_skip", False)
                if acc_delay_skip:
                    print("   ⏭️ [즉시 실행] 계정 간 대기 없이 바로 다음 계정으로 넘어갑니다.")
                else:
                    import time, random
                    # UI에서 넘어온 값은 분(minute) 단위이므로 초(second) 단위로 변환
                    d_min_val = int(acc.get("acc_delay_min", 60))
                    d_max_val = int(acc.get("acc_delay_max", 120))
                    
                    if d_min_val > d_max_val:
                        d_min_val, d_max_val = d_max_val, d_min_val
                        
                    wait_sec = random.randint(d_min_val * 60, d_max_val * 60)
                    wait_min = wait_sec // 60
                    print(f"   ⏳ 다음 계정 실행 전 {wait_min}분 ({wait_sec}초) 대기 (스텔스 난수 행동 병행)...")
                    
                    # ── [NEW] 대기 시간 동안 가만히 있는 게 아니라 스텔스 모방 행동 수행 ──
                    try:
                        import browser_core
                        wander_driver = browser_core.get_driver("stealth_wanderer", headless=False)
                        if wander_driver:
                            # 7~20번의 행동을 수행하며 대기 시간을 자연스럽게 소비
                            import human_wanderer
                            human_wanderer.perform_wandering(wander_driver, is_first_account=False)
                            browser_core.close_session(wander_driver)
                    except Exception as e:
                        print(f"   ⚠️ 대기 중 스텔스 행동 실패: {e}")
                    
                    # 배회 행동을 마치고 남은 시간이 있다면 마저 대기
                    print("   ⏳ 추가 대기 (안정화 중)...")
                    time.sleep(15) 
                
        print("\n🎉 모든 계정 작업이 완료되었습니다!")
        
    else:
        # 단일 계정 모드 (호환성)
        print("   📋 단일 계정 모드 실행")
        acc = config_data
        if "naver_id" not in acc:
            try:
                with open("account.txt", "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    acc["naver_id"] = lines[0].strip()
                    acc["naver_pw"] = lines[1].strip()
            except: pass
        process_account(acc, dashboard_data, is_first_account=True)

if __name__ == "__main__":
    main()
