# -*- coding: utf-8 -*-
"""
updater.py — 자동 업데이트 모듈 (version.json 기반 버전 비교 방식)

동작 방식:
  1. GitHub (RED-TE/autoblog) 의 raw version.json을 HTTP로 다운로드
  2. 로컬 version.json과 버전 비교 (semantic versioning: major.minor.patch)
  3. 원격 버전이 더 높으면 git pull 실행 → 재시작 신호 반환

장점:
  - 네트워크 불안정에 견고한 예외 처리
  - 개발자는 version.json 숫자만 올리면 모든 사용자에게 업데이트 배포
"""

import os
import sys
import json
import subprocess

# ── 설정 ───────────────────────────────────────────────────────────────────
# GitHub RAW 주소 (version.json)
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/RED-TE/autoblog/main/version.json"
# 로컬 버전 파일 경로
LOCAL_VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
# Pull 할 브랜치
GIT_BRANCH = "main"
# ───────────────────────────────────────────────────────────────────────────


def _parse_version(ver_str: str):
    """'4.1.2' 형태의 문자열을 (4, 1, 2) 튜플로 변환 (비교 가능)"""
    try:
        parts = ver_str.strip().split(".")
        return tuple(int(x) for x in parts)
    except Exception:
        return (0, 0, 0)


def get_local_version() -> str:
    """로컬 version.json 의 버전 문자열을 읽어 반환"""
    try:
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # version.json: {"version": "48.8"} 또는 {"version": "4.1.0"} 형태 지원
            return str(data.get("version", "0.0.0")).strip()
    except Exception:
        return "0.0.0"


def get_remote_version() -> str | None:
    """GitHub (RED-TE/autoblog) 의 version.json 에서 원격 버전 문자열을 가져옴. 실패 시 None 반환"""
    try:
        import urllib.request
        with urllib.request.urlopen(REMOTE_VERSION_URL, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return str(data.get("version", "0.0.0")).strip()
    except Exception as e:
        print(f"   ⚠️ [Updater] 원격 버전 확인 실패: {e}")
        return None


def _run_git(args: list) -> str | None:
    """git 명령어를 실행하고 stdout을 반환. 실패 시 None"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        r = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=base_dir,
        )
        if r.returncode == 0:
            return r.stdout.strip()
        print(f"   ⚠️ [Git] {' '.join(args)} → {r.stderr.strip()}")
        return None
    except FileNotFoundError:
        print("   ⚠️ [Updater] git 명령어를 찾을 수 없습니다. Git이 설치되어 있는지 확인하세요.")
        return None
    except Exception as e:
        print(f"   ⚠️ [Updater] git 오류: {e}")
        return None


def _apply_git_pull() -> bool:
    """git pull 을 실행. 성공 시 True"""
    print("   📥 [Updater] 최신 코드를 내려받는 중...")
    # 강제 pull: 로컬 변경사항을 stash 후 pull (충돌 방지)
    _run_git(["stash"])
    result = _run_git(["pull", "origin", GIT_BRANCH, "--rebase", "--autostash"])
    if result is not None:
        print("   ✅ [Updater] git pull 완료!")
        return True
    # fallback: 강제 reset
    print("   🔄 [Updater] pull 실패 → 강제 동기화 시도...")
    _run_git(["fetch", "origin"])
    reset_result = _run_git(["reset", "--hard", f"origin/{GIT_BRANCH}"])
    if reset_result is not None:
        print("   ✅ [Updater] 강제 동기화 완료!")
        return True
    print("   ❌ [Updater] 업데이트 실패. Git 저장소 상태를 확인해 주세요.")
    return False


def check_and_apply_update() -> bool:
    """
    버전을 비교하고, 원격이 더 높으면 git pull을 실행합니다.
    True 반환 → 업데이트 자동 적용됨 (프로그램 재시작 필요)
    False 반환 → 이미 최신 버전이거나 조용히 넘어감
    에러/종료 → 버전 다름 & 자동 업데이트 실패 시 프로그램 강제 종료 후 수동 다운로드 안내
    """
    print("   🔄 [Updater] 버전 확인 중...")

    local_ver  = get_local_version()
    remote_ver = get_remote_version()

    if remote_ver is None:
        # 네트워크 실패 등 원격 버전 확인 불가 시 스킵
        return False

    if _parse_version(remote_ver) <= _parse_version(local_ver):
        return False

    # 업데이트가 존재함
    print(f"\n========================================================")
    print(f"   🚀 [System] 신규 업데이트 발견! (현재: {local_ver} → 최신: {remote_ver})")
    print(f"========================================================\n")

    # .git 폴더 유무 확인
    base_dir  = os.path.dirname(os.path.abspath(__file__))
    git_dir   = os.path.join(base_dir, ".git")
    
    if os.path.isdir(git_dir):
        # 자동 업데이트 시도
        success = _apply_git_pull()
        if success:
            return True

    # 1) .git 폴더가 없거나 (EXE 사용자)
    # 2) git pull 자동 업데이트가 실패했을 경우
    
    import webbrowser
    import time
    
    down_link = "https://drive.google.com/file/d/18d3CgGKfU7qA6McN1sFksksnzhgZLn_m/view?usp=drive_link"
    print("\n   ⚠️ 프로그램 버전을 최신으로 유지해야만 실행 가능합니다.")
    print("   ⚠️ 자동 업데이트를 사용할 수 없는 환경입니다. (혹은 권한 오류)")
    print(f"   👉 아래 구글 드라이브 링크에서 최신 버전({remote_ver})을 다운로드해주세요.")
    print(f"   🌐 다운로드 링크: {down_link}\n")
    
    try:
        # 3초 대기 후 다운로드 링크 창 띄우기
        time.sleep(3)
        webbrowser.open(down_link)
    except Exception:
        pass
        
    print("   ❌ 버전을 맞추지 않으면 봇을 실행할 수 없습니다. 프로그램을 종료합니다.")
    sys.exit(1)


if __name__ == "__main__":
    if check_and_apply_update():
        print("✅ 업데이트 완료! 재시작이 필요합니다.")
    else:
        print("ℹ️ 재시작이 필요하지 않습니다.")
