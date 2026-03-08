# -*- coding: utf-8 -*-
import os

CUSTOM_PERSONAS_DIR = os.path.join(os.getcwd(), "personas")

def load_custom_personas() -> dict:
    """
    ./personas 폴더 내의 .txt 파일들을 읽어서
    {'파일명(확장자 제외)': '파일 내용'} 형태의 딕셔너리로 반환합니다.
    """
    custom_dict = {}
    if not os.path.exists(CUSTOM_PERSONAS_DIR):
        try:
            os.makedirs(CUSTOM_PERSONAS_DIR, exist_ok=True)
            # 안내용 샘플 파일 생성
            sample_path = os.path.join(CUSTOM_PERSONAS_DIR, "sample_persona.txt")
            with open(sample_path, "w", encoding="utf-8") as f:
                f.write(
                    "[페르소나: 나만의 커스텀 페르소나]\n\n"
                    "여기에 원하는 페르소나의 성격, 특징, 작성 가이드라인을 적어주세요.\n"
                    "파일 이름(확장자 제외)이 시스템 상의 페르소나 ID가 되며 UI에 표시됩니다."
                )
        except Exception as e:
            print(f"   ⚠️ 커스텀 페르소나 폴더 생성 실패: {e}")
            return custom_dict

    for filename in os.listdir(CUSTOM_PERSONAS_DIR):
        if filename.endswith(".txt"):
            file_id = os.path.splitext(filename)[0]
            file_path = os.path.join(CUSTOM_PERSONAS_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        custom_dict[file_id] = content
            except Exception as e:
                print(f"   ⚠️ 커스텀 페르소나 읽기 실패 ({filename}): {e}")

    return custom_dict

def get_all_personas(base_personas: dict) -> dict:
    """
    기존 페르소나 딕셔너리에 커스텀 페르소나 딕셔너리를 병합하여 반환합니다.
    (기존 딕셔너리를 덮어쓰지 않고 새로운 복사본을 반환)
    """
    merged = base_personas.copy()
    custom_personas = load_custom_personas()
    for p_id, p_content in custom_personas.items():
        # 이미 존재하는 거라면 (커스텀이 덮어씌움)
        merged[p_id] = p_content

    return merged
