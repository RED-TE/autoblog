import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """if __name__ == "__main__":
    from login_ui import LoginWindow
    
    def on_login_success(user_info):
        print(f"🔑 [Login Success] 인증 정보: {user_info}")
        # 인증 성공 시 본 루트 앱 띄우기
        app = BotApp()
        
        # 앱 로고나 타이틀 등에 플랜/이메일 정보 박기 용이
        app.title(f"[RealCar/blolg] Blog Post Auto-Bot (v50.2) - {user_info.get('plan', 'pro')}  플랜")
        app.mainloop()

    # 최초 실행 창을 로그인 UI 로 띄움
    login_app = LoginWindow(on_login_success)
    login_app.mainloop()
"""

replacement = """if __name__ == "__main__":
    import auth_client
    
    def run_auth_and_launch():
        # 로그인 UI 띄우기 전에 터미널/콘솔 기반 auth_flow 실행
        success, plan_obj = auth_client.auth_flow()
        if success and plan_obj:
            print(f"🔑 [Login Success] 인증 정보: {plan_obj.name}")
            app = BotApp(plan_obj)
            app.title(f"[RealCar/blolg] Blog Post Auto-Bot (v51.0) - {plan_obj.name} 플랜")
            app.mainloop()
        else:
            print("❌ 인증에 실패하여 프로그램을 종료합니다.")
            import sys
            sys.exit(1)

    # 기존 LoginWindow 대신 즉시 auth_flow()를 타게 함
    run_auth_and_launch()
"""

new_content = content.replace(target, replacement)
if target not in content:
    print("WARNING: Target string not found in bot_app.py!")
    # let's try a regex approach or manual slice
    import re
    # Just find index of if __name__ == "__main__":
    idx = content.find('if __name__ == "__main__":')
    if idx != -1:
        new_content = content[:idx] + replacement
        print("Used slice fallback")
        
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Patched bot_app.py final execute block")
