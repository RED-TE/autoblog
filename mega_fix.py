import re

file_path = r'c:\Users\jhxox\Desktop\blolg_aoto\gemini_core.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ensure SYSTEM_CONTEXT_BASE is correctly closed
# We look for SYSTEM_CONTEXT_BASE = """ and ensure it ends before SYSTEM_CONTEXT_EXPOSURE
# A simple way is to replace the gap with a clean closing and opening if needed.

# Let's find the assignment blocks
base_start = content.find('SYSTEM_CONTEXT_BASE = """')
if base_start != -1:
    exposure_start = content.find('SYSTEM_CONTEXT_EXPOSURE =')
    if exposure_start != -1:
        # Get the part that should be SYSTEM_CONTEXT_BASE
        base_part = content[base_start:exposure_start]
        # Remove any existing triple quotes within this part except the first one
        # and ensure it ends with one.
        prefix = 'SYSTEM_CONTEXT_BASE = """'
        body = base_part[len(prefix):].strip()
        # Clean up any triple quotes that might have been accidentally inserted
        body = body.replace('"""', '')
        new_base_part = prefix + '\n' + body + '\n"""\n\n\n'
        content = content[:base_start] + new_base_part + content[exposure_start:]

# 2. Comprehensive Unicode Cleanup (Again, to be safe)
def clean_char(char):
    if ord(char) <= 127: return char
    cp = ord(char)
    # Hangul ranges
    if (0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F):
        return char
    # Specific replacements
    reps = {'—': '-', '→': '->', '←': '<-', '·': '.', '■': '*', '①': '1.', '②': '2.', '③': '3.', '④': '4.', '⑤': '5.'}
    if char in reps: return reps[char]
    return '-'

final_content = "".join(clean_char(c) for c in content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Syntax and Unicode fix applied.")
