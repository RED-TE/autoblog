import os

file_path = r'c:\Users\jhxox\Desktop\blolg_aoto\gemini_core.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace em-dash with standard hyphen
new_content = content.replace('—', '-')

# Also replace some other fancy characters to be safe if they might cause issues in some environments
# (though em-dash was the one reported)
# new_content = new_content.replace('→', '->')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replacement complete.")
