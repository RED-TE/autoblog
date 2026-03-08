# 이 스크립트로 naver_core.py의 write_post 함수에 publish 파라미터를 추가합니다
with open("naver_core.py", "rb") as f:
    content = f.read()

# 함수 시그니처 변경
old_sig = b"def write_post(driver, title, content_items, tags=None):"
new_sig = b"def write_post(driver, title, content_items, tags=None, publish=True):"

# 발행 블록 변경
old_publish = (
    b"    # 8. \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc \xed\x81\xb4\xeb\xa6\xad\r\n"
    b"    try:\r\n"
    b"        print(\"   \xf0\x9f\x9a\x80 [Publish] \xeb\xb0\x9c\xed\x96\x89 \xec\x8b\x9c\xeb\x8f\x84...\")\r\n"
    b"        pub_sel = sels_editor[\"PUBLISH_BTN_1\"]\r\n"
    b"        if browser.click_element(driver, pub_sel, timeout=8):\r\n"
    b"            print(\"   \xe2\x9c\x85 \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc \xed\x81\xb4\xeb\xa6\xad \xec\x99\x84\xeb\xa3\x8c (\xec\xb5\x9c\xec\xa2\x85 \xed\x99\x95\xec\x9d\xb8\xec\x9d\x80 \xec\x88\x98\xeb\x8f\x99)\")\r\n"
    b"            time.sleep(2)\r\n"
    b"        else:\r\n"
    b"            # XPath \xed\x8f\xb4\xeb\xb0\xb1\r\n"
    b"            pub_btn = driver.find_element(\r\n"
    b"                By.XPATH, \r\n"
    b"                \"//button[contains(@class,'btn_upload') or contains(@class,'btn_publish') or contains(text(),'\xeb\xb0\x9c\xed\x96\x89') or contains(text(),'\xec\x99\x84\xeb\xa3\x8c')]\"\r\n"
    b"            )\r\n"
    b"            driver.execute_script(\"arguments[0].click();\", pub_btn)\r\n"
    b"            print(\"   \xe2\x9c\x85 \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc JS \xed\x81\xb4\xeb\xa6\xad \xec\x99\x84\xeb\xa3\x8c\")\r\n"
    b"            time.sleep(2)\r\n"
    b"    except Exception as e:\r\n"
    b"        print(f\"   \xe2\x9a\xa0\xef\xb8\x8f \xeb\xb0\x9c\xed\x96\x89 \xec\x8b\xa4\xed\x8c\xa8: {e}\")\r\n"
)

new_publish = (
    b"    # 8. \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc \xed\x81\xb4\xeb\xa6\xad\r\n"
    b"    if not publish:\r\n"
    b"        print(\"   \xf0\x9f\x9b\x91 [Publish] \xeb\xb0\x9c\xed\x96\x89 \xec\xa0\x84 \xeb\xa9\x88\xec\xb6\xa4 \xeb\xaa\xa8\xeb\x93\x9c: \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc\xec\x9d\x84 \xeb\x88\x84\xeb\xa5\xb4\xec\xa7\x80 \xec\x95\x8a\xec\x8a\xb5\xeb\x8b\x88\xeb\x8b\xa4\")\r\n"
    b"        print(\"   \xe2\x9c\x8f\xef\xb8\x8f  \xea\xb8\x80 \xeb\x82\xb4\xec\x9a\xa9\xec\x9d\x84 \xed\x99\x95\xec\x9d\xb8 \xed\x9b\x84 \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc\xec\x9d\x84 \xec\xa7\x81\xec\xa0\x91 \xeb\x88\x84\xeb\xa5\xb4\xec\x84\xb8\xec\x9a\x94!\")\r\n"
    b"        return\r\n"
    b"    try:\r\n"
    b"        print(\"   \xf0\x9f\x9a\x80 [Publish] \xeb\xb0\x9c\xed\x96\x89 \xec\x8b\x9c\xeb\x8f\x84...\")\r\n"
    b"        pub_sel = sels_editor[\"PUBLISH_BTN_1\"]\r\n"
    b"        if browser.click_element(driver, pub_sel, timeout=8):\r\n"
    b"            print(\"   \xe2\x9c\x85 \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc \xed\x81\xb4\xeb\xa6\xad \xec\x99\x84\xeb\xa3\x8c (\xec\xb5\x9c\xec\xa2\x85 \xed\x99\x95\xec\x9d\xb8\xec\x9d\x80 \xec\x88\x98\xeb\x8f\x99)\")\r\n"
    b"            time.sleep(2)\r\n"
    b"        else:\r\n"
    b"            pub_btn = driver.find_element(\r\n"
    b"                By.XPATH, \r\n"
    b"                \"//button[contains(@class,'btn_upload') or contains(@class,'btn_publish') or contains(text(),'\xeb\xb0\x9c\xed\x96\x89') or contains(text(),'\xec\x99\x84\xeb\xa3\x8c')]\"\r\n"
    b"            )\r\n"
    b"            driver.execute_script(\"arguments[0].click();\", pub_btn)\r\n"
    b"            print(\"   \xe2\x9c\x85 \xeb\xb0\x9c\xed\x96\x89 \xeb\xb2\x84\xed\x8a\xbc JS \xed\x81\xb4\xeb\xa6\xad \xec\x99\x84\xeb\xa3\x8c\")\r\n"
    b"            time.sleep(2)\r\n"
    b"    except Exception as e:\r\n"
    b"        print(f\"   \xe2\x9a\xa0\xef\xb8\x8f \xeb\xb0\x9c\xed\x96\x89 \xec\x8b\xa4\xed\x8c\xa8: {e}\")\r\n"
)

count = 0
if old_sig in content:
    content = content.replace(old_sig, new_sig, 1)
    count += 1
    print(f"시그니처 변경 완료")
else:
    print("시그니처 못찾음")

if old_publish in content:
    content = content.replace(old_publish, new_publish, 1)
    count += 1
    print(f"발행 블록 변경 완료")
else:
    # 그냥 text replace
    content_str = content.decode("utf-8")
    marker = "    # 8. 발행 버튼 클릭\n    try:"
    replacement = "    # 8. 발행 버튼 클릭\n    if not publish:\n        print(\"   🛑 [Publish] 발행 전 멈춤 모드: 발행 버튼을 누르지 않습니다\")\n        print(\"   ✏️  글 내용을 확인 후 발행 버튼을 직접 눌러주세요!\")\n        return\n    try:"
    if marker in content_str:
        content_str = content_str.replace(marker, replacement, 1)
        content = content_str.encode("utf-8")
        count += 1
        print("발행 블록 변경 완료 (text mode)")
    else:
        print("발행 블록도 못찾음")
        # CRLF 시도
        marker2 = "    # 8. 발행 버튼 클릭\r\n    try:"
        if marker2 in content_str:
            replacement2 = "    # 8. 발행 버튼 클릭\r\n    if not publish:\r\n        print(\"   🛑 [Publish] 발행 전 멈춤 모드: 발행 버튼을 누르지 않습니다\")\r\n        print(\"   ✏️  글 내용을 확인 후 발행 버튼을 직접 눌러주세요!\")\r\n        return\r\n    try:"
            content_str = content_str.replace(marker2, replacement2, 1)
            content = content_str.encode("utf-8")
            count += 1
            print("발행 블록 변경 완료 (CRLF mode)")

with open("naver_core.py", "wb") as f:
    f.write(content)
print(f"총 {count}개 변경 완료")
