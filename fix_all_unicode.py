import os

file_path = r'c:\Users\jhxox\Desktop\blolg_aoto\gemini_core.py'

# Mapping of problematic Unicode characters to ASCII equivalents
replacements = {
    '—': '-',    # em-dash
    '–': '-',    # en-dash
    '→': '->',   # arrow
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
    '🎲': '*',
    '🎲': '*',
    '═': '=',
    '━': '-',
    '─': '-',
    '━━━━━━━━': '========',
}

def is_hangul(char):
    cp = ord(char)
    # Syllabus: AC00-D7A3, Jamo: 1100-11FF, Compatibility Jamo: 3130-318F
    return (0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_line = ""
    for char in line:
        if ord(char) <= 127:
            new_line += char
        elif char in replacements:
            new_line += replacements[char]
        elif is_hangul(char):
            new_line += char
        else:
            # Fallback for any other non-ASCII, non-Hangul char
            # We use a space or a generic hyphen to keep it safe
            new_line += '-'
    new_lines.append(new_line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Comprehensive replacement complete.")
