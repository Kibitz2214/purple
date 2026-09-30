from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, Text, ForeignKey
from typing import Optional, TYPE_CHECKING
from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.transaction import Transaction


class RiskScore(Base, TimestampMixin):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), unique=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)           # 0.0 ~ 100.0
    risk_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # 위험 사유 (XAI 근거)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # GPT 분석 전문

    # relationship
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="risk_score")
