from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.deps import get_current_user
from crud import crud_blacklist, crud_notification, crud_report
from database.tidb import get_db
from models.user import User, UserRole
from schemas.notification import NotificationCreate, NotificationType
from schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

AUTO_BLACKLIST_THRESHOLD = 5


def _check_and_auto_blacklist(db: Session, report_in: ReportCreate) -> None:
    """신고 누적 기준 초과 시 블랙리스트 자동 등록 + 관리자 알림.

    중복 방지 2중 구조:
      1차(앱): 등록 전 이미 존재하는지 조회 → 있으면 즉시 반환
      2차(DB): create_blacklist_entry 내 IntegrityError 처리 → None 반환 시 알림 생략
    """
    # 1차 방지: 앱 레이어 — 이미 블랙리스트에 있으면 즉시 종료
    if crud_blacklist.get_blacklist_by_account_number(db, report_in.account_number):
        return

    count = crud_report.count_active_reports_by_account(db, report_in.account_number)
    if count < AUTO_BLACKLIST_THRESHOLD:
        return

    # 2차 방지: DB 레이어 — 동시 요청으로 IntegrityError 발생 시 None 반환
    entry = crud_blacklist.create_blacklist_entry(
        db,
        account_number=report_in.account_number,
        bank_name=report_in.bank_name,
        account_holder=report_in.account_holder,
        reason=f"자동등록: 신고 누적 {count}회",
        report_count=count,
    )
    if entry is None:
        return  # 동시 요청으로 이미 등록됨 — 알림 중복 발송 방지

    admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
    for admin in admins:
        crud_notification.create_notification(db, NotificationCreate(
            user_id=admin.id,
            notification_type=NotificationType.SYSTEM,
            title="블랙리스트 자동 등록",
            content=(
                f"계좌 {report_in.account_number} ({report_in.bank_name})이(가) "
                f"신고 누적 {count}회로 블랙리스트에 자동 등록되었습니다."
            ),
        ))


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_fraud_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사기 거래를 신고합니다. 신고 누적 5회 이상 시 블랙리스트에 자동 등록됩니다."""
    db_report = crud_report.create_report(db, report_in, current_user.id)
    _check_and_auto_blacklist(db, report_in)
    return db_report


@router.get("/", response_model=List[ReportResponse])
def list_my_reports(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """자신의 신고 내역 목록을 조회합니다."""
    return crud_report.get_user_reports(db, current_user.id, skip=skip, limit=limit)


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """신고 상세 정보 및 처리 결과를 조회합니다."""
    db_report = crud_report.get_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="신고 내역을 찾을 수 없습니다.")
    if db_report.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 신고 내역에 대한 접근 권한이 없습니다.")
    return db_report


@router.delete("/{report_id}")
def withdraw_fraud_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """신고를 철회합니다. (대기 중인 신고만 철회 가능)"""
    db_report = crud_report.get_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="신고 내역을 찾을 수 없습니다.")
    if db_report.reporter_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 신고 내역에 대한 삭제 권한이 없습니다.")

    success = crud_report.withdraw_report(db, db_report)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="이미 검토 중이거나 처리가 완료된 신고는 철회할 수 없습니다."
        )
    return {"detail": "신고가 성공적으로 철회되었습니다."}
