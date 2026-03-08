import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if skip:
        skip = False
        continue
    if 'messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.' in line:
        new_lines.append(line.rstrip('\n') + '\\n트랙 1만 이용 가능합니다.")\n')
        skip = True
    else:
        new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Patched line 682 with v2 script")
