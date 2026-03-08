import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = 'messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.\n트랙 1만 이용 가능합니다.")'

replacement = 'messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.\\n트랙 1만 이용 가능합니다.")'

if target in content:
    new_content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched line 682")
else:
    print("Target string not found for patching line 682")
