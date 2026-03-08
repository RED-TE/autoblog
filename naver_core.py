# -*- coding: utf-8 -*-
# naver_core.py — 역호환 파사드 (Backward-Compatible Facade)
# ============================================================
# [리팩토링] 코드가 3개 전담 모듈로 분리됨:
#   naver_login.py   — 로그인 로직
#   naver_writer.py  — 글쓰기 에디터 로직
#   naver_nurture.py — 계정 육성 / 지식인 로직
#
# 기존 코드에서 `import naver_core as naver` 방식으로 사용하던
# 모든 함수/클래스가 이 파일 하나로 그대로 동작합니다.
# 외부 코드 수정 없이 완전 호환됩니다.
# ============================================================

# ── 로그인 ───────────────────────────────────────────────────
from naver_login import (
    LoginError,
    login,
)

# ── 글쓰기 ───────────────────────────────────────────────────
from naver_writer import (
    count_images_in_body,
    wait_for_upload_complete,
    apply_image_link,
    insert_quote,
    NaverBlogUI,
    write_post,
)

# ── 계정 육성 / 지식인 ─────────────────────────────────────
from naver_nurture import (
    account_nurturing,
    kin_solver,
)

# ── 하위 호환: 모듈 전체를 import한 경우를 위해 ───────────
__all__ = [
    "LoginError",
    "login",
    "count_images_in_body",
    "wait_for_upload_complete",
    "apply_image_link",
    "insert_quote",
    "NaverBlogUI",
    "write_post",
    "account_nurturing",
    "kin_solver",
]