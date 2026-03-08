import os

filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\auth_client.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Inject sys.stdout.reconfigure(encoding='utf-8') at the top 
first_import_idx = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('import sys'):
        first_import_idx = i
        break

lines.insert(first_import_idx + 1, "import sys\n")
lines.insert(first_import_idx + 2, "if hasattr(sys.stdout, 'reconfigure'):\n")
lines.insert(first_import_idx + 3, "    sys.stdout.reconfigure(encoding='utf-8')\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("auth_client.py Encoding patched")
