from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, ForeignKey, Enum
from typing import Optional, TYPE_CHECKING
from models.base import Base, TimestampMixin
import enum

if TYPE_CHECKING:
    from models.user import User


class ReportStatus(str, enum.Enum):
    PENDING = "pending"       # 접수 대기
    REVIEWED = "reviewed"     # 검토 중
    RESOLVED = "resolved"     # 처리 완료
    REJECTED = "rejected"     # 신고 반려
    WITHDRAWN = "withdrawn"   # 사용자 신고 철회


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False)      # 신고 대상 계좌번호
    bank_name: Mapped[str] = mapped_column(String(50), nullable=False)          # 은행명
    account_holder: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 예금주 이름
    content: Mapped[str] = mapped_column(Text, nullable=False)                  # 신고 내용
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False
    )
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # 관리자 처리 메모

    # relationship
    reporter: Mapped["User"] = relationship("User", back_populates="reports")
