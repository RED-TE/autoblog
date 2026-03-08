# naver_core.py 두 곳 수정: 1) 함수 시그니처, 2) 발행 블록
with open("naver_core.py", "r", encoding="utf-8") as f:
    txt = f.read()

changed = 0

# 1. 함수 시그니처
old1 = "def write_post(driver, title, content_items, tags=None):"
new1 = "def write_post(driver, title, content_items, tags=None, publish=True):"
if old1 in txt:
    txt = txt.replace(old1, new1, 1); changed += 1
    print("✅ 시그니처 변경")
else:
    print("❌ 시그니처 못찾음")

# 2. 발행 블록 앞에 멈춤 처리 추가
old2 = "    # 8. 발행 버튼 클릭\n    try:"
new2 = (
    "    # 8. 발행 버튼 클릭\n"
    "    if not publish:\n"
    "        print(\"   🛑 [멈춤] 발행 전 멈춤 모드 — 에디터에서 직접 발행 버튼을 눌러주세요!\")\n"
    "        return\n"
    "    try:"
)
if old2 in txt:
    txt = txt.replace(old2, new2, 1); changed += 1
    print("✅ 발행 블록 변경")
else:
    # CRLF 버전
    old2b = "    # 8. 발행 버튼 클릭\r\n    try:"
    new2b = new2.replace("\n", "\r\n")
    if old2b in txt:
        txt = txt.replace(old2b, new2b, 1); changed += 1
        print("✅ 발행 블록 변경 (CRLF)")
    else:
        print("❌ 발행 블록 못찾음")
        # 주변 확인
        i = txt.find("# 8. 발행")
        if i >= 0: print("주변:", repr(txt[i:i+60]))

with open("naver_core.py", "w", encoding="utf-8") as f:
    f.write(txt)
print(f"총 {changed}개 변경 완료 → naver_core.py 저장")
