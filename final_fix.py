import os

file_path = r'c:\Users\jhxox\Desktop\blolg_aoto\gemini_core.py'

# Mapping of problematic Unicode characters to ASCII equivalents
replacements = {
    '—': '-',    # em-dash
    '–': '-',    # en-dash
    '→': '->',   # arrow
    '←': '<-',   # left arrow
    '…': '...',  # ellipsis
    '·': '.',    # middle dot
    '■': '*',    # square
    '①': '1.',
    '②': '2.',
    '③': '3.',
    '④': '4.',
    '⑤': '5.',
    '⑥': '6.',
    '⑦': '7.',
    '⑧': '8.',
    '⑨': '9.',
    '⑩': '10.',
    '✨': '*',
    '🔄': '*',
    '⚠️': '!',
    '❌': 'X',
    '📢': '*',
    '💬': '*',
    '🎭': '*',
    '🎲': '*',
    '😊': ':)',
    '═': '=',
    '━': '-',
    '─': '-',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
    '·': '.',
}

# Add box drawing characters specifically
for i in range(0x2500, 0x257F + 1):
    replacements[chr(i)] = '=' if chr(i) in '═╦╩╬' else '-'

def is_hangul(char):
    cp = ord(char)
    return (0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F) or (0xA960 <= cp <= 0xA97F) or (0xD7B0 <= cp <= 0xD7FF)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = ""
for char in content:
    if ord(char) <= 127:
        new_content += char
    elif char in replacements:
        new_content += replacements[char]
    elif is_hangul(char):
        new_content += char
    else:
        # Fallback for any other non-ASCII, non-Hangul char
        new_content += '-'

# Final check for double triple quotes if I accidentally created them
new_content = new_content.replace('"""\n\n"""', '"""')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Final comprehensive replacement complete.")
