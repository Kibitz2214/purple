from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.deps import get_current_user, get_non_blacklisted_user
from crud import crud_account
from database.tidb import get_db
from models.user import User, UserRole
from schemas.account import AccountCreate, AccountUpdate, AccountResponse

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_non_blacklisted_user)
):
    """현재 로그인한 유저의 새 계좌를 등록합니다."""
    if crud_account.get_account_by_number(db, account_in.account_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 계좌번호입니다."
        )
    return crud_account.create_user_account(db, account_in, current_user.id)


@router.get("/", response_model=List[AccountResponse])
def list_my_accounts(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """현재 로그인한 유저의 모든 계좌 목록을 조회합니다."""
    return crud_account.get_user_accounts(db, current_user.id, skip=skip, limit=limit)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 계좌의 상세 정보를 조회합니다 (본인 계좌만 가능)."""
    db_account = crud_account.get_account_by_id(db, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다.")
    if db_account.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="이 계좌에 대한 접근 권한이 없습니다.")
    return db_account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account_info(
    account_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """계좌 정보를 수정합니다 (별칭 등, 본인 계좌 또는 관리자)."""
    db_account = crud_account.get_account_by_id(db, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다.")
    if db_account.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="이 계좌에 대한 수정 권한이 없습니다.")
    return crud_account.update_account(db, db_account, account_in)


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """계좌를 삭제합니다 (본인 계좌만 가능)."""
    db_account = crud_account.get_account_by_id(db, account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다.")
    if db_account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 계좌에 대한 삭제 권한이 없습니다.")

    crud_account.delete_account(db, account_id)
    return {"detail": "계좌가 성공적으로 삭제되었습니다."}
