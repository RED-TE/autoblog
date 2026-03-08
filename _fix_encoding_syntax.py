import os

# 1. Fix bot_app.py syntax error on line 682
filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.' in line:
        # Instead of risking string manipulation, just hardcode the exact line replacement
        lines[i] = '                messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.\\n트랙 1만 이용 가능합니다.")\n'
        break

# Inject sys.stdout.reconfigure(encoding='utf-8') at the top to fix cp949 errors
first_import_idx = 0
for i, line in enumerate(lines):
    if line.startswith('import '):
        first_import_idx = i
        break

lines.insert(first_import_idx, "import sys\n")
lines.insert(first_import_idx + 1, "if hasattr(sys.stdout, 'reconfigure'):\n")
lines.insert(first_import_idx + 2, "    sys.stdout.reconfigure(encoding='utf-8')\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("bot_app.py fixed")

# 2. Fix main_bot.py encoding issue
main_filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\main_bot.py"
with open(main_filepath, "r", encoding="utf-8") as f:
    main_lines = f.readlines()

first_import_idx = 0
for i, line in enumerate(main_lines):
    if line.startswith('import '):
        first_import_idx = i
        break

main_lines.insert(first_import_idx, "import sys\n")
main_lines.insert(first_import_idx + 1, "if hasattr(sys.stdout, 'reconfigure'):\n")
main_lines.insert(first_import_idx + 2, "    sys.stdout.reconfigure(encoding='utf-8')\n")

with open(main_filepath, "w", encoding="utf-8") as f:
    f.writelines(main_lines)
print("main_bot.py fixed")
