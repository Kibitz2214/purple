from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, ForeignKey, Enum
from typing import Optional, TYPE_CHECKING
from models.base import Base, TimestampMixin
import enum

if TYPE_CHECKING:
    from models.account import Account
    from models.risk_score import RiskScore


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"       # 처리 중
    COMPLETED = "completed"   # 완료
    BLOCKED = "blocked"       # 차단 (위험도 초과)
    FLAGGED = "flagged"       # 의심 플래그


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    receiver_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    memo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # relationships
    sender_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[sender_account_id], back_populates="sent_transactions"
    )
    receiver_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[receiver_account_id], back_populates="received_transactions"
    )
    risk_score: Mapped[Optional["RiskScore"]] = relationship("RiskScore", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
