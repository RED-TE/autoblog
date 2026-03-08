import re

file_path = r'c:\Users\jhxox\Desktop\blolg_aoto\gemini_core.py'

def is_hangul(char):
    cp = ord(char)
    return (0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

foreign_chars = set()
for char in content:
    if ord(char) > 127 and not is_hangul(char):
        foreign_chars.add(char)

print("Detected non-ASCII, non-Hangul characters:")
for char in sorted(foreign_chars):
    print(f"'{char}' (U+{ord(char):04X})")
