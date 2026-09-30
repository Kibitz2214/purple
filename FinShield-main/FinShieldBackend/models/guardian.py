from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Enum
from typing import TYPE_CHECKING
from models.base import Base, TimestampMixin
import enum

if TYPE_CHECKING:
    from models.user import User


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"     # 승인 대기
    APPROVED = "approved"   # 승인 완료
    REJECTED = "rejected"   # 거절


class Guardian(Base, TimestampMixin):
    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)       # 피보호자
    guardian_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)   # 보호자
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="guardian_links")
    guardian: Mapped["User"] = relationship("User", foreign_keys=[guardian_id], back_populates="ward_links")
