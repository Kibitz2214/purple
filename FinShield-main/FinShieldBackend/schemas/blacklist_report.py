from pydantic import Field
from datetime import datetime, timezone
from typing import Optional, List
from schemas.mongo_base import MongoBase


class Attachment(MongoBase):
    """신고 첨부파일 정보"""
    file_name: str
    file_type: str           # image / pdf / audio 등
    file_url: str            # 저장 경로 또는 S3 URL
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BlacklistReport(MongoBase):
    """
    blacklist_reports 컬렉션
    사용자 신고 원본 데이터 (TiDB reports + blacklist 연동)
    AI 재학습 및 블랙리스트 등록 검토 원본 보관
    """
    report_id: int                               # reports.id FK
    reporter_id: int                             # 신고자 user_id
    reported_account: str                        # 신고 대상 계좌번호
    raw_content: str                             # 원본 신고 내용 전문
    attachments: List[Attachment] = Field(default_factory=list)   # 첨부파일 목록
    ai_analysis: Optional[str] = None           # GPT 신고 내용 분석 결과
    fraud_pattern_matched: Optional[str] = None # 매칭된 사기 패턴 유형
    is_processed: bool = False                   # 블랙리스트 등록 처리 여부
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BlacklistReportCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    report_id: int
    reporter_id: int
    reported_account: str
    raw_content: str
    attachments: List[Attachment] = Field(default_factory=list)
    ai_analysis: Optional[str] = None
    fraud_pattern_matched: Optional[str] = None
    is_processed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
