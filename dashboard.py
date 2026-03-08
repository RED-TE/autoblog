import streamlit as st
import sys
import os
import time
import requests
import datetime
import subprocess
import threading
import queue

# Adjust path to import modules
sys.path.append(os.getcwd())
import config
import ip_manager

# Page Config
st.set_page_config(
    page_title="RealCar Bot Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Premium" look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .stTextInput>div>div>input {
        background-color: #262730;
        color: white;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Session State for Logs
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'process' not in st.session_state:
    st.session_state.process = None

def add_log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

# Sidebar
with st.sidebar:
    st.title("🛡️ 관리자 패널")
    
    st.subheader("1. 계정 선택")
    accounts = st.multiselect(
        "사용할 계정",
        ["Account 1", "Account 2", "Account 3", "Account 4"],
        default=["Account 1"]
    )
    
    st.subheader("2. IP 상태")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("📡")
    with col2:
        if st.button("IP 체크"):
            try:
                ip = requests.get("https://api.ipify.org", timeout=3).text
                st.success(f"정상 연결: {ip}")
            except:
                st.error("연결 불안정")
        else:
            st.info("체크 필요")
            
    st.subheader("3. 크레딧 잔액")
    target_date = datetime.date(2026, 3, 21)
    today = datetime.date.today()
    days_left = (target_date - today).days
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Google Cloud</h4>
        <h2 style="color: #00ff00;">₩ 350,000</h2>
        <p>만료일: {days_left}일 남음</p>
    </div>
    """, unsafe_allow_html=True)

# Main Panel
st.title("🚀 작전 모드 선택")

tab1, tab2 = st.tabs(["🤖 자동 벤치마킹", "🧑‍✈️ 반자동 전문가"])

with tab1:
    st.header("자동 벤치마킹 모드")
    col_a, col_b = st.columns(2)
    
    with col_a:
        keyword = st.text_input("검색 키워드", placeholder="예: 제네시스 GV80 즉시출고")
    with col_b:
        persona = st.selectbox("AI 페르소나", ["친절한 조과장 (Dealer)", "냉철한 분석가 (Reporter)", "일반 오너 (User)"])
        
    if st.button("🚀 Start Unattended Mode", key="btn_auto"):
        if not keyword:
            st.warning("키워드를 입력해주세요.")
        else:
            add_log(f"자동 모드 시작: {keyword} ({persona})")
            # Run bot as subprocess with keyword argument
            cmd = [sys.executable, "main_bot.py", "BENCHMARK", keyword]
            st.info(f"명령어 실행: {' '.join(cmd)}")
            
            st.info("봇이 실행되었습니다. 새 터미널 창을 확인해주세요.")
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

with tab2:
    st.header("반자동 전문가 모드")
    fact_text = st.text_area("핵심 팩트 입력", placeholder="모델명: 카니발 하이리무진\n할인: 500만원\n재고: 3대\n특이사항: 화이트 색상 즉시출고 가능")
    uploaded_files = st.file_uploader("이미지 업로드 (드래그 앤 드롭)", accept_multiple_files=True)
    
    if st.button("📝 원고 생성 및 발행", key="btn_semi"):
        if not fact_text:
            st.warning("핵심 정보를 입력해주세요.")
        else:
            add_log("반자동 모드 시작...")
            st.spinner("AI가 원고를 작성 중입니다...")
            time.sleep(2) # Fake delay for UX
            st.success("원고 생성 완료! (자동 발행 프로세스 진입)")
            
            # Simulating execution with facts argument
            cmd = [sys.executable, "main_bot.py", "SEMIAUTO", fact_text]
            st.info(f"명령어 실행: {' '.join(cmd)}")
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

# Logs
st.divider()
st.subheader("📊 실시간 영업 보고서")
log_container = st.container()

with log_container:
    for log in st.session_state.logs[::-1]:
        st.text(log)
