from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
from schemas.mongo_base import MongoBase


class ConversationLog(MongoBase):
    """
    conversation_logs 컬렉션
    GPT-4.1-mini XAI 위험 분석 요청/응답 전체 내역
    설명 가능한 AI(XAI) 근거 추적 및 감사 로그
    """
    transaction_id: int                      # transactions.id FK
    user_id: int                             # 분석 요청 대상 사용자
    prompt: str                              # GPT에 전달한 프롬프트 전문
    response: str                            # GPT 응답 전문
    risk_score: float                        # 해당 분석의 위험 점수
    risk_summary: Optional[str] = None      # 위험 요약 (한 줄)
    model: str = "gpt-4.1-mini"             # 사용 모델
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[int] = None        # 응답 소요 시간 (ms)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationLogCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    transaction_id: int
    user_id: int
    prompt: str
    response: str
    risk_score: float
    risk_summary: Optional[str] = None
    model: str = "gpt-4.1-mini"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
