from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from models.blacklist import Blacklist


def _normalize(account_number: str) -> str:
    return account_number.replace("-", "").strip()


def get_blacklist_by_account_number(db: Session, account_number: str) -> Optional[Blacklist]:
    stmt = select(Blacklist).where(Blacklist.account_number == _normalize(account_number))
    return db.execute(stmt).scalar_one_or_none()


def create_blacklist_entry(
    db: Session,
    account_number: str,
    bank_name: str,
    reason: str,
    report_count: int = 0,
    account_holder: Optional[str] = None,
) -> Optional[Blacklist]:
    """블랙리스트 등록. 동시 요청으로 중복 INSERT 발생 시 None 반환."""
    try:
        entry = Blacklist(
            account_number=_normalize(account_number),
            bank_name=bank_name,
            account_holder=account_holder,
            reason=reason,
            report_count=report_count,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except IntegrityError:
        db.rollback()
        return None  # 이미 등록된 계좌 (race condition)
