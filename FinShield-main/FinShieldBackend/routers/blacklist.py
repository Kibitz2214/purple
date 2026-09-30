from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from core.deps import get_current_user, get_current_admin
from database.tidb import get_db
from models.blacklist import Blacklist
from models.user import User
from schemas.blacklist import (
    BlacklistCreate,
    BlacklistUpdate,
    BlacklistResponse,
    BlacklistCheckResponse,
)

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


def _normalize(account_number: str) -> str:
    return account_number.replace("-", "").strip()


@router.get("/", response_model=List[BlacklistResponse], summary="블랙리스트 목록 조회")
def list_blacklist(db: Session = Depends(get_db)):
    """전체 블랙리스트 계좌 목록을 조회합니다."""
    stmt = select(Blacklist)
    result = db.execute(stmt).scalars().all()
    return result


@router.get("/check/{account_number}", response_model=BlacklistCheckResponse, summary="계좌 블랙리스트 여부 확인")
def check_blacklist(account_number: str, db: Session = Depends(get_db)):
    """특정 계좌번호가 블랙리스트에 등록되어 있는지 확인합니다."""
    stmt = select(Blacklist).where(Blacklist.account_number == _normalize(account_number))
    blacklist_entry = db.execute(stmt).scalar_one_or_none()

    if blacklist_entry:
        return {
            "is_blacklisted": True,
            "reason": blacklist_entry.reason,
            "registered_at": blacklist_entry.registered_at,
        }
    return {"is_blacklisted": False}


@router.post("/", response_model=BlacklistResponse, status_code=status.HTTP_201_CREATED, summary="블랙리스트 등록")
def register_blacklist(body: BlacklistCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """새로운 계좌를 블랙리스트에 등록합니다."""
    normalized = _normalize(body.account_number)
    stmt = select(Blacklist).where(Blacklist.account_number == normalized)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 블랙리스트에 등록된 계좌번호입니다.",
        )

    new_entry = Blacklist(
        account_number=normalized,
        bank_name=body.bank_name,
        account_holder=body.account_holder,
        reason=body.reason,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@router.put("/{blacklist_id}", response_model=BlacklistResponse, summary="블랙리스트 정보 수정")
def update_blacklist(
    blacklist_id: int, body: BlacklistUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    """블랙리스트 등록 사유나 신고 횟수 등을 수정합니다."""
    stmt = select(Blacklist).where(Blacklist.id == blacklist_id)
    blacklist_entry = db.execute(stmt).scalar_one_or_none()

    if not blacklist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 ID의 블랙리스트 정보를 찾을 수 없습니다.",
        )

    if body.reason is not None:
        blacklist_entry.reason = body.reason
    if body.report_count is not None:
        blacklist_entry.report_count = body.report_count

    db.commit()
    db.refresh(blacklist_entry)
    return blacklist_entry


@router.delete("/{blacklist_id}", status_code=status.HTTP_204_NO_CONTENT, summary="블랙리스트 삭제")
def delete_blacklist(blacklist_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """블랙리스트에서 해당 계좌 정보를 삭제(해제)합니다."""
    stmt = select(Blacklist).where(Blacklist.id == blacklist_id)
    blacklist_entry = db.execute(stmt).scalar_one_or_none()

    if not blacklist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 ID의 블랙리스트 정보를 찾을 수 없습니다.",
        )

    db.delete(blacklist_entry)
    db.commit()
    return None
