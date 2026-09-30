from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, Boolean, ForeignKey, Enum
from typing import TYPE_CHECKING
from models.base import Base, TimestampMixin
import enum

if TYPE_CHECKING:
    from models.user import User


class NotificationType(str, enum.Enum):
    RISK_ALERT = "risk_alert"               # 위험 거래 경고
    GUARDIAN_REQUEST = "guardian_request"   # 보호자 승인 요청
    GUARDIAN_APPROVED = "guardian_approved" # 보호자 승인 완료
    REPORT_UPDATE = "report_update"         # 신고 처리 결과
    BLACKLIST_HIT = "blacklist_hit"         # 블랙리스트 계좌 탐지
    TRANSFER_SENT = "transfer_sent"         # 송금 완료 (보내는 사람)
    TRANSFER_RECEIVED = "transfer_received" # 입금 완료 (받는 사람)
    SYSTEM = "system"                       # 시스템 공지


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)   # 수신자
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationship
    user: Mapped["User"] = relationship("User", back_populates="notifications")
