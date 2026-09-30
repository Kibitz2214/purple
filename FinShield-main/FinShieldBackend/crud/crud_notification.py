from sqlalchemy.orm import Session
from sqlalchemy import select, update
from datetime import datetime
from typing import List, Optional

from models.notification import Notification, NotificationType
from schemas.notification import NotificationCreate, NotificationUpdate
from database.mongodb import Collections

def create_notification(db: Session, obj_in: NotificationCreate):
    """MySQL에 알림 생성"""
    db_obj = Notification(
        user_id=obj_in.user_id,
        notification_type=obj_in.notification_type,
        title=obj_in.title,
        content=obj_in.content,
        is_read=False
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

async def log_notification_to_mongo(user_id: int, notification_type: str, title: str, content: str, status: str = "sent"):
    """MongoDB에 알림 발송 이력 로그 저장 (비동기)"""
    log_data = {
        "user_id": user_id,
        "notification_type": notification_type,
        "title": title,
        "content": content,
        "sent_at": datetime.utcnow(),
        "status": status  # sent, failed, etc.
    }
    await Collections.notification_logs.insert_one(log_data)

def get_notifications_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None
):
    """사용자의 알림 목록 조회. is_read=True: 읽은 것만, False: 안 읽은 것만, None: 전체"""
    query = select(Notification).where(Notification.user_id == user_id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    return db.execute(query).scalars().all()

def update_notification(db: Session, notification_id: int, obj_in: NotificationUpdate):
    """알림 상태 업데이트 (읽음 처리)"""
    db_obj = db.get(Notification, notification_id)
    if db_obj:
        if obj_in.is_read is not None:
            db_obj.is_read = obj_in.is_read
        db.commit()
        db.refresh(db_obj)
    return db_obj

def mark_all_as_read(db: Session, user_id: int):
    """모든 알림 읽음 처리"""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    db.execute(stmt)
    db.commit()
    return True

def delete_notification(db: Session, notification_id: int):
    """알림 삭제"""
    db_obj = db.get(Notification, notification_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
        return True
    return False

def get_notification(db: Session, notification_id: int):
    """단일 알림 조회"""
    return db.get(Notification, notification_id)
