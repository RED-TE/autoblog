# -*- coding: utf-8 -*-
# gemini_core.py - Gemini AI 콘텐츠 생성 엔진 v5
# 노출형 5종 + 문의전환형 5종 | 목적별 SYSTEM_CONTEXT 분리 | E-E-A-T 완전 준수

import os
import time
import random
import concurrent.futures
from google import genai
from google.genai import types
import config

warnings_suppressed = True  # google-genai has no FutureWarning


# =======================================================================
# 공통 베이스 컨텍스트 — 모든 요청에 항상 주입
# =======================================================================
SYSTEM_CONTEXT_BASE = """
[전문 분야 고정 - 절대 이탈 금지]
- 허용 주제: 자동차 장기렌트 / 법인리스 / 운용리스 / 금융리스 / 차량 구독 / 중고차 매입
- 위 주제 외 내용(정치, 연예, 무관 제품 광고 등)은 단 한 줄도 포함 금지

[E-E-A-T 기준 — 필수]
- 경험(Experience): 실제 출고 사례, 상담 에피소드, 고객 반응을 1인칭으로 서술
- 전문성(Expertise): 잔존가치(RV), 운용리스/금융리스 차이, 선납금·보증금 구조, 초과 주행 요금 체계 등 전문 용어 자연스럽게 활용
- 권위(Authoritativeness): 월 납입금·보증금 비율·약정 기간 등 구체적 수치를 반드시 포함
- 신뢰(Trust): 장점만 나열 금지 - 단점·위약금·주의사항을 솔직하게 균형 있게 언급

[독창성 - 표절 0% 기준]
- 원문 어휘 90% 이상 새로운 표현으로 대체 (원문 문장·구절 직접 인용 절대 금지)
- 문장 구조는 원문과 완전히 다른 패턴 사용 (주어·술어 순서, 접속어 모두 변경)
- 수치·예시는 사실 범위 안에서 자연스럽게 변형

# ═══════════════════════════════════════════════════════════════════
# 🎯 네이버 상위 블로그 필수 규칙 (측정 가능 기준)
# ═══════════════════════════════════════════════════════════════════

[규칙 1: 구어체 비율 = 65% 이상 (필수)]

측정 공식:
- 총 문장 수 = 마침표(.)로 끝나는 문장 개수
- 구어체 문장 = ~거든요, ~더라고요, ~했어요, ~이에요, ~네요, ~잖아요, ~는데요로 끝나는 문장
- 구어체 비율 = (구어체 문장 수 / 총 문장 수) × 100
- 합격 기준: 65% 이상 / 즉시 폐기 기준: 50% 미만

실행 방법:
"~입니다"를 쓰려고 할 때마다 "~이에요", "~했어요", "~더라고요"로 바꾸세요.

예시:
❌ "장기렌트는 초기 비용이 적습니다" (격식체)
✅ "장기렌트는 초기 비용이 적어요" (구어체)
✅ "장기렌트는 초기 비용이 진짜 적더라고요" (구어체 강화)

[규칙 2: 소제목(##) 스타일]

금지 패턴:
❌ "~의 중요성", "~을 위한 방법", "~에 대한 분석"
❌ "충격적인", "치명적인", "놀라운"
❌ 격식체 명사형 종결 ("~을 통한 해결", "~의 필요성")

권장 패턴:
✅ "~했더니 [결과]" (경험담형) → 예: "장기렌트로 바꿨더니 월 30만원 아꼈어요"
✅ "[A]랑 [B] 뭐가 다른지 아세요?" (질문형) → 예: "운용리스랑 장기렌트 뭐가 다른지 아세요?"
✅ "[대상]이 안 알려주는 [정보]" (정보형) → 예: "딜러가 안 알려주는 할인 방법"

구체 비교:
❌ "견적서 받고 폰 엎어버릴 뻔한 사연" (자극적)
❌ "할부 대신 장기렌트로 방향을 틀다" (격식체)
✅ "카니발 견적 받고 멘탈 나간 날" (일상어 + 구어체)
✅ "장기렌트로 바꿨더니 완전히 달라짐" (경험담 + 구어체)

[규칙 3: 숫자 표현 인간화]

패턴: 범위 먼저 → 정확한 값 나중 (절대 규칙)

❌ AI 스타일 (금지): "월 73만 원입니다"
✅ 사람 스타일 (필수): "월 70만 원 초반대예요. 정확히는 73만 원이었습니다"

변환 템플릿:
- 73만 원 → "70만 원 초반대 → 정확히는 73만 원"
- 88만 원 → "80만 원 후반대 → 정확히는 88만 원"
- 530만 원 → "500만 원 중반대 → 정확히는 530만 원"
- 32% → "대략 30% 조금 넘게"
- 95% → "거의 100% 가까이"

[규칙 4: 문단 길이 강제 불규칙화]

금지:
❌ 모든 문단이 3-4문장으로 균일 → 즉시 폐기

필수:
✅ 1문장 임팩트 문단 최소 2개 (독립 문단)
✅ 5문장 긴 문단 뒤에 반드시 1-2문장 짧은 문단 배치

올바른 패턴 예시:
1문장 (임팩트)
→ 5문장 (상세 설명)
→ 2문장 (정리)
→ 3문장 (전환)
→ 1문장 (강조)
→ 4문장 (설명)

1문장 임팩트 예시:
"실제론 다릅니다."
"전혀요."
"오히려 손해였어요."
"완전히 달랐거든요."
"그래서 선택했습니다."

[즉시 폐기 트리거]
아래 중 하나라도 발견되면 해당 글 즉시 폐기 및 재작성:
🚨 구어체 비율 50% 미만
🚨 소제목에 격식체 명사형 2개 이상
🚨 "출처 입력" 또는 "AI 분석" 문구 발견
🚨 동일 소제목 2회 이상 반복
🚨 모든 문단이 3-4문장으로 균일

[절대 금지 표현]
- "안녕하세요"로 시작
- "오늘은 ~에 대해 알아보겠습니다"
- "이상으로 ~를 마치겠습니다"
- "첫째, 둘째, 셋째" 나열형 구조
- "가장 좋은", "최고의" 근거 없는 최상급
- "AI 분석 리포트", "출처 입력", "기자", "작성자:" 메타 정보
- 글 내용과 무관한 명언·속담 삽입

[출력 전 필수 자가 점검 - 절대 어기지 말 것]
1. "출처 입력" 문구가 단 1개라도 있는가? → 있으면 즉시 삭제
2. 동일한 소제목이 2번 이상 반복되는가? → 있으면 한 개만 남기고 삭제
3. 내용 없이 소제목만 연속 2개 나오는가? → 있으면 구조 재작성
4. "AI 분석 리포트", "출처:", "작성자:", "기자" 등의 메타 정보가 있는가? → 있으면 즉시 삭제

위 4가지 중 1개라도 발견되면 그 글은 발행 불가능합니다.

# =======================================================================
[제목 작성 규칙 - C-Rank + 네이버 홈 클릭율 최적화]
# =======================================================================

* 제목 길이: 최적 25~35자 (40자 초과 금지, 15자 이하 금지)

* 클릭을 부르는 제목 공식 7가지 (매 글마다 랜덤으로 1가지 선택)

  [공식 1] 숫자 + 구체적 결과
  예시: "월 6만원 아낀 테슬라 장기렌트 조건, 이거였어요"

  [공식 2] 반전·의외성
  예시: "보증금 없는 조건, 사실 더 비쌀 수 있어요"

  [공식 3] 공감형 상황 묘사
  예시: "매달 렌트료 내면서 '내가 잘 계약한 건가' 싶은 분"

  [공식 4] 금지·경고형
  예시: "이 조건 모르고 장기렌트 계약하면 3년 후 후회합니다"

  [공식 5] 비교·선택 도움형
  예시: "장기렌트 vs 할부, 같은 차 3년 타면 얼마나 차이날까요"

  [공식 6] 시의성·긴급성
  예시: "2025년 테슬라 장기렌트 조건, 작년이랑 이게 달라졌어요"

  [공식 7] 내부자 정보형
  예시: "딜러들이 먼저 말 안 해주는 장기렌트 조건 있어요"

* 제목에 절대 넣지 말아야 할 것:
  - "[1편]", "<1편>", "①" 등과 같은 시리즈물 표기 기호 및 문구 절대 금지
  - "~하는 방법 N가지", "완벽 정리", "총정리", "꿀팁", "꼭 알아야 할"
  - 업체명을 제목 앞에 배치, 느낌표(!) 남발

* C-Rank 키워드 배치 규칙:
  - 핵심 키워드는 제목 앞 15자 이내에 배치
  - 키워드는 1개 메인 + 1개 서브까지만

* 제목 후보 생성 규칙:
  - 매 글마다 제목 후보 3개 생성 (각각 다른 공식으로)
  - JSON 출력에는 선택된 제목 1개 + 탈락한 후보 2개 포함
"""








# =======================================================================
# 노출형 전용 추가 컨텍스트 - 검색 노출.클릭.체류시간.재방문 극대화
# =======================================================================
SYSTEM_CONTEXT_EXPOSURE = SYSTEM_CONTEXT_BASE + """
[네이버 C-Rank 노출 최적화 - 노출형 전용]
- 핵심 키워드를 제목.첫 100자.소제목.본문 마무리에 자연스럽게 총 3-5회 분산 배치
- 소제목(##)을 최소 2개 이상 사용해 문단 구조를 명확히 구분 -> 체류시간 증가
- 글 말미에 반드시 다음 편 예고 또는 시리즈 연결 문장 1개 삽입 -> 재방문율 상승
- 검색 의도(정보형/비교형/문제해결형)에 정확히 대응하는 내용 구성 필수
- 독자가 댓글.저장.공유를 자연스럽게 하도록 유도하는 문장 포함
- 제목에 숫자 또는 연도 포함 권장 (클릭률 상승 효과)
"""

# =======================================================================
# 문의전환형 전용 추가 컨텍스트 - 신뢰 구축 -> 상담 문의 전환 극대화
# =======================================================================
SYSTEM_CONTEXT_CONVERSION = SYSTEM_CONTEXT_BASE + """
[문의 전환 최적화 - 문의전환형 전용]
- 글의 목적은 독자가 읽고 나서 "이 사람/업체에 상담하고 싶다"는 마음이 들게 하는 것
- 신뢰 구축 -> 공감 -> 구체적 조건 제시 -> 행동 유도(CTA) 순서로 흐름 구성
- CTA는 글 중반(1회)과 말미(1회), 총 2회 자연스럽게 삽입 (광고처럼 보이지 않게)
- 독자의 불안.의심.망설임을 먼저 인정하고, 해소하는 구조로 전개
- 업체명 또는 상담 연결 정보는 강요 없이 맥락 속에 녹여서 1-2회만 언급
- 소제목(##)은 선택 사항 - 흐름을 해치지 않는다면 사용, 해친다면 생략
"""


import persona_v2

# V2 + V1 + BIZ + RE + AUTO + Custom 전체 통합 페르소나 (persona_v2에서 통합됨)
ALL_PERSONAS = persona_v2.ALL_PERSONAS_DICT

# Aliases for backward compatibility
EXPOSURE_PERSONAS = ALL_PERSONAS
CONVERSION_PERSONAS = ALL_PERSONAS
DEALER_PERSONAS = ALL_PERSONAS

# V2 전용 맵 (UI 등에서 명시적으로 구분할 때 사용)
EXPOSURE_V2_KEYS = list(persona_v2.EXPOSURE_PERSONAS_V2.keys())
CONVERSION_V2_KEYS = list(persona_v2.CONVERSION_PERSONAS_V2.keys())
CHEAT_SHEET = persona_v2.PERSONA_CHEAT_SHEET

# SYSTEM_CONTEXT 매핑
SYSTEM_CONTEXT_MAP = {
    "exposure":    SYSTEM_CONTEXT_EXPOSURE,
    "conversion":  SYSTEM_CONTEXT_CONVERSION,
}

def clean_generated_content(text: str) -> str:
    """
    생성된 글에서 AI 메타 정보 자동 제거
    """
    import re
    if not text: return text
    
    # 1. "출처 입력" 완전 제거
    text = text.replace("출처 입력", "")
    text = text.replace("출처입력", "")
    
    # 2. 중복 소제목 제거 (완전 동일한 ## 제목이 연속으로 나올 경우)
    lines = text.split("\n")
    cleaned_lines = []
    prev_h2 = None
    
    for line in lines:
        if line.strip().startswith("## "):
            # 소제목 정규화 (마침표 제거 후 비교)
            normalized = line.strip().rstrip(".").strip()
            if normalized == prev_h2:
                continue  # 중복 소제목 건너뛰기
            prev_h2 = normalized
        cleaned_lines.append(line)
    
    text = "\n".join(cleaned_lines)
    
    # 3. 기타 메타 정보 제거
    meta_patterns = [
        r"작성자:\s*\S+",
        r"AI 분석 리포트",
        r"출처:\s*\S+",
    ]
    for pattern in meta_patterns:
        text = re.sub(pattern, "", text)
    
    # 4. 연속 빈 줄 정리 (3개 이상 → 2개로)
    text = re.sub(r"\n\n\n+", "\n\n", text)
    
    return text.strip()

# =======================================================================
class GeminiClient:
    def __init__(self):
        self.api_keys = config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.client = None          # google-genai Client
        self.model_generate = None  # 글쓰기 전용 모델명 (Flash, 무제한)
        self.model_analyze  = None  # 팩트 추출 전용 모델명 (Pro, 지능형)
        self.model = None           # 호환성 alias
        self._initialize_client()

    def _make_safety(self):
        return [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT',        threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH',        threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT',  threshold='BLOCK_NONE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT',  threshold='BLOCK_NONE'),
        ]

    def _initialize_client(self):
        if not self.api_keys:
            print("❌ No Gemini API Keys in config.py")
            return
        api_key = self.api_keys[self.current_key_index]
        self.client = genai.Client(api_key=api_key)

        # 포스팅 작성 전용 (대량/고속/무제한)
        self.model_generate = getattr(config, "GEMINI_MODEL", "gemini-2.0-flash-lite")
        # 팩트 분석 전용 (똑똑한 모델)
        self.model_analyze  = getattr(config, "GEMINI_MODEL_ANALYZE", "gemini-3.1-pro-preview")
        self.model = self.model_generate  # 호환성
        print(f"   ✅ Gemini [Generate] ready: {self.model_generate}")
        print(f"   🧠 Gemini [Analyze] ready: {self.model_analyze}")

    def _rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._initialize_client()

    def _call_model(self, model_name: str, prompt: str, label: str = "") -> str | None:
        """
        실제 API 호출 로직. ThreadPoolExecutor로 60초 타임아웃 + 지수 백오프 재시도.
        model_name: self.model_generate 또는 self.model_analyze
        """
        fallback_model = getattr(config, "GEMINI_MODEL_FALLBACK", "gemini-2.0-flash-lite")
        max_retries = len(self.api_keys) + 1

        def _do_call(m_name):
            gen_cfg = types.GenerateContentConfig(
                temperature=random.uniform(0.75, 0.95),
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                safety_settings=self._make_safety(),
            )
            resp = self.client.models.generate_content(
                model=m_name,
                contents=prompt,
                config=gen_cfg,
            )
            return resp.text

        for attempt in range(max_retries):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_do_call, model_name)
                    return future.result(timeout=90)
            except concurrent.futures.TimeoutError:
                print(f"   ⚠️ [Timeout] {label} 호출 90초 초과. 재시도 {attempt+1}/{max_retries}")
                if len(self.api_keys) > 1:
                    self._rotate_key()
                else:
                    time.sleep(5)
            except Exception as e:
                msg = str(e).lower()
                print(f"   ⚠️ Gemini API Error [{label}]: {e}")
                if "429" in msg or "quota" in msg:
                    if len(self.api_keys) <= 1:
                        print("   ⏳ [Quota] 60초 대기 후 재시도...")
                        time.sleep(60)
                    else:
                        self._rotate_key()
                        time.sleep(2)
                elif "500" in msg or "503" in msg:
                    print(f"   🔄 [Recovery] 서버 오류 재시도 {attempt+1}/{max_retries}...")
                    if attempt >= 1:
                        print(f"   ⚠️ 복구 실패 → Flash 폴백으로 전환")
                        model_name = fallback_model
                    time.sleep(3)
                else:
                    return None
        return None

    def generate(self, prompt: str, persona_type: str = "exposure") -> str | None:
        """Gemini API 호출 - 글쓰기 전용 모델(Flash) 사용."""
        system_ctx = SYSTEM_CONTEXT_MAP.get(persona_type, SYSTEM_CONTEXT_EXPOSURE)
        full_prompt = system_ctx + "\n\n" + prompt
        return self._call_model(self.model_generate, full_prompt, label="Generate")


    def extract_info(self, text: str) -> str:
        """\uc2a4\ud06c\ub808\uc774\ud551\ub41c \uc6d0\ubb38\uc5d0\uc11c \ud575\uc2ec \ud329\ud2b8\ub9cc \uad6c\uc870\ud654 \ucd94\ucd9c - \uc9c0\ub2a5\ud615 \ubaa8\ub378(Pro) \uc0ac\uc6a9."""
        prompt = f"""
\ub2e4\uc74c \ube14\ub85c\uadf8 \uc6d0\ubb38\uc5d0\uc11c \uc7a5\uae30\ub80c\ud2b8/\ub9ac\uc2a4 \uad00\ub828 \ud595\uc2ec \uc815\ubcf4\ub9cc JSON\uc73c\ub85c \ucd94\ucd9c\ud558\uc138\uc694.

\ucd94\ucd9c \ud56d\ubaa9:
- \uc2dc\uc885 / \ubaa8\ub378\uba85
- \uc6d4 \ub0a9\uc785\uae08 \ub610\ub294 \uac00\uaca9\ub300
- \uc8fc\uc694 \ud2b9\uc9d5/\uc635\uc158
- \uc7a5\uc810 / \ub2e8\uc810 (\uac01 2~3\uac00\uc9c0)
- \ud2b9\ubcc4 \ud504\ub85c\ubaa8\uc158 (\uc788\uc744 \uacbd\uc6b0)
- \uc0c1\ub2f4/\ubb38\uc758 \ubc29\ubc95

\uc6d0\ubb38 (\ucd5c\ub300 5000\uc790):
{text[:5000]}

\ucd9c\ub825: JSON \ud615\uc2dd\ub9cc
"""
        full_prompt = SYSTEM_CONTEXT_BASE + "\n\n" + prompt
        return self._call_model(self.model_analyze, full_prompt, label="Analyze")

    def rewrite_content(self, facts: str, persona: str = "random_exposure",
                        biz_name: str = "", keyword: str = "", car_model: str = "",
                        must_phrase: str = "", must_pos: list = None,
                        persona_type: str = "exposure", post_length: str = "일반형 (1500~1800자)",
                        advanced_format: bool = True) -> str:
        """
        핵심 팩트를 기반으로 완전히 새로운 블로그 글을 작성합니다.
        ... (중략) ...
        """
        # ── 페르소나 선택 로직 ───────────────────────────────────────
        if persona_type == "random":
            selected_key = random.choice(list(ALL_PERSONAS.keys()))
        elif persona_type in ("exposure",):
            selected_key = (persona if persona in ALL_PERSONAS
                            else random.choice(list(ALL_PERSONAS.keys())))
        elif persona_type in ("conversion", "dealer"):
            selected_key = (persona if persona in ALL_PERSONAS
                            else random.choice(list(ALL_PERSONAS.keys())))
        else:  # "auto"
            _fallback = next(iter(ALL_PERSONAS))
            selected_key = persona if persona in ALL_PERSONAS else _fallback

        # ── 페르소나 타입 자동 판별 (SYSTEM_CONTEXT 선택용) ──────────
        # persona_type 파라미터(exposure/conversion)를 우선적으로 따름
        if persona_type in ("conversion", "dealer"):
            resolved_type = "conversion"
        else:
            resolved_type = "exposure"
        persona_desc  = ALL_PERSONAS[selected_key]
        persona_label = "노출형" if resolved_type == "exposure" else "문의전환형"

        # ── 글 구조 선택 ─────────────────────────────────────────────
        exposure_structures = [
            "1. 결론 먼저 제시 (2-3줄) -> 2. 배경.원인 설명 -> 3. 핵심 데이터.비교 -> 4. 독자 행동 가이드 -> 5. 다음 편 예고",
            "1. 문제 상황 스토리 도입 -> 2. 원인 분석 -> 3. 해결 방법 단계별 -> 4. 체크리스트 -> 5. 시리즈 연결",
            "1. 숫자.통계로 훅 -> 2. A케이스 vs B케이스 비교 -> 3. 전문가 결론 -> 4. 댓글.저장 유도",
        ]
        conversion_structures = [
            "1. 독자 공감 도입 -> 2. 신뢰 구축 (경력.사례) -> 3. 구체적 조건.수치 -> 4. 주의사항 솔직하게 -> 5. 상담 CTA",
            "1. 실제 계약 사례 스토리 -> 2. Q&A 2-3개 -> 3. 담당자 개인 추천 -> 4. 문의 CTA",
            "1. 단점.위험 먼저 솔직하게 -> 2. 그럼에도 유리한 케이스 -> 3. 월 납입금 시뮬레이션 -> 4. 상담 신청 CTA",
        ]

        selected_structure = (random.choice(exposure_structures)
                              if resolved_type == "exposure"
                              else random.choice(conversion_structures))

        biz_inject = (
            f"\n업체명: '{biz_name}' - 본문에 자연스럽게 1~2회 언급, 광고티 금지"
            if biz_name else ""
        )
        keyword_inject = (
            f"\n핵심 키워드: '{keyword}' - 제목·첫 100자·소제목에 반드시 포함, 본문 전체 3~5회 분산"
            if keyword else ""
        )
        car_model_inject = (
            f"\n핵심 차종: '{car_model}' - 반드시 제목에 최우선적으로 명시하고, 본문과 해시태그에서도 이 차종을 집중적으로 다루세요."
            if car_model else ""
        )
        
        must_include_inject = ""
        if must_phrase and must_pos:
            must_include_inject += "\n[🚨 사용자 지정 필수 포함 문구 - 절대로 누락하지 말고 정확하게 삽입하세요! 🚨]\n"
            if "top" in must_pos:
                must_include_inject += f"- 글의 '상단 (도입부)' 부근에 다음 문구를 반드시 포함하세요: \"{must_phrase}\"\n"
            if "mid" in must_pos:
                must_include_inject += f"- 글의 '중간 (본문 전개부)' 부근에 다음 문구를 반드시 포함하세요: \"{must_phrase}\"\n"
            if "bot" in must_pos:
                must_include_inject += f"- 글의 '하단 (마무리부)' 부근에 다음 문구를 반드시 포함하세요: \"{must_phrase}\"\n"

        import datetime
        
        prompt_additions = ""
        if advanced_format:
            prompt_additions = """
[고급 서식 규칙 - 매우 중요]
- 옵션, 장단점, 나열 등 목록이 필요한 경우 반드시 `- `(동그라미) 또는 `1. `(숫자) 마크다운 리스트 형태로 작성하세요.
- 여러 모델, 가격, 트림 등을 비교 분석할 때는 반드시 [표] 와 [/표] 태그 사이에 마크다운 표 형식으로 작성하세요. 표는 반드시 3x3 이하 크기여야 합니다.

[표 작성 예시]
[표]
| 비교항목 | A 방식 | B 방식 |
| 초기비용 | 부담 없음 | 전액 현금 |
| 유지보수 | 수리비 면제 | 발생 시 자가부담 |
[/표]
"""

        prompt = f"""
{persona_desc}
{biz_inject}
{keyword_inject}
{car_model_inject}
{must_include_inject}
{prompt_additions}

아래 팩트를 기반으로 완전히 새로운 한국어 블로그 포스팅을 작성하세요.

[요청된 글 분량]
{post_length}
🚨 [절대 엄수 지침] 
- 위 요청된 글 분량(글자 수)을 **정확하게** 맞춰야 합니다. 
- 분량 하한선 미만으로 너무 짧게 대충 쓰거나, 반대로 상한선을 넘어 TMI로 너무 길게 쓰면 무조건 실패 처리됩니다.
- 본문을 다 작성한 후, 머릿속으로 글자 수를 세어보고 부족하면 부연 설명을 더 넣고, 넘치면 과감히 쳐내서 무조건 저 분량대를 맞추세요.

[팩트 데이터]
{facts}

[발행일 기준 정보]
오늘 날짜: {datetime.datetime.now().strftime('%Y. %m. %d.')}
내일/모레 중 가장 조회수/트래픽 타겟팅이 좋은 최적의 1개 시간대(00분/30분 단위)를 계산하세요.

[글 구조 — 반드시 준수]
{selected_structure}

[품질 체크리스트]
* 원문 어휘 90% 이상 새로운 표현으로 대체
* 1인칭 실제 경험 문장 2개 이상 자연스럽게 삽입
3. 구체적 수치 (월 납입금·보증금 비율·약정 기간·초과 주행 요금 등) 반드시 포함
4. 문단 및 가독성 규칙 (매우 중요!): 한 문단은 무조건 1~2문장으로 짧게 치고 넘어가세요. 자주 엔터(\\n)를 쳐서 본문의 호흡을 짧게 가져가야 합니다. 절대 글을 빽빽하게 붙여 쓰면 안 됩니다! 시원시원하게 띄어 쓰세요.
5. 중간중간 핵심 강조 문장은 markdown 인용구(> ) 문법으로 작성하세요. (예: > 장기렌트, 지금이 제일 저렴합니다.)
6. 총 글자 수: 🚨 **지정된 [{post_length}] 기준을 완벽하게 맞출 것.** (너무 길지도, 짧지도 않게!)
7. 글 내에 절대 마크다운 헤딩 기호(## 등)를 사용하지 마세요. 소제목이 필요하다면 그냥 일반 텍스트로 자연스럽게 강조 없이 쓰세요.

[AI 느낌 완전 제거 요령 - 말투 튜닝 규칙]
- '~입니다/습니다'는 거의 쓰지 말고, '~에요', '~거든요', '~더라고요', '~죠', '~네요' 같은 구어체, 1인칭 후기 말투를 적극 사용하세요.
- AI 특유의 기계적인 나열(첫째, 둘째, 셋째 / 장점은 다음과 같습니다)은 무조건 금지입니다.
- 전문가가 쓴 딱딱한 글 흉내보다, 최근에 직접 계약하고 차 받은 오너가 친한 친구나 카페 회원들에게 남기는 솔직한(심지어 약간 필터링 없는) 말투로 써주세요.
- "다양한~", "최적의~", "효과적인~", "결론적으로" 등 영혼 없는 형용사/부사 절대 금지. 짧고 명확하게!

[출력 형식 — JSON만, 다른 텍스트 절대 포함 금지]
{{
  "title": "최종 선택된 제목 (25~35자, C-Rank + 클릭율 최적화)",
  "title_candidates": [
    "후보1 - 공식1(숫자+결과) 기반",
    "후보2 - 공식2-7 중 하나 기반",
    "후보3 - 공식2-7 중 또 다른 하나 기반"
  ],
  "content": "본문 전체 (단락 구분 \\n, 마크다운 기호 금지)",
  "cta_text": "글 마지막에 삽입될 자연스러운 행동 유도(CTA) 문장 1~2개",
  "optimal_publish_time": "추천 예약 발행 시간 (형식: YYYY. MM. DD. HH:MM) - 오늘부터 모레 사이 한정",
  "seo_tags": ["태그1", "태그2", "태그3"], // 최소 25개 이상 필수! 연관 SEO 태그를 벤치마킹 타겟과 본문 기반으로 직접 생성하세요
  "persona_used": "{selected_key}",
  "content_type": "{persona_label}"
"""
        # 구조:
        result = self.generate(prompt, persona_type=resolved_type)
        if result:
            return clean_generated_content(result)
        return None

    def generate_cta(self, topic: str, persona_type: str = "conversion") -> str:
        """
        글 마무리에 삽입할 맞춤형 CTA 문구 생성.
        persona_type: "exposure" (공유·저장·재방문 유도) / "conversion" (상담 문의 유도)
        """
        if persona_type == "exposure":
            styles = ["다음 편 시리즈 예고형", "질문 댓글 유도형", "저장·공유 요청형", "관련 키워드 연결형"]
        else:
            styles = ["신뢰 기반 상담 연결형", "역설적 솔직 유도형", "케이스 확인 제안형", "이달 한정 긴급형"]

        style = random.choice(styles)
        prompt = f"""
주제: '{topic}' / CTA 스타일: {style} / 타입: {persona_type}

위 블로그 글 마지막에 들어갈 CTA 문구를 작성하세요.
- 한국어, 2~3문장
- 자연스럽게 행동 유도 (광고처럼 보이면 안 됨)
- 이모티콘 최대 2개
- 출력: CTA 텍스트만 (따옴표나 JSON 등 서식 없이 순수 텍스트만 출력)
"""
        result = self.generate(prompt, persona_type=persona_type)
        if result:
            result = result.replace("```json", "").replace("```", "").strip()
            # 만약 {"cta": "..."} 형태로 응답했다면 파싱 시도
            if result.startswith("{") and result.endswith("}"):
                try:
                    import json
                    parsed = json.loads(result)
                    if "cta" in parsed:
                        result = parsed["cta"]
                except: pass
            return result.strip()
        return f"'{topic}'에 대해 궁금한 점은 댓글로 남겨주세요 😊"

    def get_best_publish_time(self, keyword: str) -> str:
        """발행 최적 시간 추천 — flash 경량 모델로 빠르게 처리"""
        import datetime
        now = datetime.datetime.now()
        tomorrow_str = (now + datetime.timedelta(days=1)).strftime("%Y. %m. %d.")
        dayafter_str = (now + datetime.timedelta(days=2)).strftime("%Y. %m. %d.")

        prompt = (
            f"키워드: '{keyword}'\n"
            f"이 키워드 타겟 독자가 가장 많이 클릭하는 네이버 블로그 발행 시간 1개를 골라줘.\n"
            f"오늘~모레({dayafter_str}) 범위 안에서, 분은 00 또는 30분이어야 해.\n"
            f"설명 없이 날짜+시간만 출력. 예시: 2026. 03. 01. 18:30"
        )
        try:
            # 🚀 flash 경량 모델로 직접 호출 (main 모델보다 10배 빠름)
            flash_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={"temperature": 0.3, "max_output_tokens": 64},
            )
            resp = flash_model.generate_content([prompt])
            result = resp.text.strip() if resp.text else ""
            if len(result) >= 15 and "." in result and ":" in result:
                return result
        except Exception as e:
            print(f"   ⚠️ [AI-Time] flash 질의 실패, fallback 사용: {e}")
        return tomorrow_str + " 18:00"

    def list_personas(self) -> None:
        """사용 가능한 전체 페르소나 목록 출력"""
        for k in ALL_PERSONAS:
            print(f"   - {k}")
        print()


def diagnose_low_quality_risk(text: str) -> dict:
    """
    생성된 글의 저품질/AI 탐지 위험 간단 진단 (자동 검증기)
    Returns: {"risk_level": "LOW"/"MID"/"HIGH", "issues": [...]}
    """
    issues = []
    
    # 1. 글 길이 체크 (너무 짧으면 저품질 위험)
    if len(text) < 800: 
        issues.append("글 길이 부족 (800자 미만)")
    
    # 2. "~입니다/습니다" 비율 체크 (종결어미 중 너무 많으면 AI 의심)
    imnida_count = text.count("니다.") + text.count("습니다.") + text.count("입니다.")
    total_sentences = text.count(".")
    if total_sentences > 0:
        imnida_ratio = imnida_count / total_sentences
        if imnida_ratio > 0.6: 
            issues.append(f"AI 탐지 위험: '니다'체 비율 너무 높음 ({imnida_ratio:.1f})")
            
    # 3. 덩어리 문단 체크 (줄바꿈 없이 너무 긴 문단)
    paragraphs = text.split("\n\n")
    long_paragraphs = sum(1 for p in paragraphs if p.count(".") > 6)
    if long_paragraphs > 1:
        issues.append("가독성 낮음: 6문장 이상 덩어리 문단 존재")

    # 4. "출처 입력" 메타 정보 체크 (치명적)
    if "출처 입력" in text or "출처:" in text or "AI 분석 리포트" in text:
        issues.append("🔴 치명적: AI 메타 정보 '출처 입력/출처/AI리포트' 발견")

    risk_level = "LOW"
    if len(issues) >= 3 or any("🔴" in i for i in issues): risk_level = "HIGH"
    elif len(issues) >= 1: risk_level = "MID"
        
    return {
        "risk_level": risk_level,
        "issues": issues
    }

# Singleton
client = GeminiClient()