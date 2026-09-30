from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User
    from models.transaction import Transaction


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    bank_name: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)  # 단위: 원
    
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 계좌 별칭 (예: 주거래 통장)
    account_type: Mapped[str] = mapped_column(String(50), default="checking", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    sent_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.sender_account_id", back_populates="sender_account",
        cascade="all, delete-orphan"
    )
    received_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.receiver_account_id", back_populates="receiver_account",
        cascade="all"
    )
