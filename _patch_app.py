# bot_app.py의 subprocess 실행 부분 패치
with open("bot_app.py", "rb") as f:
    content = f.read()

# CRLF 유지하면서 특정 바이트 문자열 교체
old = b'[python, "-X", "utf8", "main_bot.py", "BENCHMARK", keyword],'
new = b'[python, "-u", "-X", "utf8", "main_bot.py", "BENCHMARK", keyword],'
if old in content:
    content = content.replace(old, new, 1)
    with open("bot_app.py", "wb") as f:
        f.write(content)
    print("SUCCESS: -u 플래그 추가 완료")
else:
    print("NOT FOUND - 이미 적용됐거나 파일이 다름")
    # 현재 내용 확인
    idx = content.find(b'main_bot.py')
    if idx >= 0:
        print("현재 내용:", content[max(0,idx-50):idx+80])
