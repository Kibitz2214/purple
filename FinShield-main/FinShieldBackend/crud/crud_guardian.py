from sqlalchemy.orm import Session
from models.guardian import Guardian, ApprovalStatus
from schemas.guardian import GuardianCreate, GuardianUpdate
from sqlalchemy import select, and_, or_

def create_guardian_request(db: Session, user_id: int, guardian_id: int):
    # 이미 존재하는 관계 확인
    existing = db.execute(
        select(Guardian).where(
            and_(
                Guardian.user_id == user_id,
                Guardian.guardian_id == guardian_id
            )
        )
    ).scalar_one_or_none()
    
    if existing:
        return existing
        
    db_guardian = Guardian(
        user_id=user_id,
        guardian_id=guardian_id,
        approval_status=ApprovalStatus.PENDING
    )
    db.add(db_guardian)
    db.commit()
    db.refresh(db_guardian)
    return db_guardian

def get_guardians_for_user(db: Session, user_id: int):
    """피보호자(본인) 기준의 승인된 보호자 목록"""
    query = select(Guardian).where(
        and_(
            Guardian.user_id == user_id,
            Guardian.approval_status == ApprovalStatus.APPROVED
        )
    )
    return db.execute(query).scalars().all()

def get_approved_guardians_for_user(db: Session, user_id: int):
    """승인된 보호자 목록만 조회"""
    query = select(Guardian).where(
        and_(
            Guardian.user_id == user_id,
            Guardian.approval_status == ApprovalStatus.APPROVED
        )
    )
    return db.execute(query).scalars().all()

def get_wards_for_guardian(db: Session, guardian_id: int):
    """보호자(본인) 기준의 승인된 피보호자 목록"""
    query = select(Guardian).where(
        and_(
            Guardian.guardian_id == guardian_id,
            Guardian.approval_status == ApprovalStatus.APPROVED
        )
    )
    return db.execute(query).scalars().all()

def get_pending_for_guardian(db: Session, guardian_id: int):
    """내가 보호자로서 받은 승인 대기 요청 목록"""
    query = select(Guardian).where(
        and_(
            Guardian.guardian_id == guardian_id,
            Guardian.approval_status == ApprovalStatus.PENDING
        )
    )
    return db.execute(query).scalars().all()

def update_guardian_status(db: Session, guardian_link_id: int, new_status: ApprovalStatus):
    db_guardian = db.get(Guardian, guardian_link_id)
    if db_guardian:
        db_guardian.approval_status = new_status
        db.commit()
        db.refresh(db_guardian)
    return db_guardian

def delete_guardian_relation(db: Session, guardian_link_id: int):
    db_guardian = db.get(Guardian, guardian_link_id)
    if db_guardian:
        db.delete(db_guardian)
        db.commit()
        return True
    return False

def get_guardian_relation(db: Session, guardian_link_id: int):
    return db.get(Guardian, guardian_link_id)
