# -*- coding: utf-8 -*-
import re, sys

with open("main_bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# 교체할 OLD 블록 (정확히 파일에 있는 텍스트)
OLD = (
    '                             # 포스트 아이템 구성\n'
    '                             post_items = []\n'
    '                             post_items.append({"type": "quote", "style": "quotation_line",\n'
    '                                                "content": f"AI 분석 리포트: {persona}"})\n'
    "                             for p in body_text.split('\\n\\n'):\n"
    '                                 if p.strip():\n'
    '                                     post_items.append({"type": "text", "content": p.strip()})\n'
    '\n'
    '                             # CTA\n'
    '                             try:\n'
    '                                 cta = gemini_core.client.generate_cta(keyword)\n'
    '                                 if cta:\n'
    '                                     post_items.append({"type": "quote", "style": "quotation_corner",\n'
    '                                                        "content": cta.strip()})\n'
    '                             except: pass\n'
    '\n'
    '                             # 이미지 균등 삽입\n'
    '                             if image_paths:\n'
    '                                 interval = max(1, len(post_items) // (len(image_paths) + 1))\n'
    '                                 for img_i, img_p in enumerate(image_paths):\n'
    '                                     ins = min((img_i + 1) * interval, len(post_items))\n'
    '                                     post_items.insert(ins, {"type": "image", "content": img_p})\n'
)

NEW = (
    '                             # ── 포스트 레이아웃 구성 (인용구 + 이미지 자연 배치) ──\n'
    '                             post_items = []\n'
    '                             paragraphs = [p.strip() for p in body_text.split(\'\\n\\n\') if p.strip()]\n'
    '\n'
    '                             def _pick_quote(para):\n'
    '                                 sents = [s.strip() for s in para.split(\'.\') if len(s.strip()) > 15]\n'
    '                                 return (sents[0] + \'.\') if sents else para[:60] + \'...\'\n'
    '\n'
    '                             # 인트로 인용구\n'
    '                             post_items.append({"type": "quote", "style": "quotation_line",\n'
    '                                                "content": f"AI 분석 리포트: {persona}"})\n'
    '\n'
    '                             img_idx    = 0\n'
    '                             text_count = 0\n'
    '                             q_styles   = ["quotation_line", "quotation_corner"]\n'
    '                             q_count    = 0\n'
    '\n'
    '                             for i, para in enumerate(paragraphs):\n'
    '                                 post_items.append({"type": "text", "content": para})\n'
    '                                 text_count += 1\n'
    '\n'
    '                                 # 이미지: 텍스트 2개마다 1장\n'
    '                                 if image_paths and img_idx < len(image_paths) and text_count % 2 == 0:\n'
    '                                     post_items.append({"type": "image", "content": image_paths[img_idx]})\n'
    '                                     img_idx += 1\n'
    '\n'
    '                                 # 인용구: 2~3단락마다 중간 삽입 (마지막 제외)\n'
    '                                 if i < len(paragraphs) - 1 and (i + 1) % random.choice([2, 3]) == 0:\n'
    '                                     post_items.append({"type": "quote",\n'
    '                                                        "style": q_styles[q_count % 2],\n'
    '                                                        "content": _pick_quote(para)})\n'
    '                                     q_count += 1\n'
    '\n'
    '                             # 남은 이미지 마지막에 배치\n'
    '                             while image_paths and img_idx < len(image_paths):\n'
    '                                 post_items.append({"type": "image", "content": image_paths[img_idx]})\n'
    '                                 img_idx += 1\n'
    '\n'
    '                             # CTA 인용구 (마무리)\n'
    '                             try:\n'
    '                                 cta = gemini_core.client.generate_cta(keyword)\n'
    '                                 if cta:\n'
    '                                     post_items.append({"type": "quote", "style": "quotation_corner",\n'
    '                                                        "content": cta.strip()})\n'
    '                             except: pass\n'
)

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open("main_bot.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: 레이아웃 교체 완료!")
else:
    # 대안: 줄 번호 기반
    print("EXACT MATCH FAILED - 줄 번호 기반으로 시도...")
    lines = content.splitlines(keepends=True)
    # 마커 찾기
    s_idx = next((i for i, l in enumerate(lines) if '# 포스트 아이템 구성' in l), -1)
    e_idx = next((i for i, l in enumerate(lines) if 'post_items.insert(ins,' in l), -1)
    if s_idx >= 0 and e_idx >= 0:
        lines[s_idx:e_idx+1] = [NEW]
        with open("main_bot.py", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"SUCCESS (line-based): {s_idx+1}~{e_idx+1} 교체!")
    else:
        print(f"FAIL: s={s_idx}, e={e_idx}")
        sys.exit(1)
