import customtkinter as ctk
import threading
import json
import requests
import webbrowser
from tkinter import messagebox
from firebase_config import FIREBASE_CONFIG

# 테마 설정
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppLoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🚗 시작하기 - 로그인")
        self.geometry("500x700")
        self.resizable(False, False)
        
        # 데스크톱 앱 중앙 배치 (간단화)
        self.eval('tk::PlaceWindow . center')
        
        # 인증 상태 변수
        self.user_email = None
        self.user_id = None
        self.id_token = None
        self.refresh_token = None
        self.is_authenticated = False
        
        # 첫 화면
        self.show_login_screen()

    # ========================================
    # 1. 로그인 화면 (Login Screen)
    # ========================================
    def show_login_screen(self):
        # 기존 위젯 초기화
        for widget in self.winfo_children():
            widget.destroy()
        
        # 로고 영역
        logo = ctk.CTkLabel(self, text="🚗 블로그 자동화", font=("Montserrat Black", 32, "bold"), text_color="#38bdf8")
        logo.pack(pady=(60, 10))
        
        subtitle = ctk.CTkLabel(self, text="로그인하여 봇을 시작하세요", font=("Apple SD Gothic Neo", 14), text_color="#94a3b8")
        subtitle.pack(pady=(0, 40))
        
        # 로그인 폼 카드
        login_frame = ctk.CTkFrame(self, width=380, height=400, corner_radius=15, fg_color="#1e293b")
        login_frame.pack(pady=20, padx=60)
        login_frame.pack_propagate(False)
        
        title = ctk.CTkLabel(login_frame, text="🔒 계정 로그인", font=("Apple SD Gothic Neo", 18, "bold"))
        title.pack(pady=(30, 20))
        
        # 이메일 입력
        self.email_entry = ctk.CTkEntry(login_frame, width=300, height=45, placeholder_text="이메일 주소", font=("Apple SD Gothic Neo", 13))
        self.email_entry.pack(pady=10)
        
        # 비밀번호 입력
        self.password_entry = ctk.CTkEntry(login_frame, width=300, height=45, placeholder_text="비밀번호", show="●", font=("Apple SD Gothic Neo", 13))
        self.password_entry.pack(pady=10)
        
        # 로그인 버튼
        login_btn = ctk.CTkButton(login_frame, text="로그인", width=300, height=45, font=("Apple SD Gothic Neo", 14, "bold"), fg_color="#38bdf8", hover_color="#0ea5e9", command=self.handle_login)
        login_btn.pack(pady=(25, 5))
        
        # 회원가입 전환 버튼
        signup_btn = ctk.CTkButton(login_frame, text="회원가입", width=300, height=40, font=("Apple SD Gothic Neo", 13), fg_color="transparent", border_width=2, border_color="#38bdf8", hover_color="#0f172a", text_color="#38bdf8", command=self.open_signup_url)
        signup_btn.pack(pady=10)
        
        # 상태 메시지
        self.status_label = ctk.CTkLabel(login_frame, text="", font=("Apple SD Gothic Neo", 12), text_color="#ef4444")
        self.status_label.pack(pady=5)
        
        # 엔터키 바인딩
        self.password_entry.bind("<Return>", lambda e: self.handle_login())

    # ========================================
    # 2. 회원가입 화면 ( Signup 웹페이지로 전환)
    # ========================================
    def open_signup_url(self):
        webbrowser.open("https://recarplan.com/signup.html")
    def show_signup_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        logo = ctk.CTkLabel(self, text="🚗 블로그 자동화", font=("Montserrat Black", 28, "bold"), text_color="#38bdf8")
        logo.pack(pady=(40, 10))
        
        signup_frame = ctk.CTkFrame(self, width=380, height=520, corner_radius=15, fg_color="#1e293b")
        signup_frame.pack(pady=10, padx=60)
        signup_frame.pack_propagate(False)
        
        title = ctk.CTkLabel(signup_frame, text="✨ 무료 회원가입", font=("Apple SD Gothic Neo", 18, "bold"))
        title.pack(pady=(20, 15))
        
        self.signup_email = ctk.CTkEntry(signup_frame, width=300, height=45, placeholder_text="이메일 주소", font=("Apple SD Gothic Neo", 13))
        self.signup_email.pack(pady=10)
        
        self.signup_pw = ctk.CTkEntry(signup_frame, width=300, height=45, placeholder_text="비밀번호 (8자 이상)", show="●", font=("Apple SD Gothic Neo", 13))
        self.signup_pw.pack(pady=10)
        
        self.signup_pw_confirm = ctk.CTkEntry(signup_frame, width=300, height=45, placeholder_text="비밀번호 재확인", show="●", font=("Apple SD Gothic Neo", 13))
        self.signup_pw_confirm.pack(pady=10)
        
        signup_btn = ctk.CTkButton(signup_frame, text="가입하기", width=300, height=45, fg_color="#22c55e", hover_color="#16a34a", font=("Apple SD Gothic Neo", 14, "bold"), command=self.handle_signup)
        signup_btn.pack(pady=(25, 5))
        
        back_btn = ctk.CTkButton(signup_frame, text="← 로그인으로 돌아가기", width=300, height=35, fg_color="transparent", border_width=2, border_color="#64748b", hover_color="#0f172a", command=self.show_login_screen)
        back_btn.pack(pady=10)
        
        self.signup_status = ctk.CTkLabel(signup_frame, text="", text_color="#ef4444", font=("Apple SD Gothic Neo", 12))
        self.signup_status.pack(pady=5)

    # ========================================
    # 3. 로직 처리부 (Firebase REST API)
    # ========================================
    def handle_login(self):
        email = self.email_entry.get().strip()
        pwd = self.password_entry.get().strip()
        
        if not email or not pwd:
            self.status_label.configure(text="이메일과 비밀번호를 모두 입력해주세요.")
            return
            
        self.status_label.configure(text="인증 서버와 연결 중...", text_color="#94a3b8")
        threading.Thread(target=self._process_login, args=(email, pwd), daemon=True).start()

    def _process_login(self, email, password):
        api_key = FIREBASE_CONFIG["apiKey"]
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.user_email = email
                self.user_id = data.get('localId')
                self.id_token = data.get('idToken')          # [NEW] idToken 추출
                self.refresh_token = data.get('refreshToken')# [NEW] refreshToken 추출
                self.is_authenticated = True
                
                # 인증 성공 후 창 닫기: 파이어베이스 로그인 성공 시 메인 플로우 진행하도록 제어 반환
                self.after(0, self.destroy)
            else:
                resp_json = resp.json()
                error_msg = resp_json.get('error', {}).get('message', '로그인 실패')
                
                # 사용자 친화적 메시지 변환
                if error_msg == "INVALID_LOGIN_CREDENTIALS":
                    error_msg = "이메일 또는 비밀번호가 올바르지 않습니다."
                elif error_msg == "USER_DISABLED":
                    error_msg = "이용이 정지된 계정입니다."
                
                self.after(0, lambda: self.status_label.configure(text=error_msg, text_color="#ef4444"))
        except requests.exceptions.RequestException:
            self.after(0, lambda: self.status_label.configure(text="네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.", text_color="#ef4444"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"오류: {e}", text_color="#ef4444"))

    def handle_signup(self):
        email = self.signup_email.get().strip()
        pwd = self.signup_pw.get().strip()
        pwd_conf = self.signup_pw_confirm.get().strip()
        
        if not email or not pwd:
            self.signup_status.configure(text="정보를 모두 입력해주세요.")
            return
        if pwd != pwd_conf:
            self.signup_status.configure(text="비밀번호가 일치하지 않습니다.")
            return
        if len(pwd) < 6:
            self.signup_status.configure(text="비밀번호는 6자리 이상이어야 합니다.")
            return
            
        self.signup_status.configure(text="계정 생성 중...", text_color="#94a3b8")
        threading.Thread(target=self._process_signup, args=(email, pwd), daemon=True).start()

    def _process_signup(self, email, password):
        api_key = FIREBASE_CONFIG["apiKey"]
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                self.after(0, lambda: messagebox.showinfo("가입 완료", "가입이 완료되었습니다. 방금 만든 계정으로 로그인해주세요."))
                self.after(0, self.show_login_screen)
            else:
                resp_json = resp.json()
                error_msg = resp_json.get('error', {}).get('message', '회원가입 실패')
                
                if error_msg == "EMAIL_EXISTS":
                    error_msg = "이미 가입된 이메일 계정입니다."
                elif error_msg == "INVALID_EMAIL":
                    error_msg = "올바른 이메일 형식이 아닙니다."
                elif error_msg == "WEAK_PASSWORD : Password should be at least 6 characters":
                    error_msg = "비밀번호가 형식이 잘못되었습니다 (최소 6자)."
                    
                self.after(0, lambda: self.signup_status.configure(text=error_msg, text_color="#ef4444"))
        except requests.exceptions.RequestException:
            self.after(0, lambda: self.signup_status.configure(text="네트워크 오류가 발생했습니다.", text_color="#ef4444"))
        except Exception as e:
            self.after(0, lambda: self.signup_status.configure(text=f"오류: {e}", text_color="#ef4444"))

if __name__ == "__main__":
    app = AppLoginWindow()
    app.mainloop()
    
    if app.is_authenticated:
        print(f"로그인 성공. UID: {app.user_id}")
    else:
        print("로그인 취소됨")
