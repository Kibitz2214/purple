import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:8001")


class FraudRequest(BaseModel):
    transaction_id: int
    amount: float
    sender_account_id: int
    receiver_account_id: int
    hour_of_day: int
    day_of_week: int
    is_blacklisted: bool
    sender_tx_count_7d: int
    sender_avg_amount_30d: float


class FraudResponse(BaseModel):
    transaction_id: int
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    top_reasons: List[str]
    recommendation: str


def _build_request(db: Session, tx, is_blacklisted: bool) -> FraudRequest:
    from models.account import Account
    from models.transaction import Transaction

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    tx_count_7d = (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == tx.sender_account_id,
            Transaction.created_at >= week_ago,
        )
        .count()
    )

    recent_txs = (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == tx.sender_account_id,
            Transaction.created_at >= month_ago,
        )
        .all()
    )
    avg_amount_30d = (
        sum(float(t.amount) for t in recent_txs) / len(recent_txs)
        if recent_txs
        else 0.0
    )

    # 30일 데이터가 없는 신규 유저 → MongoDB 베이스라인 전체 평균으로 fallback
    if avg_amount_30d == 0.0:
        try:
            from crud.crud_user_behavior import get_baseline_avg_amount
            sender_account = db.query(Account).filter(
                Account.id == tx.sender_account_id
            ).first()
            if sender_account:
                avg_amount_30d = get_baseline_avg_amount(sender_account.user_id)
        except Exception:
            pass

    return FraudRequest(
        transaction_id=tx.id,
        amount=float(tx.amount),
        sender_account_id=tx.sender_account_id,
        receiver_account_id=tx.receiver_account_id,
        hour_of_day=tx.created_at.hour,
        day_of_week=tx.created_at.weekday(),
        is_blacklisted=is_blacklisted,
        sender_tx_count_7d=tx_count_7d,
        sender_avg_amount_30d=avg_amount_30d,
    )


def call_ai_server(db: Session, tx, is_blacklisted: bool) -> Optional[FraudResponse]:
    """AI 서버에 사기 예측 요청. 실패 시 None 반환 (AI 오류로 송금 차단 금지)."""
    try:
        payload = _build_request(db, tx, is_blacklisted)
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{AI_SERVER_URL}/predict/fraud",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return FraudResponse(**resp.json())
    except Exception:
        return None


def save_risk_score(db: Session, tx_id: int, result: FraudResponse) -> None:
    from models.risk_score import RiskScore

    data = json.dumps(result.model_dump(), ensure_ascii=False)
    reasons = ", ".join(result.top_reasons)

    existing = db.query(RiskScore).filter(RiskScore.transaction_id == tx_id).first()
    if existing:
        existing.score = result.fraud_probability * 100
        existing.risk_reason = reasons
        existing.ai_analysis = data
    else:
        db.add(
            RiskScore(
                transaction_id=tx_id,
                score=result.fraud_probability * 100,
                risk_reason=reasons,
                ai_analysis=data,
            )
        )
    db.commit()
