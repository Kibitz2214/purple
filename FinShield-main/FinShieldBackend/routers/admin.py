from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_admin
from crud import crud_user, crud_report, crud_notification, crud_account, crud_transaction
from models.user import User
from models.blacklist import Blacklist
from schemas.account import AccountUpdate, AccountResponse
from schemas.notification import NotificationCreate, NotificationResponse, NotificationType, AdminBroadcastRequest
from schemas.report import ReportUpdate, ReportResponse
from schemas.transaction import TransactionResponse
from schemas.user import UserResponse, UserUpdate
from schemas.blacklist import BlacklistResponse
from sqlalchemy import select

router = APIRouter(prefix="/admin", tags=["admin"])


# ── 사용자 관리 ──────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """전체 사용자 목록 조회 (관리자 전용)"""
    return crud_user.get_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserResponse)
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """특정 사용자 상세 조회 (관리자 전용)"""
    db_user = crud_user.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return db_user


@router.patch("/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """회원 정보 수정 (관리자 전용)"""
    db_user = crud_user.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return crud_user.update_user(db, db_user, user_data)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def force_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """사용자 강제 탈퇴 (관리자 전용)"""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="자기 자신은 탈퇴시킬 수 없습니다.")
    db_user = crud_user.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    crud_user.delete_user(db, db_user)


# ── 계좌 관리 ─────────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/accounts", response_model=List[AccountResponse])
def admin_list_user_accounts(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """특정 사용자의 계좌 목록 조회 (관리자 전용)"""
    if not crud_user.get_user_by_id(db, user_id):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return crud_account.get_user_accounts(db, user_id)


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
def admin_update_account(
    account_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """계좌 정보 수정 (관리자 전용)"""
    db_account = crud_account.get_account_by_id(db, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다.")
    return crud_account.update_account(db, db_account, account_in)


# ── 거래 내역 관리 ────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/transactions", response_model=List[TransactionResponse])
def admin_list_user_transactions(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """특정 사용자의 거래 내역 조회 (관리자 전용)"""
    if not crud_user.get_user_by_id(db, user_id):
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return crud_transaction.get_user_transactions(db, user_id, skip=skip, limit=limit)


# ── 신고 관리 ─────────────────────────────────────────────────────────────────

@router.get("/reports", response_model=List[ReportResponse])
def list_all_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """전체 신고 목록 조회 (관리자 전용)"""
    return crud_report.get_all_reports(db, skip=skip, limit=limit)


@router.patch("/reports/{report_id}", response_model=ReportResponse)
def update_report_status(
    report_id: int,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """신고 처리 상태 변경 (관리자 전용)"""
    db_report = crud_report.get_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="신고 내역을 찾을 수 없습니다.")
    return crud_report.update_report(db, db_report, report_in)


# ── 블랙리스트 관리 ───────────────────────────────────────────────────────────

@router.get("/blacklist", response_model=List[BlacklistResponse])
def list_all_blacklist(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """블랙리스트 전체 조회 (관리자 전용)"""
    return db.execute(select(Blacklist).offset(skip).limit(limit)).scalars().all()


# ── 알림 공지 ─────────────────────────────────────────────────────────────────

@router.post("/notifications", response_model=List[NotificationResponse], status_code=status.HTTP_201_CREATED)
def broadcast_notification(
    body: AdminBroadcastRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """전체 사용자에게 공지 알림 발송 (관리자 전용)"""
    users = crud_user.get_users(db, skip=0, limit=10000)
    created = []
    for user in users:
        notification = crud_notification.create_notification(db, NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM,
            title=body.title,
            content=body.content,
        ))
        created.append(notification)
    return created
