from pydantic import Field
from datetime import datetime, timezone
from typing import List, Optional
from schemas.mongo_base import MongoBase


class FraudPattern(MongoBase):
    """
    fraud_patterns 컬렉션
    AI 학습에 사용되는 사기 유형 패턴 데이터
    신고 데이터 → AI 재학습 선순환 구조의 핵심
    """
    pattern_type: str                        # voice_phishing / smishing / used_trade / romance_scam 등
    name: str                                # 패턴 이름 (예: 기관사칭 보이스피싱)
    description: str                         # 패턴 상세 설명
    indicators: List[str] = Field(default_factory=list)   # 위험 지표 목록
    keywords: List[str] = Field(default_factory=list)     # 연관 키워드
    weight: float = 1.0                      # 위험 가중치 (높을수록 위험)
    is_active: bool = True                   # 활성화 여부
    source: Optional[str] = None            # 출처 (경찰청, 금감원, 사용자신고 등)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FraudPatternCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    pattern_type: str
    name: str
    description: str
    indicators: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    weight: float = 1.0
    is_active: bool = True
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
