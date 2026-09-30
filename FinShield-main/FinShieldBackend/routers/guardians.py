from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.deps import get_db, get_current_user
from models.user import User
from models.guardian import ApprovalStatus
from schemas.guardian import (
    GuardianCreate,
    GuardianResponse,
    GuardianRelationInfo,
    GuardianUserDetail
)
from crud import crud_guardian

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.post("/request", response_model=GuardianResponse)
async def request_guardian(
    guardian_in: GuardianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자가 다른 사용자에게 보호자 등록을 요청합니다.
    """
    if current_user.id == guardian_in.guardian_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신을 보호자로 등록할 수 없습니다."
        )
    
    # 보호자 대상 사용자가 존재하는지 확인
    target_user = db.query(User).filter(User.id == guardian_in.guardian_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다."
        )

    return crud_guardian.create_guardian_request(
        db=db, 
        user_id=current_user.id, 
        guardian_id=guardian_in.guardian_id
    )


@router.get("/my-guardians", response_model=List[GuardianRelationInfo])
async def list_my_guardians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 보호자 목록을 조회합니다.
    """
    relations = crud_guardian.get_guardians_for_user(db, current_user.id)
    result = []
    for rel in relations:
        rel_info = GuardianRelationInfo.model_validate(rel)
        # 보호자 정보 추가
        rel_info.guardian_info = GuardianUserDetail(
            id=rel.guardian.id,
            username=rel.guardian.name,
            phone=rel.guardian.phone or ""
        )
        result.append(rel_info)
    return result


@router.get("/my-wards", response_model=List[GuardianRelationInfo])
async def list_my_wards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자가 보호하고 있는 피보호자 목록을 조회합니다.
    """
    relations = crud_guardian.get_wards_for_guardian(db, current_user.id)
    result = []
    for rel in relations:
        rel_info = GuardianRelationInfo.model_validate(rel)
        # 피보호자 정보 추가
        rel_info.user_info = GuardianUserDetail(
            id=rel.user.id,
            username=rel.user.name,
            phone=rel.user.phone or ""
        )
        result.append(rel_info)
    return result


@router.get("/pending", response_model=List[GuardianRelationInfo])
async def list_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """내가 보호자로서 받은 승인 대기 요청 목록을 조회합니다."""
    relations = crud_guardian.get_pending_for_guardian(db, current_user.id)
    result = []
    for rel in relations:
        rel_info = GuardianRelationInfo.model_validate(rel)
        rel_info.user_info = GuardianUserDetail(
            id=rel.user.id,
            username=rel.user.name,
            phone=rel.user.phone or ""
        )
        result.append(rel_info)
    return result


@router.patch("/{guardian_link_id}/approve", response_model=GuardianResponse)
async def approve_guardian(
    guardian_link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보호자 요청을 승인합니다. (보호자만 수행 가능)"""
    relation = crud_guardian.get_guardian_relation(db, guardian_link_id)
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="보호자 관계를 찾을 수 없습니다.")
    if relation.guardian_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="해당 요청을 승인할 권한이 없습니다.")
    if relation.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="대기 중인 요청만 승인할 수 있습니다.")

    return crud_guardian.update_guardian_status(db, guardian_link_id, ApprovalStatus.APPROVED)


@router.patch("/{guardian_link_id}/reject", response_model=GuardianResponse)
async def reject_guardian(
    guardian_link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보호자 요청을 거절합니다. (보호자만 수행 가능)"""
    relation = crud_guardian.get_guardian_relation(db, guardian_link_id)
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="보호자 관계를 찾을 수 없습니다.")
    if relation.guardian_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="해당 요청을 거절할 권한이 없습니다.")
    if relation.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="대기 중인 요청만 거절할 수 있습니다.")

    return crud_guardian.update_guardian_status(db, guardian_link_id, ApprovalStatus.REJECTED)


@router.delete("/{guardian_link_id}")
async def remove_relation(
    guardian_link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    보호자 관계를 삭제합니다. (피보호자 또는 보호자만 수행 가능)
    """
    relation = crud_guardian.get_guardian_relation(db, guardian_link_id)
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="보호자 관계를 찾을 수 없습니다."
        )
    
    if relation.user_id != current_user.id and relation.guardian_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관계를 삭제할 권한이 없습니다."
        )
    
    crud_guardian.delete_guardian_relation(db, guardian_link_id)
    return {"message": "보호자 관계가 성공적으로 삭제되었습니다."}
