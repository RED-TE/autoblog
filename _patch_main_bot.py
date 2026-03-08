import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\main_bot.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """    if config_data.get("MODE") == "MULTI_ACCOUNT":
        accounts = config_data.get("accounts", [])
        print(f"   📋 총 {len(accounts)}개 계정 순차 작업 시작")"""

replacement = """    if config_data.get("MODE") == "MULTI_ACCOUNT":
        accounts = config_data.get("accounts", [])
        
        # ── [2] 플랜 허용 계정 수 제한 ─────────────────────────────────
        if len(accounts) > plan_obj.max_accounts:
            print(f"   ⚠️ [플랜 제한] 현재 플랜({plan_obj.name})은 최대 {plan_obj.max_accounts}개 계정까지만 실행 가능합니다.")
            accounts = accounts[:plan_obj.max_accounts]
            
        print(f"   📋 총 {len(accounts)}개 계정 순차 작업 시작")"""

new_content = content.replace(target, replacement)
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Patched main_bot.py multi account limit")
