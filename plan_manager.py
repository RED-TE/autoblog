# -*- coding: utf-8 -*-
# plan_manager.py
# 라이선스 등급별 기능 관리자 (Lite vs Pro)

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

class PlanLevel(Enum):
    LITE = "LITE"       # 도구 (Tool)
    PRO = "PRO"         # 시스템 (System)
    MASTER = "MASTER"   # 설비 (Infrastructure)
    AGENCY = "AGENCY"   # 대행사 (Unlimited)

@dataclass
class PlanFeatures:
    level: PlanLevel
    name: str
    max_accounts: int
    allow_auto_publish: bool      # 자동 발행 여부 (Lite도 True)
    allow_advanced_strategy: bool # 노출/전환 분리 전략 (Pro 이상)
    allow_human_behavior: bool    # 사람 흉내 (예열/검수) (Pro 이상)
    allow_all_personas: bool      # 전체 페르소나 사용 (Pro 이상)
    allow_advanced_image: bool    # 이미지 정밀 가공 (Pro 이상)
    max_content_length: int       # [NEW] 본문 글자수 제한 (Lite: 1700자)
    description: str
    allow_auto_mode: bool = False # [NEW] AI 자동 모드 사용 가능 여부 (Pro 이상)
    is_trial: bool = False        # [NEW] 1회 무료 체험 여부

# ==========================================
# [설정] 등급별 기능 정의
# ==========================================
FEATURES = {
    PlanLevel.LITE: PlanFeatures(
        level=PlanLevel.LITE,
        name="라이트(도구)",
        max_accounts=2,                # [CHANGE] 라이트는 2개로 제한
        allow_auto_publish=True,       # 자동 발행 OK
        allow_advanced_strategy=False, # 전략 분리 X (단순 믹스)
        allow_human_behavior=False,    # 기계적 즉시 실행 (Fast)
        allow_all_personas=False,      # 기본 10종 제한
        allow_advanced_image=False,    # 단순 리사이즈
        max_content_length=1700,       # 1700자 미만
        description="빠른 실행, 기본 기능 (최대 2계정)",
        allow_auto_mode=False         # AI 자동 모드 불가
    ),
    PlanLevel.PRO: PlanFeatures(
        level=PlanLevel.PRO,
        name="프로(시스템)",
        max_accounts=8,
        allow_auto_publish=True,
        allow_advanced_strategy=True,  # 노출/전환 완벽 분리
        allow_human_behavior=True,     # 사람 흉내 (예열/지연)
        allow_all_personas=True,       # 60종 + 커스텀 전체
        allow_advanced_image=True,     # 텍스트 합성 + 이미지 링크 삽입
        max_content_length=5000,       # 넉넉하게
        description="네이버 로직 최적화, 자동 스케줄링 (최대 8계정)",
        allow_auto_mode=True          # AI 자동 모드 가능
    ),
    # Master, Agency는 추후 확장 (우선 Pro 상위 호환)
    PlanLevel.MASTER: PlanFeatures(
        level=PlanLevel.MASTER,
        name="마스터(수익설비)",
        max_accounts=20,
        allow_auto_publish=True,
        allow_advanced_strategy=True,
        allow_human_behavior=True,
        allow_all_personas=True,
        allow_advanced_image=True,
        max_content_length=10000,
        description="다계정 대량 운영 (20계정)",
        allow_auto_mode=True
    ),
    PlanLevel.AGENCY: PlanFeatures(
        level=PlanLevel.AGENCY,
        name="에이전시(무제한)",
        max_accounts=999,
        allow_auto_publish=True,
        allow_advanced_strategy=True,
        allow_human_behavior=True,
        allow_all_personas=True,
        allow_advanced_image=True,
        max_content_length=10000,
        description="무제한 대행사 플랜",
        allow_auto_mode=True
    )
}

def get_plan_from_key(license_key: str) -> PlanFeatures:
    """
    라이선스 키 Prefix를 분석하여 해당 플랜의 기능을 반환
    Default: PRO (기존 사용자 호환성 위함, 또는 LITE로 보수적 잡을 수도 있음)
    """
    if not license_key:
        return FEATURES[PlanLevel.LITE] # 키 없으면 최하위

    key_upper = license_key.upper().strip()
    
    # [SECURITY] 더 이상 테스트 키 및 자동 Fallback을 허용하지 않음
    if key_upper.startswith("LGT-"):
        return FEATURES[PlanLevel.LITE]
    elif key_upper.startswith("PRO-"):
        return FEATURES[PlanLevel.PRO]
    elif key_upper.startswith("MST-"):
        return FEATURES[PlanLevel.MASTER]
    elif key_upper.startswith("AGC-"):
        return FEATURES[PlanLevel.AGENCY]
    
    return None # Default Fallback (Block)

def get_plan_from_name(plan_name: str) -> PlanFeatures:
    """
    Firestore에서 읽어온 plan 문자열(lite, pro, master)을 객체로 변환
    """
    if not plan_name: return None
    
    p = plan_name.lower().strip()
    if p == "lite": return FEATURES[PlanLevel.LITE]
    if p == "pro": return FEATURES[PlanLevel.PRO]
    if p == "master": return FEATURES[PlanLevel.MASTER]
    if p == "agency": return FEATURES[PlanLevel.AGENCY]
    
    return None # 'free' 또는 알 수 없는 등급은 차단하도록 None 반환
