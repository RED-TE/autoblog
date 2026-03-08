# 정리 스크립트: 임시/레거시 파일을 _legacy/, _dev/ 폴더로 이동
import os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))

def move(src, dst_dir):
    dst = os.path.join(BASE, dst_dir, os.path.basename(src))
    os.makedirs(os.path.join(BASE, dst_dir), exist_ok=True)
    full_src = os.path.join(BASE, src)
    if os.path.exists(full_src):
        shutil.move(full_src, dst)
        print(f"  ✅ {src} → {dst_dir}/")
    else:
        print(f"  ⚠️ 없음: {src}")

# 레거시 (기능 대체됨, 백업 보관)
legacy = [
    "modules.py",       # V1 monolith → naver_core+browser_core+human_action으로 대체
    "bot_ui.py",        # 구버전 Streamlit UI → bot_app.py로 대체
    "dashboard.py",     # 구버전 대시보드
]

# 임시 패치 파일 (작업 완료, 필요 없음)
patches = [
    "_patch_app.py",
    "_patch_naver.py",
    "_patch2.py",
    "_patch3.py",
    "_fix_layout.py",
]

# 개발/테스트 파일
dev = [
    "debug_requests.py",
    "debug_scraper.py",
    "debug_telegram.py",
    "integration_test.py",
    "simple_test.py",
    "test_import.py",
]

# 빈 스텁 (미구현, 아무 데서도 import 안 함)
stubs = [
    "persona_logic.py",
    "plan_manager.py",
    "log_manager.py",
]

print("=== 레거시 이동 ===")
for f in legacy: move(f, "_legacy")

print("\n=== 패치 파일 이동 ===")
for f in patches: move(f, "_legacy/_patches")

print("\n=== 개발 파일 이동 ===")
for f in dev: move(f, "_dev")

print("\n=== 빈 스텁 이동 ===")
for f in stubs: move(f, "_dev/_stubs")

print("\n✅ 정리 완료")
print("\n[현재 핵심 파일들]")
keep = [
    "bot_app.py", "main_bot.py",
    "browser_core.py", "naver_core.py", "naver_scraper.py",
    "gemini_core.py", "human_action.py", "image_utils.py",
    "ui_selectors.py", "config.py",
    "telegram_bot.py", "ip_manager.py", "rank_tracker.py",
]
for f in keep:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  ✅ {f} ({size:,}바이트)")
    else:
        print(f"  ❌ 없음: {f}")
