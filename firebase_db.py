import requests
import json
import firebase_config
from datetime import datetime

class FirestoreClient:
    def __init__(self, id_token):
        self.id_token = id_token
        self.project_id = firebase_config.FIREBASE_CONFIG['projectId']
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"

    def check_subscription(self, uid):
        """
        Check user's subscription plan from Firestore.
        Path: users/{uid}
        Returns: 'lite', 'pro', 'master', 'trial_consumed' or None
        """
        url = f"{self.base_url}/users/{uid}"
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"   ☁️ [Firestore] Checking subscription for: {uid}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                values = data.get('fields', {})
                
                # [NEW] Trial Check for Account (UID)
                if values.get('trialUsed', {}).get('booleanValue', False):
                    print("   🚫 [Firestore] This account has already used a trial.")
                
                # 1. Status Check (Blocked User)
                status_val = values.get('status', {}).get('stringValue', 'active').lower()
                if status_val == "blocked":
                    print(f"   🚫 [Firestore] Blocked user detected: {uid}")
                    return "blocked"

                # 2. Plan Check
                if 'plan' not in values:
                    print("   ⚠️ [Firestore] User document exists but no 'plan' field.")
                    return None
                    
                plan_val = values['plan'].get('stringValue', 'free').lower()
                
                # [CRITICAL] 무료 회원은 여기서 차단 (단, 체험 여부 정보 반환)
                if plan_val == "free":
                    if values.get('trialUsed', {}).get('booleanValue', False):
                        return "trial_consumed"
                    print("   ❌ [Firestore] Free user detected.")
                    return "free"

                # 2. Expiry Check (Paid plans MUST have an expiryDate)
                if 'expiryDate' not in values:
                    print(f"   ⚠️ [Firestore] {plan_val.upper()} plan found, but NO expiryDate. Falling back to FREE (Trial).")
                    return "free"
                
                ts_str = values['expiryDate'].get('timestampValue')
                if not ts_str:
                    print(f"   ⚠️ [Firestore] Expiry date empty. Falling back to FREE.")
                    return "free"
                    
                try:
                    ts_str = ts_str.replace("Z", "+00:00")
                    expiry_dt = datetime.fromisoformat(ts_str)
                    now_dt = datetime.now(expiry_dt.tzinfo)
                    
                    if now_dt > expiry_dt:
                        print(f"   ❌ [Firestore] Subscription Expired! (Expired: {ts_str})")
                        return None
                    else:
                        print(f"   ✅ [Firestore] Valid Subscription (Plan: {plan_val})")
                        return plan_val
                except Exception as e:
                    print(f"   ⚠️ [Firestore] Date parsing error: {e}")
                    return None
                
            elif response.status_code == 404:
                return "free" # Default to free if no doc
            else:
                return None
                
        except Exception as e:
            print(f"   ⚠️ [Firestore] Exception: {e}")
            return None

    def check_trial_used(self, uid, hwid):
        """
        [IMPROVED] 계정(UID) 또는 기기(HWID) 중 하나라도 사용 기록이 있는지 확인
        """
        url_hwid = f"{self.base_url}/trial_logs/{hwid}"
        headers = {"Authorization": f"Bearer {self.id_token}"}
        
        try:
            res_hwid = requests.get(url_hwid, headers=headers, timeout=10)
            if res_hwid.status_code == 200:
                print(f"   🚫 [Trial] 기기({hwid[:8]}...) 체험 기록 존재")
                return True
        except: pass
        return False

    def mark_trial_used(self, uid, hwid):
        """
        [IMPROVED] 1회 무료 체험 완료 기록 (Firestore)
        """
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Update User Document (UID Block)
        user_url = f"{self.base_url}/users/{uid}?updateMask.fieldPaths=trialUsed"
        user_data = {
            "fields": {
                "trialUsed": {"booleanValue": True}
            }
        }
        
        # 2. Create Trial Log (HWID Block)
        log_url = f"{self.base_url}/trial_logs/{hwid}"
        log_data = {
            "fields": {
                "uid": {"stringValue": uid},
                "hwid": {"stringValue": hwid},
                "usedAt": {"timestampValue": now_iso},
                "status": {"stringValue": "completed"}
            }
        }

        try:
            print(f"   💾 [Firestore] Marking trial used for PC: {hwid[:8]}...")
            response_hwid = requests.patch(log_url, headers=headers, json=log_data, timeout=10)
            
            print(f"   💾 [Firestore] Marking trial used for Account: {uid[:5]}...")
            response_uid = requests.patch(user_url, headers=headers, json=user_data, timeout=10)
            
            return response_uid.status_code in [200, 201] and response_hwid.status_code in [200, 201]
        except Exception as e:
            print(f"   ⚠️ [Trial] Exception: {e}")
            return False

    def register_active_session(self, uid, hwid):
        """
        [NEW] 활성 세션 등록 (라이선스 공유 방지)
        """
        can_login, existing_hwid = self.check_concurrent_limit(uid, hwid)
        if not can_login:
            return False, f"이미 다른 PC에서 로그인 중입니다!\n\nHWID: {existing_hwid}\n\n동시에 1개의 PC에서만 사용 가능합니다."
        
        success, msg, _ = self.update_session_heartbeat(uid, hwid)
        return success, msg

    def update_session_heartbeat(self, uid, hwid):
        """
        [NEW] 세션 생존 주기(Heartbeat) 갱신 및 플랜 유효성 검증
        """
        session_id = f"{uid}_{hwid}"
        url = f"{self.base_url}/activeSessions/{session_id}"
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }
        
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        
        doc_data = {
            "fields": {
                "uid": {"stringValue": uid},
                "hwid": {"stringValue": hwid},
                "lastActive": {"timestampValue": now_iso},
                "status": {"stringValue": "active"}
            }
        }
        
        try:
            print(f"   💓 [Heartbeat] Updating session for {session_id}...")
            response = requests.patch(url, headers=headers, json=doc_data, timeout=10)
            if response.status_code not in [200, 201]:
                return False, f"세션 갱신 실패 ({response.status_code})", False

            user_plan = self.check_subscription(uid)
            if not user_plan:
                return False, "구독이 만료되거나 취소되었습니다.", False
                
            return True, "세션 및 플랜 유효함", True
        except Exception as e:
            print(f"   ⚠️ [Heartbeat] Exception: {e}")
            return False, str(e), False
    
    def check_concurrent_limit(self, uid, current_hwid, max_sessions=1):
        """
        [NEW] 동시 접속 제한 확인
        """
        from datetime import datetime, timezone, timedelta
        url = f"{self.base_url}/activeSessions"
        headers = {"Authorization": f"Bearer {self.id_token}"}
        
        try:
            print(f"   ☁️ [Firestore] Checking active sessions for UID: {uid}...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return True, None
            
            data = response.json()
            documents = data.get('documents', [])
            now = datetime.now(timezone.utc)
            ACTIVE_THRESHOLD_MINS = 15 
            
            active_other_sessions = []
            for doc in documents:
                fields = doc.get('fields', {})
                if fields.get('uid', {}).get('stringValue') != uid or fields.get('hwid', {}).get('stringValue') == current_hwid:
                    continue
                
                last_active_str = fields.get('lastActive', {}).get('timestampValue')
                if last_active_str:
                    try:
                        last_active = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                        if (now - last_active) < timedelta(minutes=ACTIVE_THRESHOLD_MINS):
                            active_other_sessions.append(fields.get('hwid', {}).get('stringValue'))
                    except: continue
            
            if len(active_other_sessions) >= max_sessions:
                return False, active_other_sessions[0]
            return True, None
        except Exception as e:
            print(f"   ⚠️ [Session Check] Exception: {e}")
            return True, None
    
    def cleanup_session(self, uid, hwid):
        """
        [NEW] 세션 정리 (앱 종료 시 호출)
        """
        session_id = f"{uid}_{hwid}"
        url = f"{self.base_url}/activeSessions/{session_id}"
        headers = {"Authorization": f"Bearer {self.id_token}"}
        try:
            print(f"   🧹 [Session] Cleaning up session {session_id}...")
            requests.delete(url, headers=headers, timeout=5)
        except: pass

    def increment_usage_count(self, uid, usage_type="total"):
        """
        [NEW] REST API를 사용하여 사용량 카운트 증가
        usage_type: "total" (전체 사용량) 또는 "freeTrial" (무료 체험 사용량)
        Atomic Increment 사용
        """
        field_path = "totalUsageCount" if usage_type == "total" else "freeTrialCount"
        
        url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents:commit"
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }
        
        body = {
            "writes": [
                {
                    "transform": {
                        "document": f"projects/{self.project_id}/databases/(default)/documents/users/{uid}",
                        "fieldTransforms": [
                            {
                                "fieldPath": field_path,
                                "increment": {"integerValue": "1"}
                            }
                        ]
                    }
                }
            ]
        }
        
        try:
            print(f"   🔢 [Firestore] Incrementing {field_path} for {uid}...")
            response = requests.post(url, headers=headers, json=body, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {field_path} increment successful.")
                return True
            else:
                print(f"   ⚠️ {field_path} increment failed: {response.text}")
                return False
        except Exception as e:
            print(f"   ⚠️ Exception incrementing {field_path}: {e}")
            return False

    def increment_free_trial_count(self, uid):
        """[DEPRECATED] unified increment_usage_count() 사용 권장"""
        return self.increment_usage_count(uid, usage_type="freeTrial")

    def get_free_trial_count(self, uid):
        """
        [NEW] 현재 무료 체험 횟수 조회
        """
        url = f"{self.base_url}/users/{uid}"
        headers = {"Authorization": f"Bearer {self.id_token}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                fields = data.get('fields', {})
                count_val = fields.get('freeTrialCount', {}).get('integerValue', '0')
                return int(count_val)
            return 0
        except:
            return 0

class RestTrialManager:
    """
    [NEW] REST API 기반의 체험 관리자 (Admin SDK 미사용, Client Side 호환)
    기존 FreeTrialManager와 인터페이스 호환
    """
    def __init__(self, db_client, user_id, hwid=None):
        self.db_client = db_client
        self.user_id = user_id
        self.hwid = hwid
        
    def check_free_trial_limit(self, max_count=1):
        """
        체험 제한 체크
        True: 사용 가능 (또한 카운트 증가 안함 - 증가는 별도 호출)
        False: 사용 불가
        """
        current_count = self.db_client.get_free_trial_count(self.user_id)
        if current_count >= max_count:
            print(f"❌ 무료 체험 제한 초과: {current_count}회 (최대 {max_count}회)")
            return False
            
        print(f"✅ 무료 체험 가능 상태: {current_count}/{max_count}회")
        return True

    def increment_trial(self):
        """소모 처리 (1회 증가 + Booean Flag 설정)"""
        # 1. Count 증가
        res = self.db_client.increment_free_trial_count(self.user_id)
        
        # 2. Boolean Flag 설정 (Auth Client 차단용)
        if self.hwid:
            try:
                self.db_client.mark_trial_used(self.user_id, self.hwid)
                print("   💾 [Trial] 체험 완료 플래그(Boolean) 설정 완료")
            except Exception as e:
                print(f"   ⚠️ 체험 완료 플래그 설정 실패: {e}")
                
        return res

if __name__ == "__main__":
    pass
