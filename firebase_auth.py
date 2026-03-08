import pyrebase
import webbrowser
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import requests
import json
import firebase_config

# [Local Server] 로그인을 위한 임시 웹서버
auth_code = None
server_instance = None

class LocalAuthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # 터미널 로그 지저분하지 않게 억제

    def do_GET(self):
        global auth_code
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/callback':
            query_params = parse_qs(parsed_path.query)
            if 'code' in query_params:
                auth_code = query_params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                # 성공 메시지 출력
                success_html = """
                <html><body style="font-family:sans-serif; text-align:center; padding-top:50px;">
                    <h1 style="color:#22c55e;">✅ 인증 성공!</h1>
                    <p>이제 브라우저를 닫고 프로그램으로 돌아가셔도 됩니다.</p>
                    <script>setTimeout(function(){ window.close(); }, 3000);</script>
                </body></html>
                """
                self.wfile.write(success_html.encode('utf-8'))
            else:
                self.send_response(400)
                self.wfile.write(b"Authentication Failed. No code found.")
        else:
            self.send_response(404)

class FirebaseAuthClient:
    def __init__(self):
        self.firebase = pyrebase.initialize_app(firebase_config.FIREBASE_CONFIG)
        self.auth = self.firebase.auth()
        self.user = None

    def login_with_google(self):
        global auth_code
        auth_code = None # 초기화
        
        # [NEW] refreshToken 캡처 변수
        self._refresh_token = None
        
        # [NEW] device_id 생성 (웹페이지 요구사항)
        import uuid
        device_id = str(uuid.uuid4())[:8]
        
        # 1. 로컬 서버 시작
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # 2. 브라우저로 외부 로그인 페이지 열기 (device_id 포함)
        login_url = f"https://recarplan.com/prlogin.html?device_id={device_id}"
        print(f"🌍 Opening External Login Page: {login_url}")
        webbrowser.open(login_url)
        
        # 3. 토큰 대기
        print("⏳ Waiting for user login on the web page...")
        timeout = 180 # 3분
        start_time = time.time()
        
        while auth_code is None:
            if time.time() - start_time > timeout:
                print("❌ Login Timeout")
                self.stop_server()
                return None
            time.sleep(1)
            
        print(f"✅ Token Received from Web Page!")
        
        # 4. 서버 중지 및 사용자 정보 설정
        id_token = auth_code
        uid = self.extract_uid(id_token)
        
        # [NEW] Account Info에서 email, refreshToken 추출
        email = ""
        refresh_token = ""
        try:
            account_info = self.auth.get_account_info(id_token)
            if account_info and 'users' in account_info:
                user_info = account_info['users'][0]
                email = user_info.get('email', '')
        except:
            pass
        
        # [NEW] pyrebase current_user에서 refreshToken 가져오기
        try:
            if hasattr(self.auth, 'current_user') and self.auth.current_user:
                refresh_token = self.auth.current_user.get('refreshToken', '')
        except:
            pass
        
        # [NEW] refreshToken이 없으면 idToken으로 custom exchange 시도
        if not refresh_token:
            try:
                import firebase_config
                api_key = firebase_config.FIREBASE_CONFIG.get('apiKey', '')
                # signInWithCustomToken은 custom token 필요하므로 불가
                # 대신 idToken 자체를 "refresh 가능한" 세션으로 저장
                # (securetoken API에 idToken 직접 전달은 불가, refreshToken 필요)
                print("   ℹ️ [Auth] refreshToken 미확보 - 세션은 idToken으로 유지")
            except:
                pass
        
        self.user = {
            "idToken": id_token, 
            "localId": uid,
            "email": email,
            "refreshToken": refresh_token
        }
        self.stop_server()
        return self.user

    def start_server(self):
        global server_instance
        try:
            server_instance = HTTPServer(('localhost', 8080), LocalAuthHandler)
            server_instance.serve_forever()
        except Exception as e:
            print(f"⚠️ Local server error: {e}")

    def stop_server(self):
        global server_instance
        if server_instance:
            # shutdown()은 다른 쓰레드에서 불러야 함. 
            # 여기서는 서버가 어차피 daemon thread이므로 그냥 둬도 되지만 깔끔하게 처리하려면:
            threading.Thread(target=server_instance.shutdown).start()

    def extract_uid(self, id_token):
        try:
            return self.auth.get_account_info(id_token)['users'][0]['localId']
        except:
            return "unknown_uid"

if __name__ == "__main__":
    client = FirebaseAuthClient()
    user = client.login_with_google()
    print(f"Logged in User: {user}")
