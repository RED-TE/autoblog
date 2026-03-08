# -*- coding: utf-8 -*-
# auth_client.py
# [IMPROVED] Client Authentication Module with Process Lock & Caching

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import sys
import time
import traceback
import types
import requests
import hwid_manager
import atexit
from plan_manager import get_plan_from_name, get_plan_from_key, PlanFeatures
from datetime import datetime, timedelta

# ==========================================
# [NEW] Process Lock (중복 실행 방지)
# ==========================================
import tempfile

# [FIX] Windows/Unix 조건부 import
WINDOWS = sys.platform.startswith('win')

if WINDOWS:
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
        print("⚠️ msvcrt 모듈을 찾을 수 없습니다. 프로세스 잠금이 비활성화됩니다.")
else:
    try:
        import fcntl
    except ImportError:
        fcntl = None
        print("⚠️ fcntl 모듈을 찾을 수 없습니다. 프로세스 잠금이 비활성화됩니다.")

LOCK_FILE = os.path.join(tempfile.gettempdir(), "realcar_bot.lock")
_lock_handle = None

def acquire_process_lock():
    """
    프로세스 잠금 획득 (이미 실행 중이면 실패)
    """
    global _lock_handle
    
    # 모듈이 없으면 잠금 비활성화 (항상 성공)
    if WINDOWS and msvcrt is None:
        print("   ⚠️ [Lock] Windows 잠금 모듈 없음 (비활성화)")
        return True
    if not WINDOWS and fcntl is None:
        print("   ⚠️ [Lock] Unix 잠금 모듈 없음 (비활성화)")
        return True
    
    try:
        _lock_handle = open(LOCK_FILE, 'w')
        
        if WINDOWS:
            # Windows: msvcrt.locking
            msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            # Unix/Linux/Mac: fcntl.flock
            fcntl.flock(_lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        _lock_handle.write(str(os.getpid()))
        _lock_handle.flush()
        print("   🔒 프로세스 잠금 획득 성공")
        return True
    except (IOError, OSError):
        print("   ❌ 이미 RealCar Bot이 실행 중입니다!")
        print("      (다른 프로그램을 먼저 종료해 주세요)")
        return False

def release_process_lock():
    """
    프로세스 잠금 해제 (프로그램 종료 시)
    """
    global _lock_handle
    if _lock_handle:
        try:
            if WINDOWS and msvcrt:
                msvcrt.locking(_lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif not WINDOWS and fcntl:
                fcntl.flock(_lock_handle, fcntl.LOCK_UN)
            _lock_handle.close()
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
            print("   🔓 프로세스 잠금 해제 완료")
        except:
            pass

# 프로그램 종료 시 자동으로 잠금 해제
atexit.register(release_process_lock)

# ==========================================
# [NEW] Session Cache (구독 검증 캐싱)
# ==========================================
class SessionCache:
    """
    메모리 기반 세션 캐시 (Firestore API 호출 최소화)
    """
    def __init__(self, ttl_minutes=5):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, uid):
        """캐시에서 플랜 정보 가져오기"""
        if uid in self.cache:
            data, timestamp = self.cache[uid]
            if datetime.now() - timestamp < self.ttl:
                print(f"   💾 [Cache Hit] 캐시된 플랜 사용: {data}")
                return data
            else:
                del self.cache[uid]  # 만료된 캐시 삭제
        return None
    
    def set(self, uid, plan_name):
        """캐시에 플랜 정보 저장"""
        self.cache[uid] = (plan_name, datetime.now())
        print(f"   💾 [Cache Set] 플랜 캐싱: {plan_name} (TTL: {self.ttl.seconds//60}분)")
    
    def clear(self):
        """캐시 초기화"""
        self.cache.clear()

_session_cache = SessionCache(ttl_minutes=5)

# ==========================================
# [LEGACY] urllib3 stub
# ==========================================
def _ensure_urllib3_appengine_stub():
    if "urllib3.contrib.appengine" in sys.modules:
        return
    try:
        import urllib3
    except ImportError:
        pass
    try:
        import urllib3.contrib.appengine
    except ImportError:
        pass
    if "urllib3.contrib.appengine" not in sys.modules:
        contrib = sys.modules.get("urllib3.contrib")
        if contrib is None:
            contrib = types.ModuleType("urllib3.contrib")
            sys.modules["urllib3.contrib"] = contrib
        appengine = types.ModuleType("urllib3.contrib.appengine")
        appengine.is_appengine_sandbox = lambda: False
        appengine.AppEngineManager = type("AppEngineManager", (), {})
        contrib.appengine = appengine
        sys.modules["urllib3.contrib.appengine"] = appengine

_ensure_urllib3_appengine_stub()

# Firebase Modules
try:
    from firebase_db import FirestoreClient
    FIREBASE_AVAILABLE = True
except Exception as e:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase modules not found. Running in Offline Mode.")

# Paths
if getattr(sys, 'frozen', False):
    _exe_dir = os.path.dirname(sys.executable)
    # [FIX] dist/bin 에 위치할 경우 상위 폴더(dist/)를 기준으로 설정
    if os.path.basename(_exe_dir).lower() == 'bin':
        BASE_DIR = os.path.dirname(_exe_dir)
    else:
        BASE_DIR = _exe_dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LICENSE_FILE = os.path.join(BASE_DIR, "license.key")

def get_hwid():
    return hwid_manager.get_hwid()

def log_debug(msg):
    log_path = os.path.join(BASE_DIR, "auth_debug.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# ==========================================
# [IMPROVED] 메인 인증 플로우
# ==========================================
AUTH_SAVE_FILE = os.path.join(BASE_DIR, "launcher_auth.json")

def _refresh_firebase_token(refresh_token):
    """Firebase refreshToken으로 새 idToken 발급 (브라우저 없이!)"""
    try:
        import firebase_config
        api_key = firebase_config.FIREBASE_CONFIG.get('apiKey', '')
        
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            new_id_token = data.get('id_token')
            new_refresh_token = data.get('refresh_token', refresh_token)
            user_id = data.get('user_id')
            print(f"   🔄 [Auth] 토큰 자동 갱신 성공! (UID: {user_id[:5]}...)")
            return new_id_token, new_refresh_token, user_id
        else:
            print(f"   ⚠️ [Auth] 토큰 갱신 실패: {resp.status_code}")
            return None, None, None
    except Exception as e:
        print(f"   ⚠️ [Auth] 토큰 갱신 에러: {e}")
        return None, None, None

def _save_auth_session(uid, id_token, refresh_token, email=""):
    """인증 세션 저장 (다음번 자동 로그인용)"""
    try:
        import json as _json
        with open(AUTH_SAVE_FILE, 'w', encoding='utf-8') as f:
            _json.dump({
                'uid': uid,
                'token': id_token,
                'refreshToken': refresh_token,
                'email': email,
                'timestamp': datetime.now().isoformat(),
                'launcher_authenticated': True
            }, f)
        print(f"   💾 [Auth] 인증 정보 저장 완료 → 다음부터 자동 로그인")
    except Exception as e:
        print(f"   ⚠️ [Auth] 인증 정보 저장 실패: {e}")

def _load_saved_session():
    """저장된 세션 로드 + 자동 갱신"""
    try:
        if not os.path.exists(AUTH_SAVE_FILE):
            return None, None, None
        
        import json as _json
        with open(AUTH_SAVE_FILE, 'r', encoding='utf-8') as f:
            data = _json.load(f)
        
        uid = data.get('uid')
        id_token = data.get('token')
        refresh_token = data.get('refreshToken')
        email = data.get('email', '')
        
        if not uid or not refresh_token:
            print("   ⚠️ [Auth] 저장된 세션이 불완전합니다.")
            return None, None, None
        
        # 무조건 refreshToken으로 새 토큰 발급 (만료 여부 관계없이 안전)
        print(f"   🔄 [Auth] 저장된 세션 발견 → 토큰 자동 갱신 중...")
        new_token, new_refresh, new_uid = _refresh_firebase_token(refresh_token)
        
        if new_token:
            # 갱신 성공 → 새 토큰 저장
            _save_auth_session(new_uid or uid, new_token, new_refresh or refresh_token, email)
            return new_uid or uid, new_token, email
        else:
            print("   ⚠️ [Auth] 토큰 갱신 실패 → 브라우저 로그인 필요")
            return None, None, None
            
    except Exception as e:
        print(f"   ⚠️ [Auth] 세션 로드 실패: {e}")
        return None, None, None

def _process_subscription(uid, id_token, hwid, db_client, email=""):
    """구독 확인 및 접근 권한 처리 (자동로그인/브라우저로그인 공통)"""
    try:
        plan_name = db_client.check_subscription(uid)
        if plan_name and plan_name not in ["free", "trial_consumed", "blocked"]:
            _session_cache.set(uid, plan_name)
        
        log_debug(f"check_subscription: plan_name={plan_name}")
        
        # 차단 유저
        if plan_name == "blocked":
            print(f"   🚫 [Access Denied] 차단된 사용자입니다.")
            import tkinter.messagebox as messagebox
            messagebox.showerror("계정 차단 안내", "이 계정은 관리자에 의해 이용이 차단되었습니다.")
            return False, None
        
        # 유효기간 누락
        if plan_name == "missing_expiry":
            print(f"   🚫 [Access Denied] 유효기간 데이터 누락.")
            import tkinter.messagebox as messagebox
            messagebox.showwarning("오류", "유효기간 데이터가 누락되었습니다.")
            return False, None
        
        # 무료 체험
        if plan_name in ["free", "trial_consumed"] or not plan_name:
            print(f"   🆓 [Trial] 미결제 사용자 감지.")
            is_account_used = (plan_name == "trial_consumed")
            is_hw_used = db_client.check_trial_used(uid, hwid)
            
            if not is_account_used and not is_hw_used:
                print("   ✅ [Trial] 1회 체험 가능!")
                import tkinter.messagebox as messagebox
                messagebox.showinfo("무료 체험 안내", "환영합니다! 1회 무료 체험이 시작됩니다.")
                
                from plan_manager import FEATURES, PlanLevel
                import copy
                trial_plan = copy.deepcopy(FEATURES[PlanLevel.PRO])
                trial_plan.name = "Free Trial (체험판)"
                trial_plan.level = PlanLevel.PRO
                trial_plan.is_trial = True
                trial_plan.uid = uid
                trial_plan.hwid = hwid
                trial_plan.db_client = db_client
                trial_plan.trial_count = 0
                trial_plan.max_trial = 1
                return True, trial_plan
            else:
                reason = "기기" if is_hw_used else "계정"
                print(f"   ❌ [Trial] 이미 체험 완료한 {reason}입니다.")
                import tkinter.messagebox as messagebox
                messagebox.showwarning("체험 만료", f"이미 1회 무료 체험을 완료하셨습니다.")
                return False, None
        
        # 유료 플랜
        if plan_name and plan_name != "free":
            plan_obj = get_plan_from_name(plan_name)
            if not plan_obj:
                print(f"   ❌ 유효하지 않은 구독 플랜: {plan_name}")
                return False, None
            
            # 동시 세션 체크
            print(f"   🛰️ [Auth] 세션 등록 중...")
            success, msg = db_client.register_active_session(uid, hwid)
            if not success:
                print(f"   🚫 {msg}")
                import tkinter.messagebox as messagebox
                messagebox.showerror("중복 로그인", msg)
                return False, None
            
            plan_obj.uid = uid
            plan_obj.hwid = hwid
            plan_obj.db_client = db_client
            
            def cleanup_on_exit():
                try:
                    db_client.cleanup_session(uid, hwid)
                except: pass
            atexit.register(cleanup_on_exit)
            
            log_debug(f"Access granted: {plan_obj.name}")
            print(f"   🔓 [Access Granted] Plan: {plan_obj.name}")
            return True, plan_obj
        else:
            print("   ❌ 유효한 구독 정보가 없습니다.")
            import tkinter.messagebox as messagebox
            messagebox.showwarning("라이선스 안내", "유효한 유료 구독 정보가 없습니다.")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 구독 확인 중 오류: {e}")
        traceback.print_exc()
        return False, None

def auth_flow():
    """
    Main Authentication Flow (개선판)
    
    개선 사항:
    1. 프로세스 잠금 (중복 실행 방지)
    2. 저장된 토큰 자동 갱신 (브라우저 없이!)
    3. 세션 캐싱 (구독 검증 최적화)
    """
    log_debug("Auth Flow Started (Improved)")
    print("=" * 60)
    print("   🔐 RealCar Bot - 라이선스 인증")
    print("=" * 60)
    
    # 1. 프로세스 잠금 획득 (UI에서 실행된 서브프로세스인 경우 스킵)
    is_from_ui = "FROM_UI" in sys.argv
    
    if not is_from_ui:
        if not acquire_process_lock():
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "중복 실행 감지",
                "이미 RealCar Bot이 실행 중입니다.\n\n"
                "실행 중인 프로그램을 먼저 종료한 후 다시 시도해 주세요."
            )
            return False, None
    else:
        log_debug("Bypassing process lock (Subprocess launched FROM_UI)")
    
    # 2. HWID
    log_debug("Getting HWID...")
    try:
        hwid = get_hwid()
        log_debug(f"HWID ok: {hwid[:8]}...")
        print(f"   🖥️  PC ID: {hwid}")
    except Exception as e:
        hwid = "UNKNOWN"
        log_debug(f"HWID failed: {e}")

    # =============================================
    # 3. [NEW] 저장된 세션으로 자동 로그인 시도 (비활성화 - 항상 로그인 창 띄움)
    # =============================================
    # 사용자가 항상 로그아웃 및 로그인 창이 뜨길 원함에 따라 주석 처리
    # uid, id_token, email = _load_saved_session()
    # 
    # if uid and id_token:
    #     print(f"   ✅ 자동 로그인 성공! (UID: {uid[:5]}...) 🎉 브라우저 불필요!")
    #     log_debug(f"Auto-login success: {uid[:5]}...")
    #     
    #     # Firestore로 구독 확인
    #     db_client = FirestoreClient(id_token)
    #     return _process_subscription(uid, id_token, hwid, db_client, email)
    
    # =============================================
    # 4. [FALLBACK] 저장된 세션 없음 → 인증 UI 실행
    # =============================================
    if FIREBASE_AVAILABLE:
        if is_from_ui:
            # UI에서 파생된 프로세스(main_bot.py)는 로그인 창을 띄우지 않고 저장된 세션 활용
            uid, id_token, email = _load_saved_session()
            if uid and id_token:
                db_client = FirestoreClient(id_token)
                return _process_subscription(uid, id_token, hwid, db_client, email)
            else:
                print("   ❌ [Subprocess] 인증 세션을 찾을 수 없습니다.")
                return False, None
                
        log_debug("Launching Desktop Login UI...")
        print("\n   🖥️ 데스크탑 로그인 화면을 띄웁니다... (최초 1회만 필요)")
        try:
            from login_ui import AppLoginWindow
            app = AppLoginWindow()
            app.mainloop()
            
            if app.is_authenticated and app.id_token:
                uid = app.user_id
                id_token = app.id_token
                refresh_token = app.refresh_token
                email = app.user_email
                
                print(f"   ✅ 로그인 성공! (UID: {uid[:5]}...)")
                
                # 인증 세션 저장
                _save_auth_session(uid, id_token, refresh_token, email)
                
                # Firestore 구독 확인
                db_client = FirestoreClient(id_token)
                return _process_subscription(uid, id_token, hwid, db_client, email)
            else:
                log_debug("Login canceled or failed")
                print("   ❌ 로그인이 취소되었거나 실패했습니다.")
                return False, None
        except Exception as e:
            log_debug(f"Desktop Login UI error: {e}")
            print(f"   ⚠️ 데스크탑 로그인 실행 오류: {e}")
            import traceback
            traceback.print_exc()
            return False, None
            
    else:
        # Fallback to Offline Key Check
        log_debug("Firebase unavailable, trying offline key...")
        print("   ⚠️ Firebase 연결 실패. 오프라인 키 인증을 시도합니다.")
        key = load_license_key()
        if key:
            plan_obj = get_plan_from_key(key)
            if plan_obj:
                return True, plan_obj
            else:
                print("   ❌ 유효하지 않은 라이선스 키입니다. (Offline)")
                return False, None
        else:
            print("   ❌ 라이선스 파일 없음.")
            return False, None




def verify_license_offline(license_key):
    """Offline Fallback Verification"""
    key = license_key.upper()
    if key.startswith("LGT-"): return True, "LITE Plan"
    if key.startswith("PRO-"): return True, "PRO Plan"
    if key.startswith("MST-"): return True, "MASTER Plan"
    if key.startswith("AGC-"): return True, "AGENCY Plan"
    return False, "Invalid Key"

def load_license_key():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None
