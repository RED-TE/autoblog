import os
import platform

# .env 파일 지원 (설치: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)
except ImportError:
    pass  # python-dotenv 미설치시 하드코딩 fallback

# 역할 분리 모델 설정
# - ANALYZE: 벤치마킹 핵심 팩트 추출 전용 (똑똑한 모델)
# - MAIN: 블로그 글쓰기 전용 (무제한/고속 모델)
GEMINI_MODEL_ANALYZE  = os.environ.get("GEMINI_MODEL_ANALYZE",  "gemini-3.1-pro-preview")
GEMINI_MODEL          = os.environ.get("GEMINI_MODEL",          "gemini-2.5-flash")
GEMINI_MODEL_FALLBACK = os.environ.get("GEMINI_MODEL_FALLBACK", "gemini-2.5-flash")
# ── Gemini API Keys ──────────────────────────────────────────────
# UI에서 키 입력을 제거했으므로, 여기서 하드코딩된 단일 키를 사용합니다.
GEMINI_API_KEYS = [
    "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0",  # Primary key
    "AIzaSyA15apXjNCUSXxM02w2TNAd3ycN2heI_zs",   # Fallback key
]

# ── Telegram (환경변수 우선, fallback: 하드코딩) ─────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8239932060:AAG_RV8CKTau23Jo0ugIa6mjZZMTuO9MrwE")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8417214531")

# ── 기본 경로 ──────────────────────────────────────────────────
BASE_DIR   = os.getcwd()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IS_MAC     = platform.system() == "Darwin"

# ══════════════════════════════════════════════════════════════
# 멀티 계정 설정 (Multi-Account)
# account.txt 대신 여기서 직접 관리하거나 bot_app.py에서 덮어씁니다.
# ══════════════════════════════════════════════════════════════
# 계정 형식: {"id": "네이버ID", "pw": "비밀번호", "blog_id": "블로그ID"}
# blog_id: 댓글/소통 기능에 사용됩니다 (naver.com 뒤에 오는 값)
ACCOUNTS = [
    # {"id": "account1", "pw": "password1", "blog_id": "account1"},
    # {"id": "account2", "pw": "password2", "blog_id": "account2"},
]

# 하루에 계정당 최대 발행 글 수
MAX_DAILY_POSTS_PER_ACCOUNT = 3

# ══════════════════════════════════════════════════════════════
# 브라우저 해상도 풀 (매 세션마다 랜덤 선택)
# ══════════════════════════════════════════════════════════════
SCREEN_RESOLUTIONS = [
    (1366, 768),
    (1440, 900),
    (1600, 900),
    (1920, 1080),
    (1280, 800),
    (1536, 864),
]

# ── 레거시 호환 (TitlePrompts, PERSONA_PROMPTS) ─────────────────
class TitlePrompts:
    ALL_TITLE_PROMPTS = {
        "AUTO": {"conversion": "Create a title for {car_model}.", "exposure": "Exposure title for {car_model}."},
    }
    AUTO_TITLE_PROMPTS = ALL_TITLE_PROMPTS["AUTO"]

title_prompts = TitlePrompts()

PERSONA_PROMPTS = {
    "dealer_trust": "Act as a trustworthy dealer.",
    "CAR_01":       "Helpful car expert.",
    "RENT_01":      "Rental expert.",
}

TECHNICAL_FORMAT_RULES = "Use JSON strictly."
ANTI_SPAM_KEYWORDS     = ["spam", "illegal"]
