from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Optional
from models.transaction import Transaction, TransactionStatus
from schemas.transaction import TransactionCreate
from crud.crud_account import update_account_balance, get_account_by_id


def create_transaction(db: Session, transaction_in: TransactionCreate, receiver_account_id: int) -> Transaction:
    db_transaction = Transaction(
        sender_account_id=transaction_in.sender_account_id,
        receiver_account_id=receiver_account_id,
        amount=transaction_in.amount,
        memo=transaction_in.memo,
        status=TransactionStatus.PENDING
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def process_transfer(db: Session, db_transaction: Transaction) -> bool:
    """
    실제 계좌 간 이체 처리를 수행합니다.
    트랜잭션 안전성을 위해 DB 세션 관리가 중요합니다.
    """
    try:
        sender_account = get_account_by_id(db, db_transaction.sender_account_id)
        receiver_account = get_account_by_id(db, db_transaction.receiver_account_id)
        
        if not sender_account or not receiver_account:
            return False
            
        if sender_account.balance < db_transaction.amount:
            # 잔액 부족 시 거래 상태 업데이트 후 실패 반환
            db_transaction.status = TransactionStatus.BLOCKED
            db.commit()
            return False

        # 1. 출금 처리
        sender_account.balance -= int(db_transaction.amount)
        db.add(sender_account)
        
        # 2. 입금 처리
        receiver_account.balance += int(db_transaction.amount)
        db.add(receiver_account)
        
        # 3. 거래 상태 업데이트
        db_transaction.status = TransactionStatus.COMPLETED
        
        db.commit()
        db.refresh(db_transaction)
        return True
    except Exception:
        db.rollback()
        return False


def cancel_transaction(db: Session, db_transaction: Transaction) -> Transaction:
    """PENDING 상태인 거래를 취소합니다."""
    db_transaction.status = TransactionStatus.CANCELLED
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_account_transactions(db: Session, account_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """해당 계좌와 관련된 모든 거래 내역(송금/입금)을 조회합니다."""
    return db.query(Transaction).filter(
        (Transaction.sender_account_id == account_id) | 
        (Transaction.receiver_account_id == account_id)
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()


def check_cooldown(db: Session, sender_account_id: int, minutes: int = 10) -> bool:
    """최근 N분 내 BLOCKED/FLAGGED 거래가 있으면 True 반환 (냉각기 중)."""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == sender_account_id,
            Transaction.status.in_([TransactionStatus.BLOCKED, TransactionStatus.FLAGGED]),
            Transaction.created_at >= cutoff,
        )
        .first()
        is not None
    )


def update_transaction_status(
    db: Session, db_transaction: Transaction, new_status: TransactionStatus
) -> Transaction:
    db_transaction.status = new_status
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_user_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """사용자의 모든 계좌에서 발생한 거래 내역을 조회합니다."""
    from models.account import Account
    return db.query(Transaction).join(
        Account, 
        (Transaction.sender_account_id == Account.id) | (Transaction.receiver_account_id == Account.id)
    ).filter(Account.user_id == user_id).distinct().order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
