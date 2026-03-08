import os
filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def __init__(self):" in line:
        # Check if it's the BotApp init
        if i > 0 and "class BotApp" in lines[i-1]:
            lines[i] = "    def __init__(self, plan_obj=None):\n"
            lines.insert(i+1, "        self.plan_obj = plan_obj\n")
            print(f"Patched at line {i}")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)
