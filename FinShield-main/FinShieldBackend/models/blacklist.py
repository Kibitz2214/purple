from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, func
from typing import Optional
from models.base import Base, TimestampMixin


class Blacklist(Base, TimestampMixin):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    bank_name: Mapped[str] = mapped_column(String(50), nullable=False)
    account_holder: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)           # 등록 사유
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)   # 신고 횟수
    registered_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False             # 최초 블랙리스트 등록일
    )
