# -*- coding: utf-8 -*-
# bot_ui.py  —  네이버 블로그 자동화 컨트롤 패널

import streamlit as st
import subprocess
import threading
import os
import sys
import json
import time
import datetime
import queue

# ───────────────────────────────────────────────
# 페이지 설정
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="블로그 자동화 봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ───────────────────────────────────────────────
# 다크 프리미엄 CSS
# ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0a0b0f; }

/* 헤더 배너 */
.hero {
    background: linear-gradient(135deg, #1a1f3a 0%, #0d1117 60%, #1a0d2e 100%);
    border: 1px solid rgba(100, 80, 255, 0.25);
    border-radius: 16px;
    padding: 28px 32px 22px;
    margin-bottom: 24px;
}
.hero h1 { font-size: 2rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { color: #8892aa; margin: 6px 0 0; font-size: 0.95rem; }

/* 카드 */
.card {
    background: #131621;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #7c85a2; margin-bottom: 14px;
}

/* 입력 필드 */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea {
    background: #0d1117 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e8eaf0 !important;
    border-radius: 8px !important;
}
div.stTextInput > div > div > input:focus,
div.stTextArea > div > div > textarea:focus {
    border-color: rgba(167,139,250,0.5) !important;
    box-shadow: 0 0 0 3px rgba(167,139,250,0.12) !important;
}

/* 실행 버튼 */
div.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 1rem !important; padding: 0.7rem 2rem !important;
    transition: all 0.2s;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(124,58,237,0.4) !important;
}

/* 정지 버튼 */
.stop-btn > div > button {
    background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
}

/* 로그 박스 */
.log-box {
    background: #080a0f;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 16px;
    height: 320px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: #adb5c9;
    white-space: pre-wrap;
    word-break: break-all;
}

/* 태그 칩 힌트 */
.tag-hint { color: #5c677d; font-size: 0.78rem; margin-top: 4px; }

/* 상태 뱃지 */
.badge {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 0.75rem; font-weight: 600;
}
.badge-ready  { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.badge-running{ background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.badge-idle   { background: rgba(107,114,128,0.15); color: #9ca3af; border: 1px solid rgba(107,114,128,0.3); }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# 설정 파일 로드/저장 헬퍼
# ───────────────────────────────────────────────
_CONFIG_PATH = os.path.join(os.getcwd(), "_ui_config.json")

def _load_config() -> dict:
    """앱 시작 시 저장된 설정 읽기"""
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_config(cfg: dict):
    """입력값 변경 시 즉시 저장"""
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ───────────────────────────────────────────────
# 세션 상태 초기화 (저장된 값 복원)
# ───────────────────────────────────────────────
_saved = _load_config()

for key, default in {
    "logs": [],
    "process": None,
    "running": False,
    "log_queue": queue.Queue(),
    "images_dir": "",
    "keyword":      _saved.get("keyword", ""),
    "manual_title": _saved.get("manual_title", ""),
    "tags_raw":     ", ".join(_saved.get("tags", [])),
    "biz_name":     _saved.get("biz_name", ""),
    "blog_count":   _saved.get("blog_count", 5),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def add_log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 300:
        st.session_state.logs = st.session_state.logs[-300:]

def log_reader(proc, q):
    for line in iter(proc.stdout.readline, b""):
        try:
            q.put(line.decode("utf-8", errors="replace").rstrip())
        except: pass
    proc.stdout.close()

# ───────────────────────────────────────────────
# 헤더
# ───────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🤖 블로그 자동화 봇</h1>
  <p>네이버 블로그 벤치마킹 &amp; 자동 발행 컨트롤 패널</p>
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# 레이아웃: 왼쪽(설정) / 오른쪽(로그)
# ───────────────────────────────────────────────
left, right = st.columns([1.05, 0.95], gap="large")

# ─── 왼쪽: 설정 ─────────────────────────────────
with left:

    # ── 1. 이미지 업로드 ──────────────────────
    st.markdown('<div class="card"><div class="card-title">📷 이미지 업로드</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "본문에 삽입할 이미지를 선택하세요 (여러 장 가능)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="img_upload",
        label_visibility="collapsed",
    )
    if uploaded_files:
        cols = st.columns(min(len(uploaded_files), 4))
        img_dir = os.path.join(os.getcwd(), "_uploaded_images")
        os.makedirs(img_dir, exist_ok=True)
        saved_paths = []
        for i, f in enumerate(uploaded_files):
            path = os.path.join(img_dir, f.name)
            with open(path, "wb") as out:
                out.write(f.getbuffer())
            saved_paths.append(path)
            with cols[i % 4]:
                st.image(f, width=100)
        st.session_state.images_dir = img_dir
        st.caption(f"✅ {len(uploaded_files)}장 저장됨 → `_uploaded_images/`")
    else:
        st.session_state.images_dir = ""
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2. 주요 설정 ──────────────────────────
    st.markdown('<div class="card"><div class="card-title">⚙️ 포스팅 설정</div>', unsafe_allow_html=True)

    keyword = st.text_input(
        "🔍 주제 / 벤치마킹 키워드",
        placeholder="예: GV70 장기렌트, 김치맛집, 법인리스",
        key="keyword",
    )

    manual_title = st.text_input(
        "📝 제목  (공란이면 AI가 자동 생성)",
        placeholder="직접 입력하면 AI 호출 없이 그대로 사용합니다",
        key="manual_title",
    )
    if manual_title.strip():
        st.caption("✏️ 제목 직접 입력 모드 — AI 호출 없음")
    else:
        st.caption("🤖 제목 공란 → AI가 자동으로 생성합니다")

    tags_raw = st.text_input(
        "🏷️ 필수 태그  (쉼표로 구분)",
        placeholder="예: 법인리스, GV70장기렌트, 수입차리스",
        key="tags_raw",
    )
    st.markdown('<p class="tag-hint">입력한 태그는 발행 시 자동으로 추가됩니다</p>', unsafe_allow_html=True)

    biz_name = st.text_input(
        "🏢 업체명  (AI 글쓰기에 반영)",
        placeholder="예: 한결오토리스, 다음부동산, 맛있는 우리 식당",
        key="biz_name",
    )
    if biz_name.strip():
        st.caption(f"AI가 '{biz_name}' 이름으로 자연스럽게 콘텐츠를 편집합니다")

    blog_count = st.slider(
        "📋 벤치마킹 블로그 수",
        min_value=1, max_value=10, value=st.session_state.blog_count, step=1,
        key="blog_count",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 입력값 자동 저장 (변경 즉시 파일에 기록) ───────
    _save_config({
        "keyword":      st.session_state.keyword,
        "manual_title": st.session_state.manual_title,
        "tags":         [t.strip() for t in st.session_state.tags_raw.split(",") if t.strip()],
        "biz_name":     st.session_state.biz_name,
        "blog_count":   st.session_state.blog_count,
        "images_dir":   st.session_state.images_dir,
    })

    # ── 3. 실행 버튼 ─────────────────────────
    status_badge = ""
    if st.session_state.running:
        status_badge = '<span class="badge badge-running">● 실행 중</span>'
    elif st.session_state.logs:
        status_badge = '<span class="badge badge-ready">● 완료</span>'
    else:
        status_badge = '<span class="badge badge-idle">● 대기</span>'

    st.markdown(f"<div style='margin-bottom:10px'>{status_badge}</div>", unsafe_allow_html=True)

    run_col, stop_col = st.columns(2)
    with run_col:
        run_btn = st.button("🚀 봇 실행", disabled=st.session_state.running, use_container_width=True)
    with stop_col:
        st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
        stop_btn = st.button("⛔ 정지", disabled=not st.session_state.running, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ─── 오른쪽: 로그 ────────────────────────────────
with right:
    st.markdown('<div class="card"><div class="card-title">📟 실행 로그</div>', unsafe_allow_html=True)

    # 로그 폴링 (프로세스가 살아있으면 큐에서 읽기)
    if st.session_state.running and st.session_state.process:
        proc = st.session_state.process
        q = st.session_state.log_queue
        try:
            while True:
                line = q.get_nowait()
                add_log(line)
        except queue.Empty:
            pass
        if proc.poll() is not None:  # 종료됨
            st.session_state.running = False
            add_log("✅ 봇 프로세스 종료됨")

    log_text = "\n".join(st.session_state.logs[-150:]) if st.session_state.logs else "로그가 여기에 표시됩니다..."
    st.markdown(f'<div class="log-box">{log_text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🗑️ 로그 초기화", use_container_width=True):
        st.session_state.logs = []
        st.rerun()

# ───────────────────────────────────────────────
# 실행 로직
# ───────────────────────────────────────────────
if run_btn:
    if not keyword.strip():
        st.error("❌ 주제/키워드를 입력해주세요!")
    else:
        # 설정 파일 저장 (main_bot.py가 읽을 JSON)
        ui_config = {
            "keyword": keyword.strip(),
            "manual_title": manual_title.strip(),
            "tags": [t.strip() for t in tags_raw.split(",") if t.strip()],
            "biz_name": biz_name.strip(),
            "blog_count": blog_count,
            "images_dir": st.session_state.images_dir,
        }
        config_path = os.path.join(os.getcwd(), "_ui_config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(ui_config, f, ensure_ascii=False, indent=2)

        add_log(f"🚀 봇 시작 | 키워드: {keyword} | 블로그: {blog_count}개")
        if manual_title.strip():
            add_log(f"📝 직접 입력 제목: {manual_title}")
        if biz_name.strip():
            add_log(f"🏢 업체명: {biz_name}")
        if ui_config["tags"]:
            add_log(f"🏷️ 태그: {', '.join(ui_config['tags'])}")
        if st.session_state.images_dir:
            add_log(f"📷 이미지 폴더: {st.session_state.images_dir}")

        python_exec = sys.executable
        proc = subprocess.Popen(
            [python_exec, "main_bot.py", "FROM_UI", "BENCHMARK", keyword.strip()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
            bufsize=1,
        )
        st.session_state.process = proc
        st.session_state.running = True
        st.session_state.log_queue = queue.Queue()

        t = threading.Thread(target=log_reader, args=(proc, st.session_state.log_queue), daemon=True)
        t.start()

        st.rerun()

if stop_btn and st.session_state.process:
    st.session_state.process.terminate()
    st.session_state.running = False
    add_log("⛔ 사용자가 봇을 정지시켰습니다")
    st.rerun()

# 실행 중이면 3초마다 자동 새로고침 (로그 업데이트)
if st.session_state.running:
    time.sleep(3)
    st.rerun()
