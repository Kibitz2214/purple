from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.deps import get_db, get_current_user, get_current_admin
from models.user import User
from schemas.notification import (
    NotificationResponse, 
    NotificationUpdate, 
    NotificationCreate
)
from crud import crud_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def list_my_notifications(
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 알림 목록을 조회합니다.
    - is_read=false: 읽지 않은 알림만
    - is_read=true: 읽은 알림만
    - 파라미터 없음: 전체 조회
    """
    return crud_notification.get_notifications_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_read=is_read
    )


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification_status(
    notification_id: int,
    update_in: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    알림의 읽음 상태를 변경합니다. (주로 읽음 처리용)
    """
    notification = crud_notification.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다."
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="알림 상태를 변경할 권한이 없습니다."
        )
    
    return crud_notification.update_notification(db, notification_id, update_in)


@router.post("/mark-all-read")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 모든 미확인 알림을 읽음 처리합니다.
    """
    crud_notification.mark_all_as_read(db, current_user.id)
    return {"message": "모든 알림이 읽음 처리되었습니다."}


@router.delete("/{notification_id}")
async def remove_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    알림을 삭제합니다.
    """
    notification = crud_notification.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다."
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="알림을 삭제할 권한이 없습니다."
        )
    
    crud_notification.delete_notification(db, notification_id)
    return {"message": "알림이 성공적으로 삭제되었습니다."}


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_system_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    새로운 알림을 생성하고 발송 이력을 기록합니다. (시스템/관리자용)
    """
    # 1. MySQL(TiDB)에 알림 데이터 저장
    new_notification = crud_notification.create_notification(db, notification_in)
    
    # 2. MongoDB Atlas에 발송 이력 로그 저장 (비동기 처리 가능)
    await crud_notification.log_notification_to_mongo(
        user_id=notification_in.user_id,
        notification_type=notification_in.notification_type,
        title=notification_in.title,
        content=notification_in.content,
        status="sent"
    )
    
    return new_notification
