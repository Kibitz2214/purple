from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    RISK_ALERT = "risk_alert"               # 위험 거래 경고
    GUARDIAN_REQUEST = "guardian_request"   # 보호자 승인 요청
    GUARDIAN_APPROVED = "guardian_approved" # 보호자 승인 완료
    REPORT_UPDATE = "report_update"         # 신고 처리 결과
    BLACKLIST_HIT = "blacklist_hit"         # 블랙리스트 계좌 탐지
    TRANSFER_SENT = "transfer_sent"         # 송금 완료 (보내는 사람)
    TRANSFER_RECEIVED = "transfer_received" # 입금 완료 (받는 사람)
    SYSTEM = "system"                       # 시스템 공지

class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str
    content: str

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminBroadcastRequest(BaseModel):
    title: str
    content: str
