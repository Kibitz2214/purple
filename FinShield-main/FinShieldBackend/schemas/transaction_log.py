from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, List
from schemas.mongo_base import MongoBase


class RiskDetail(MongoBase):
    """위험 분석 세부 항목"""
    factor: str                # 위험 요소 이름 (예: 블랙리스트 계좌, 비정상 시간대 등)
    score: float               # 해당 요소 기여 점수
    description: str           # 설명


class TransactionLog(MongoBase):
    """
    transaction_logs 컬렉션
    거래별 상세 로그 (TiDB transactions 테이블과 연동)
    AI 분석 결과 및 위험 세부 내역 저장
    """
    transaction_id: int                          # transactions.id FK
    sender_id: int                               # 송금자 user_id
    sender_account: str                          # 송금 계좌번호
    receiver_account: str                        # 수신 계좌번호
    amount: float
    risk_score: float = 0.0                      # 최종 위험 점수 (0~100)
    risk_details: List[RiskDetail] = Field(default_factory=list)  # 위험 요소 세부 내역
    is_blacklisted: bool = False                 # 블랙리스트 계좌 여부
    is_flagged: bool = False                     # 이상 거래 플래그
    raw_request: Optional[dict] = None          # 원본 요청 데이터
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransactionLogCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    transaction_id: int
    sender_id: int
    sender_account: str
    receiver_account: str
    amount: float
    risk_score: float = 0.0
    risk_details: List[RiskDetail] = Field(default_factory=list)
    is_blacklisted: bool = False
    is_flagged: bool = False
    raw_request: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
