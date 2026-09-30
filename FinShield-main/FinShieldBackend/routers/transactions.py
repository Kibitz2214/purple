from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.ai_client import FraudResponse, call_ai_server, save_risk_score
from core.deps import get_current_user, get_non_blacklisted_user
from crud import crud_transaction, crud_account, crud_notification, crud_guardian, crud_blacklist
from database.tidb import get_db
from models.transaction import TransactionStatus as ModelTransactionStatus
from models.user import User, UserRole
from schemas.notification import NotificationCreate, NotificationType
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionStatus

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_non_blacklisted_user)
):
    """
    계좌 이체를 수행합니다.
    1. 보내는 계좌가 본인 소유인지 확인
    2. 잔액 확인
    3. 이체 처리 (DB 트랜잭션)
    """
    # 1. 보내는 계좌 권한 확인
    sender_account = crud_account.get_account_by_id(db, transaction_in.sender_account_id)
    if not sender_account:
        raise HTTPException(status_code=404, detail="보내는 계좌를 찾을 수 없습니다.")
    if sender_account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="보내는 계좌에 대한 권한이 없습니다.")

    # 냉각기 확인 (최근 10분 내 차단/검토 이력)
    if crud_transaction.check_cooldown(db, sender_account.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="보안 냉각 기간입니다. 10분 후 다시 시도해 주세요.",
        )

    # 2. 블랙리스트 확인
    if crud_blacklist.get_blacklist_by_account_number(db, transaction_in.receiver_account_number):
        # 송금자 본인 알림
        crud_notification.create_notification(db, NotificationCreate(
            user_id=current_user.id,
            notification_type=NotificationType.BLACKLIST_HIT,
            title="송금 차단",
            content=f"사기 의심 계좌({transaction_in.receiver_account_number})로의 송금이 차단되었습니다.",
        ))
        # 보호자 알림
        guardians = crud_guardian.get_approved_guardians_for_user(db, current_user.id)
        for guardian_rel in guardians:
            crud_notification.create_notification(db, NotificationCreate(
                user_id=guardian_rel.guardian_id,
                notification_type=NotificationType.BLACKLIST_HIT,
                title="사기 의심 계좌 송금 시도",
                content=f"{current_user.name}님이 사기 의심 계좌({transaction_in.receiver_account_number})로 송금을 시도했습니다.",
            ))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 계좌는 사기 의심 계좌입니다. 송금이 차단되었습니다.",
        )

    # 3. 계좌번호로 받는 계좌 조회
    receiver_account = crud_account.get_account_by_number(db, transaction_in.receiver_account_number)
    if not receiver_account:
        raise HTTPException(status_code=404, detail="받는 계좌를 찾을 수 없습니다.")
    if receiver_account.id == sender_account.id:
        raise HTTPException(status_code=400, detail="보내는 계좌와 받는 계좌가 동일합니다.")

    # 4. 잔액 확인
    if sender_account.balance < transaction_in.amount:
        raise HTTPException(status_code=400, detail="잔액이 부족합니다.")

    # 5. 거래 기록 생성 (receiver_account_id를 조회된 ID로 주입)
    db_transaction = crud_transaction.create_transaction(db, transaction_in, receiver_account.id)

    # 6. 실제 이체 처리 (Balance 업데이트)
    success = crud_transaction.process_transfer(db, db_transaction)
    
    if not success:
        raise HTTPException(status_code=500, detail="이체 처리 중 오류가 발생했습니다.")

    # 송금 완료 알림 생성
    amount_str = f"{int(transaction_in.amount):,}"
    crud_notification.create_notification(db, NotificationCreate(
        user_id=current_user.id,
        notification_type=NotificationType.TRANSFER_SENT,
        title="송금 완료",
        content=f"{amount_str}원을 {transaction_in.receiver_account_number}로 송금했습니다.",
    ))
    crud_notification.create_notification(db, NotificationCreate(
        user_id=receiver_account.user_id,
        notification_type=NotificationType.TRANSFER_RECEIVED,
        title="입금 완료",
        content=f"{amount_str}원이 입금됐습니다.",
    ))

    # 피보호자의 승인된 보호자에게 알림 생성
    guardians = crud_guardian.get_approved_guardians_for_user(db, current_user.id)
    for guardian_rel in guardians:
        crud_notification.create_notification(db, NotificationCreate(
            user_id=guardian_rel.guardian_id,
            notification_type=NotificationType.SYSTEM,
            title="피보호자 송금 알림",
            content=f"{current_user.name}님이 {amount_str}원을 {transaction_in.receiver_account_number}로 송금했습니다.",
        ))

    # 베이스라인 업데이트 (MongoDB, 실패해도 송금 정상 처리)
    try:
        from crud.crud_user_behavior import update_baseline
        update_baseline(
            user_id=current_user.id,
            amount=float(db_transaction.amount),
            hour_of_day=db_transaction.created_at.hour,
            day_of_week=db_transaction.created_at.weekday(),
            receiver_account=receiver_account.account_number,
            tx_date=db_transaction.created_at,
        )
    except Exception:
        pass

    # AI 사기 분석 (실패해도 송금 정상 처리)
    try:
        ai_result = call_ai_server(db, db_transaction, False)
        if ai_result:
            save_risk_score(db, db_transaction.id, ai_result)
            rec = ai_result.recommendation
            prob_pct = int(ai_result.fraud_probability * 100)

            if rec == "warn":
                crud_notification.create_notification(db, NotificationCreate(
                    user_id=current_user.id,
                    notification_type=NotificationType.RISK_ALERT,
                    title="송금 위험 경고",
                    content=f"AI 분석 결과 이번 송금({amount_str}원)에서 사기 위험 신호가 감지되었습니다. (위험도: {prob_pct}%)",
                ))

            elif rec == "guardian_approval":
                crud_transaction.update_transaction_status(db, db_transaction, ModelTransactionStatus.FLAGGED)
                crud_notification.create_notification(db, NotificationCreate(
                    user_id=current_user.id,
                    notification_type=NotificationType.RISK_ALERT,
                    title="송금 검토 중",
                    content=f"AI 분석 결과 이번 송금({amount_str}원)이 의심 거래로 분류되어 보호자 확인이 필요합니다. (위험도: {prob_pct}%)",
                ))
                for guardian_rel in guardians:
                    crud_notification.create_notification(db, NotificationCreate(
                        user_id=guardian_rel.guardian_id,
                        notification_type=NotificationType.GUARDIAN_REQUEST,
                        title="피보호자 의심 송금 감지",
                        content=f"{current_user.name}님이 {amount_str}원을 {transaction_in.receiver_account_number}로 송금했습니다. AI가 의심 거래로 판단했습니다. (위험도: {prob_pct}%)",
                    ))

            elif rec == "block":
                crud_transaction.update_transaction_status(db, db_transaction, ModelTransactionStatus.BLOCKED)
                crud_notification.create_notification(db, NotificationCreate(
                    user_id=current_user.id,
                    notification_type=NotificationType.RISK_ALERT,
                    title="고위험 송금 차단",
                    content=f"AI 분석 결과 이번 송금({amount_str}원)이 고위험 거래로 차단되었습니다. (위험도: {prob_pct}%)",
                ))
                for guardian_rel in guardians:
                    crud_notification.create_notification(db, NotificationCreate(
                        user_id=guardian_rel.guardian_id,
                        notification_type=NotificationType.RISK_ALERT,
                        title="피보호자 고위험 송금 감지",
                        content=f"{current_user.name}님의 송금({amount_str}원, {transaction_in.receiver_account_number})이 고위험으로 차단되었습니다. (위험도: {prob_pct}%)",
                    ))
    except Exception:
        pass

    return db_transaction


@router.get("/me", response_model=List[TransactionResponse])
def list_my_transactions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """현재 사용자의 모든 거래 내역을 조회합니다."""
    return crud_transaction.get_user_transactions(db, current_user.id, skip=skip, limit=limit)


@router.get("/account/{account_id}", response_model=List[TransactionResponse])
def list_account_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 계좌의 거래 내역을 조회합니다 (본인 계좌만 가능)."""
    db_account = crud_account.get_account_by_id(db, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다.")
    if db_account.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="이 계좌의 내역을 조회할 권한이 없습니다.")
    
    return crud_transaction.get_account_transactions(db, account_id, skip=skip, limit=limit)


@router.patch("/{transaction_id}/cancel", response_model=TransactionResponse)
def cancel_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """송금을 취소합니다. PENDING 상태인 본인 거래만 취소 가능합니다."""
    db_transaction = crud_transaction.get_transaction(db, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="거래 내역을 찾을 수 없습니다.")

    sender_account = crud_account.get_account_by_id(db, db_transaction.sender_account_id)
    if not sender_account or sender_account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 거래를 취소할 권한이 없습니다.")

    if db_transaction.status != TransactionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"PENDING 상태인 거래만 취소할 수 있습니다. (현재: {db_transaction.status})")

    return crud_transaction.cancel_transaction(db, db_transaction)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_detail(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 거래의 상세 정보를 조회합니다."""
    db_transaction = crud_transaction.get_transaction(db, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="거래 내역을 찾을 수 없습니다.")
    
    # 본인이 보냈거나 받은 거래인지 확인 (관리자 포함)
    if current_user.role != UserRole.ADMIN:
        sender_account = crud_account.get_account_by_id(db, db_transaction.sender_account_id)
        receiver_account = crud_account.get_account_by_id(db, db_transaction.receiver_account_id)
        can_access = (
            (sender_account and sender_account.user_id == current_user.id)
            or (receiver_account and receiver_account.user_id == current_user.id)
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="이 거래 내역에 대한 접근 권한이 없습니다.")
        
    return db_transaction
