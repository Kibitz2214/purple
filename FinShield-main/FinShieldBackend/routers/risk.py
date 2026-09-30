import json
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.ai_client import AI_SERVER_URL, FraudResponse, call_ai_server, save_risk_score
from core.deps import get_current_user, get_db
from crud import crud_blacklist
from models.account import Account
from models.notification import Notification, NotificationType as ModelNotificationType
from models.risk_score import RiskScore
from models.transaction import Transaction, TransactionStatus
from models.user import User

router = APIRouter(prefix="/risk", tags=["risk"])


class AnalyzeRequest(BaseModel):
    transaction_id: int


@router.post("/analyze", response_model=FraudResponse)
def analyze_risk(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == body.transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="거래 내역을 찾을 수 없습니다.")

    receiver = db.query(Account).filter(Account.id == tx.receiver_account_id).first()
    is_blacklisted = (
        crud_blacklist.get_blacklist_by_account_number(db, receiver.account_number) is not None
        if receiver
        else False
    )

    result = call_ai_server(db, tx, is_blacklisted)
    if result is None:
        raise HTTPException(status_code=502, detail="AI 서버 호출에 실패했습니다.")

    save_risk_score(db, tx.id, result)
    return result


class UserRiskRequest(BaseModel):
    user_id: int
    total_tx_count: int
    avg_amount: float
    max_amount: float
    fraud_flag_count: int
    blacklist_hit_count: int
    account_age_days: int


class UserRiskResponse(BaseModel):
    risk_score: float
    trust_score: float
    risk_grade: str
    top_reasons: List[str]


@router.post("/user/{user_id}", response_model=UserRiskResponse)
def analyze_user_risk(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 사용자 계좌 목록
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    if not accounts:
        raise HTTPException(status_code=404, detail="해당 사용자의 계좌 정보가 없습니다.")

    account_ids = [a.id for a in accounts]

    # 2. 계좌 나이 (가장 오래된 계좌 기준, 일수)
    oldest_created = min(a.created_at for a in accounts)
    now = datetime.now(timezone.utc)
    if oldest_created.tzinfo is None:
        oldest_created = oldest_created.replace(tzinfo=timezone.utc)
    account_age_days = (now - oldest_created).days

    # 3. 송금 거래 통계
    txs = (
        db.query(Transaction)
        .filter(Transaction.sender_account_id.in_(account_ids))
        .all()
    )
    total_tx_count = len(txs)
    amounts = [float(t.amount) for t in txs]
    avg_amount = sum(amounts) / len(amounts) if amounts else 0.0
    max_amount = max(amounts) if amounts else 0.0

    # 4. 사기 플래그 거래 수 (FLAGGED + BLOCKED)
    fraud_flag_count = sum(
        1 for t in txs
        if t.status in (TransactionStatus.FLAGGED, TransactionStatus.BLOCKED)
    )

    # 5. 블랙리스트 히트 수 (BLACKLIST_HIT 알림 기준)
    blacklist_hit_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.notification_type == ModelNotificationType.BLACKLIST_HIT,
        )
        .count()
    )

    # 6. AI 서버 POST /predict/risk-score 호출
    payload = UserRiskRequest(
        user_id=user_id,
        total_tx_count=total_tx_count,
        avg_amount=avg_amount,
        max_amount=max_amount,
        fraud_flag_count=fraud_flag_count,
        blacklist_hit_count=blacklist_hit_count,
        account_age_days=account_age_days,
    )

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{AI_SERVER_URL}/predict/risk-score",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return UserRiskResponse(**resp.json())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 서버 호출에 실패했습니다: {e}")


@router.get("/{transaction_id}", response_model=FraudResponse)
def get_risk_score(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk = db.query(RiskScore).filter(RiskScore.transaction_id == transaction_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="해당 거래의 위험도 분석 결과가 없습니다.")

    try:
        return FraudResponse(**json.loads(risk.ai_analysis))
    except Exception:
        raise HTTPException(status_code=500, detail="저장된 분석 결과를 불러올 수 없습니다.")
