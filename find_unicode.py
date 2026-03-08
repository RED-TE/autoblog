with open('gemini_core.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        for char in line:
            if ord(char) > 127:
                # Check if it's Korean (Hangul)
                cp = ord(char)
                if not ((0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F)):
                    print(f"Line {i}: Non-ASCII Non-Korean char '{char}' (U+{cp:04X})")
