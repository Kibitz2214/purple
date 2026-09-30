from sqlalchemy.orm import Session
from typing import List, Optional
from models.report import Report, ReportStatus
from schemas.report import ReportCreate, ReportUpdate


def _normalize(account_number: str) -> str:
    return account_number.replace("-", "").strip()


def create_report(db: Session, report_in: ReportCreate, reporter_id: int) -> Report:
    db_report = Report(
        reporter_id=reporter_id,
        account_number=_normalize(report_in.account_number),
        bank_name=report_in.bank_name,
        account_holder=report_in.account_holder,
        content=report_in.content,
        status=ReportStatus.PENDING
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def count_active_reports_by_account(db: Session, account_number: str) -> int:
    """WITHDRAWN·REJECTED 제외한 해당 계좌의 유효 신고 수"""
    normalized = _normalize(account_number)
    return (
        db.query(Report)
        .filter(
            Report.account_number == normalized,
            Report.status.notin_([ReportStatus.WITHDRAWN, ReportStatus.REJECTED]),
        )
        .count()
    )


def get_all_reports(db: Session, skip: int = 0, limit: int = 100) -> List[Report]:
    return db.query(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).first()


def get_user_reports(db: Session, reporter_id: int, skip: int = 0, limit: int = 100) -> List[Report]:
    return db.query(Report).filter(Report.reporter_id == reporter_id).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def update_report(db: Session, db_report: Report, report_in: ReportUpdate) -> Report:
    update_data = report_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def delete_report(db: Session, report_id: int) -> bool:
    db_report = get_report(db, report_id)
    if db_report:
        db.delete(db_report)
        db.commit()
        return True
    return False


def withdraw_report(db: Session, db_report: Report) -> bool:
    """PENDING 상태인 신고만 철회 가능 (WITHDRAWN 상태로 변경)"""
    if db_report.status == ReportStatus.PENDING:
        db_report.status = ReportStatus.WITHDRAWN
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return True
    return False
