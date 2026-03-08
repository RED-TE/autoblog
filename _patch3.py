# main_bot.py + naver_core.py 두 파일 동시에 수정
import re

# ── naver_core.py ─────────────────────────────────────────────
with open("naver_core.py", "r", encoding="utf-8") as f:
    nc = f.read()

nc = nc.replace(
    "def write_post(driver, title, content_items, tags=None):",
    "def write_post(driver, title, content_items, tags=None, publish=True):",
    1
)
pause_block = (
    "    # 8. 발행 버튼 클릭\n"
    "    if not publish:\n"
    "        print('   🛑 [멈춤] 발행 전 멈춤 모드 ON')\n"
    "        print('   ✏️  에디터에서 내용 확인 후 발행 버튼을 직접 눌러주세요!')\n"
    "        return\n"
    "    try:\n"
)
for old_marker in ["    # 8. 발행 버튼 클릭\n    try:\n", "    # 8. 발행 버튼 클릭\r\n    try:\r\n"]:
    if old_marker in nc:
        nc = nc.replace(old_marker, pause_block.replace("\n", old_marker[-2:], -1) if "\r\n" in old_marker else pause_block, 1)
        print("naver_core: 발행 블록 변경 완료")
        break
else:
    # 직접 삽입
    idx = nc.find("# 8. 발행 버튼 클릭")
    if idx >= 0:
        # find try: after it
        try_idx = nc.find("try:", idx)
        nc = nc[:idx] + pause_block + nc[try_idx+4:]
        print("naver_core: 발행 블록 강제 삽입")

with open("naver_core.py", "w", encoding="utf-8") as f:
    f.write(nc)
print("naver_core.py 저장 완료")

# ── main_bot.py ───────────────────────────────────────────────
with open("main_bot.py", "r", encoding="utf-8") as f:
    mb = f.read()

# pause_before_publish 읽기 추가
mb = mb.replace(
    'images_dir    = ui_cfg.get("images_dir", "")',
    'images_dir    = ui_cfg.get("images_dir", "")\n'
    '            pause_before_publish = bool(ui_cfg.get("pause_before_publish", False))\n'
    '            if pause_before_publish:\n'
    '                print("   🛑 [모드] 발행 전 멈춤 ON — 에디터에서 직접 발행 버튼 클릭 필요")',
    1
)

# write_post 호출에 publish 추가
mb = mb.replace(
    "naver.write_post(driver, title, post_items, tags=required_tags)",
    "naver.write_post(driver, title, post_items, tags=required_tags, publish=not pause_before_publish)",
    1
)

with open("main_bot.py", "w", encoding="utf-8") as f:
    f.write(mb)
print("main_bot.py 저장 완료")
print("✅ 모두 완료")
