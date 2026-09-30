from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator
import os

load_dotenv()

TIDB_URL = os.getenv("TIDB_URL")

engine = create_engine(
    TIDB_URL,
    connect_args={
        "ssl": {
            "ca": os.path.join(os.path.dirname(__file__), "..", "isrgrootx1.pem")
        }
    },
    pool_recycle=1800,   # 30분마다 커넥션 갱신 (TiDB 기본 wait_timeout 대비)
    pool_pre_ping=True,  # 쿼리 전 커넥션 유효성 확인 후 자동 재연결
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성 주입용 DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """모든 테이블 생성 (앱 시작 시 호출)"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("모든 테이블 생성 완료!")


def run_migrations():
    """기존 테이블에 누락된 컬럼을 추가하는 마이그레이션"""
    migrations = [
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50) NOT NULL DEFAULT 'checking'",
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'",
        # reports: reported_account → account_number 리네임 및 bank_name, account_holder 추가
        "ALTER TABLE reports CHANGE COLUMN IF EXISTS reported_account account_number VARCHAR(30) NOT NULL",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS bank_name VARCHAR(50) NOT NULL DEFAULT ''",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS account_holder VARCHAR(100)",
        # blacklist: bank_name, account_holder 추가
        "ALTER TABLE blacklist ADD COLUMN IF NOT EXISTS bank_name VARCHAR(50) NOT NULL DEFAULT ''",
        "ALTER TABLE blacklist ADD COLUMN IF NOT EXISTS account_holder VARCHAR(100)",
        # users: role 컬럼 추가
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'",
        # accounts: balance BigInteger → DECIMAL(15,2) 변환
        "ALTER TABLE accounts MODIFY COLUMN balance DECIMAL(15, 2) NOT NULL DEFAULT 0",
        # guardians: VARCHAR 임시 변환 → 대문자 통일 → ENUM 재정의 (REJECTED 추가)
        "ALTER TABLE guardians MODIFY COLUMN approval_status VARCHAR(50) NOT NULL",
        "UPDATE guardians SET approval_status = UPPER(approval_status)",
        "ALTER TABLE guardians MODIFY COLUMN approval_status ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING'",
        # reports: VARCHAR 임시 변환 → 대문자 통일 → ENUM 재정의 (REJECTED, WITHDRAWN 추가)
        "ALTER TABLE reports MODIFY COLUMN status VARCHAR(50) NOT NULL",
        "UPDATE reports SET status = UPPER(status)",
        "ALTER TABLE reports MODIFY COLUMN status ENUM('PENDING','REVIEWED','RESOLVED','REJECTED','WITHDRAWN') NOT NULL DEFAULT 'PENDING'",
        # notifications: ENUM 확장 (3단계)
        # SQLAlchemy는 Python enum의 NAME(대문자)을 DB에 저장 → 대문자 ENUM 유지
        # ENUM 컬럼은 허용값 외 UPDATE 불가 → VARCHAR 임시 변환 후 재정의
        "ALTER TABLE notifications MODIFY COLUMN notification_type VARCHAR(50) NOT NULL",
        "UPDATE notifications SET notification_type = UPPER(notification_type)",
        (
            "ALTER TABLE notifications MODIFY COLUMN notification_type "
            "ENUM('RISK_ALERT','GUARDIAN_REQUEST','GUARDIAN_APPROVED','REPORT_UPDATE',"
            "'BLACKLIST_HIT','TRANSFER_SENT','TRANSFER_RECEIVED','SYSTEM') NOT NULL"
        ),
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                print(f"Migration skipped ({e})")
    print("마이그레이션 완료!")


def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("TiDB 연결 성공!")
    except Exception as e:
        print(f"TiDB 연결 실패: {e}")

if __name__ == "__main__":
    test_connection()
