import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.' in line:
        lines[i] = '                messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.\\n트랙 1만 이용 가능합니다.")\n'

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed syntax error finally")
