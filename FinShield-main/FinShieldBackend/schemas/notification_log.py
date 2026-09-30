from pydantic import Field
from datetime import datetime, timezone
from typing import Optional
from schemas.mongo_base import MongoBase


class NotificationLog(MongoBase):
    """
    notification_logs 컬렉션
    알림 발송 이력 (채널별 전송 상태 추적)
    TiDB notifications 테이블과 연동하여 발송 원본 데이터 보관
    """
    notification_id: int                     # notifications.id FK
    user_id: int                             # 수신자 user_id
    channel: str                             # push / sms / email
    title: str
    content: str
    status: str = "sent"                     # sent / delivered / failed
    error_message: Optional[str] = None     # 실패 시 오류 내용
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None  # 수신 확인 시각


class NotificationLogCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    notification_id: int
    user_id: int
    channel: str
    title: str
    content: str
    status: str = "sent"
    error_message: Optional[str] = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None
