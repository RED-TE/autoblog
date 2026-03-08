# -*- coding: utf-8 -*-
import os
import json

def load_custom_personas():
    """
    외부 커스텀 페르소나 (custom_personas.json) 파일을 로드합니다.
    없으면 빈 딕셔너리를 반환합니다.
    """
    _REAL_BASE = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(_REAL_BASE, "custom_personas.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"   ⚠️ 커스텀 페르소나 로드 실패: {e}")
            return {}
    return {}
