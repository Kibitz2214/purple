# FinShield 백엔드

## 기술 스택
- **언어**: Python 3.12
- **프레임워크**: FastAPI 0.135.3
- **정형 DB**: TiDB Cloud (MySQL 호환, SQLAlchemy 2.0 + PyMySQL 1.1)
- **비정형 DB**: MongoDB Atlas (motor 3.7 + pymongo 4.16)
- **AI 분석**: OpenAI GPT-4.1-mini (XAI 위험 분석, 미구현)
- **서버**: AWS EC2 (t2.micro)

## 폴더 구조
```
FinShieldBackend/
├── .env                  # 환경변수 (깃 제외)
├── .gitignore
├── isrgrootx1.pem        # TiDB CA 인증서 (깃 제외)
├── requirements.txt
├── main.py               # FastAPI 진입점, 라우터 등록
├── core/
│   └── deps.py           # JWT 생성·검증, get_current_user / get_current_admin / get_non_blacklisted_user / get_db 의존성
├── crud/
│   ├── crud_account.py
│   ├── crud_blacklist.py
│   ├── crud_guardian.py
│   ├── crud_notification.py
│   ├── crud_report.py
│   ├── crud_transaction.py
│   └── crud_user.py
├── database/
│   ├── tidb.py           # TiDB 연결, 커넥션 풀, 마이그레이션, get_db
│   └── mongodb.py        # MongoDB 연결
├── models/               # SQLAlchemy 테이블 모델 (TiDB)
│   ├── base.py           # Base, TimestampMixin
│   ├── user.py           # User (users)
│   ├── account.py        # Account (accounts)
│   ├── transaction.py    # Transaction, TransactionStatus Enum
│   ├── guardian.py       # Guardian, ApprovalStatus Enum
│   ├── notification.py   # Notification, NotificationType Enum
│   ├── blacklist.py      # Blacklist (blacklist)
│   ├── report.py         # Report, ReportStatus Enum
│   ├── risk_score.py     # RiskScore (risk_scores)
│   └── admin.py
├── routers/              # API 엔드포인트
│   ├── auth.py
│   ├── users.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── guardians.py
│   ├── notifications.py
│   ├── blacklist.py
│   ├── reports.py
│   ├── risk.py
│   └── admin.py
└── schemas/              # Pydantic 스키마 (요청/응답 및 MongoDB 문서)
    ├── auth.py
    ├── user.py
    ├── account.py
    ├── transaction.py
    ├── guardian.py
    ├── notification.py
    ├── blacklist.py
    ├── report.py
    ├── mongo_base.py
    ├── blacklist_report.py
    ├── conversation_log.py
    ├── fraud_pattern.py
    ├── notification_log.py
    ├── transaction_log.py
    └── user_behavior_log.py
```

## MySQL 테이블 (TiDB) — models/
users, accounts, transactions, risk_scores,
guardians, blacklist, reports, notifications

## MongoDB 컬렉션 — schemas/
user_behavior_logs, transaction_logs, fraud_patterns,
conversation_logs, notification_logs, blacklist_reports

## Pydantic 스키마 — schemas/
- auth.py              : RegisterRequest, LoginRequest, TokenResponse
- user.py              : UserRole Enum, UserResponse, UserUpdate
- account.py           : AccountCreate, AccountUpdate, AccountResponse, AccountBalanceUpdate
- transaction.py       : TransactionStatus Enum, TransactionCreate, AccountBrief, TransactionResponse
- guardian.py          : ApprovalStatus Enum, GuardianCreate, GuardianResponse, GuardianUserDetail, GuardianRelationInfo
- blacklist.py         : BlacklistCreate, BlacklistUpdate, BlacklistResponse, BlacklistCheckResponse
- report.py            : ReportStatus Enum, ReportCreate, ReportUpdate, ReportResponse
- notification.py      : NotificationType Enum, NotificationCreate, NotificationUpdate, NotificationResponse, AdminBroadcastRequest
- blacklist_report.py  : 블랙리스트 신고 (MongoDB)
- conversation_log.py  : AI 대화 로그 (MongoDB)
- fraud_pattern.py     : 사기 패턴 (MongoDB)
- notification_log.py  : 알림 로그 (MongoDB)
- transaction_log.py   : 거래 로그 (MongoDB)
- user_behavior_log.py : 사용자 행동 로그 (MongoDB)
- mongo_base.py        : MongoDB 문서 베이스 클래스

## 환경변수 (.env)
```
TIDB_URL=mysql+pymysql://유저:비밀번호@호스트:4000/DB이름?ssl_ca=isrgrootx1.pem
MONGO_URI=mongodb+srv://...
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=...
JWT_EXPIRE_MINUTES=60
```

## 개발 시작
```bash
venv\Scripts\activate
uvicorn main:app --reload
```

## API 문서
서버 실행 후 http://localhost:8000/docs

## API 엔드포인트 현황

### 인증 — `routers/auth.py`
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/auth/register` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 (JWT 발급) |

### 사용자 — `routers/users.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/v1/users/me` | 현재 로그인 사용자 정보 조회 |
| GET | `/api/v1/users/{user_id}` | 특정 사용자 조회 (본인 또는 관리자) |
| PATCH | `/api/v1/users/{user_id}` | 사용자 정보 수정 (본인 또는 관리자) |
| DELETE | `/api/v1/users/{user_id}` | 사용자 탈퇴 (본인 또는 관리자) |

### 계좌 — `routers/accounts.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/accounts/` | 계좌 등록 |
| GET | `/api/v1/accounts/` | 내 계좌 목록 조회 |
| GET | `/api/v1/accounts/{account_id}` | 계좌 상세 조회 (본인) |
| PATCH | `/api/v1/accounts/{account_id}` | 계좌 정보 수정 (본인 또는 관리자) |
| DELETE | `/api/v1/accounts/{account_id}` | 계좌 삭제 (본인) |

### 거래 — `routers/transactions.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/transactions/` | 계좌 이체 (블랙리스트 확인·알림 자동 생성) |
| GET | `/api/v1/transactions/me` | 내 전체 거래 내역 조회 |
| GET | `/api/v1/transactions/account/{account_id}` | 특정 계좌 거래 내역 조회 |
| GET | `/api/v1/transactions/{transaction_id}` | 거래 상세 조회 |
| PATCH | `/api/v1/transactions/{transaction_id}/cancel` | 송금 취소 (PENDING 상태만) |

### 보호자 — `routers/guardians.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/guardians/request` | 보호자 등록 요청 |
| GET | `/api/v1/guardians/my-guardians` | 내 보호자 목록 (APPROVED) |
| GET | `/api/v1/guardians/my-wards` | 내 피보호자 목록 (APPROVED) |
| GET | `/api/v1/guardians/pending` | 보호자로서 받은 승인 대기 목록 |
| PATCH | `/api/v1/guardians/{guardian_link_id}/approve` | 보호자 요청 승인 |
| PATCH | `/api/v1/guardians/{guardian_link_id}/reject` | 보호자 요청 거절 |
| DELETE | `/api/v1/guardians/{guardian_link_id}` | 보호자 관계 삭제 |

### 알림 — `routers/notifications.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/v1/notifications/` | 내 알림 목록 조회 (is_read 필터 옵션) |
| POST | `/api/v1/notifications/` | 알림 생성 (관리자 전용) |
| POST | `/api/v1/notifications/mark-all-read` | 전체 알림 읽음 처리 |
| PATCH | `/api/v1/notifications/{notification_id}` | 알림 읽음 상태 변경 |
| DELETE | `/api/v1/notifications/{notification_id}` | 알림 삭제 |

### 블랙리스트 — `routers/blacklist.py`
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/v1/blacklist/` | 블랙리스트 목록 조회 (공개) |
| GET | `/api/v1/blacklist/check/{account_number}` | 계좌 블랙리스트 여부 확인 (공개) |
| POST | `/api/v1/blacklist/` | 블랙리스트 등록 (관리자 전용) |
| PUT | `/api/v1/blacklist/{blacklist_id}` | 블랙리스트 수정 (관리자 전용) |
| DELETE | `/api/v1/blacklist/{blacklist_id}` | 블랙리스트 삭제 (관리자 전용) |

### 신고 — `routers/reports.py` (인증 필수)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/reports/` | 사기 거래 신고 |
| GET | `/api/v1/reports/` | 내 신고 내역 조회 |
| GET | `/api/v1/reports/{report_id}` | 신고 상세 조회 |
| DELETE | `/api/v1/reports/{report_id}` | 신고 철회 (PENDING 상태만) |

### 위험 분석 — `routers/risk.py` (**미구현 stub**)
| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/risk/analyze` | XAI 위험도 분석 (TODO: GPT-4.1-mini) |
| GET | `/api/v1/risk/{transaction_id}` | 거래 위험 스코어 조회 (TODO) |

### 관리자 — `routers/admin.py` (관리자 전용)
| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/v1/admin/users` | 전체 사용자 목록 조회 |
| GET | `/api/v1/admin/users/{user_id}` | 특정 사용자 상세 조회 |
| PATCH | `/api/v1/admin/users/{user_id}` | 사용자 정보 수정 |
| DELETE | `/api/v1/admin/users/{user_id}` | 사용자 강제 탈퇴 |
| GET | `/api/v1/admin/users/{user_id}/accounts` | 특정 사용자 계좌 목록 조회 |
| PATCH | `/api/v1/admin/accounts/{account_id}` | 계좌 정보 수정 |
| GET | `/api/v1/admin/users/{user_id}/transactions` | 특정 사용자 거래 내역 조회 |
| GET | `/api/v1/admin/reports` | 전체 신고 목록 조회 |
| PATCH | `/api/v1/admin/reports/{report_id}` | 신고 처리 상태 변경 |
| GET | `/api/v1/admin/blacklist` | 블랙리스트 전체 조회 |
| POST | `/api/v1/admin/notifications` | 전체 사용자 공지 알림 발송 |

## 주요 Enum 값
| Enum | 값 | 설명 |
|---|---|---|
| TransactionStatus | pending / completed / cancelled / blocked / flagged | 거래 상태 |
| ApprovalStatus | pending / approved / rejected | 보호자 승인 상태 |
| ReportStatus | pending / reviewed / resolved / rejected / withdrawn | 신고 처리 상태 (rejected: 반려, withdrawn: 철회) |
| NotificationType | risk_alert / guardian_request / guardian_approved / report_update / blacklist_hit / transfer_sent / transfer_received / system | 알림 유형 |
| UserRole | user / admin | 사용자 권한 |

## 코딩 규칙
- 라우터는 routers/ 폴더에 기능별로 분리
- DB CRUD 로직은 crud/ 폴더에 기능별로 분리 (crud_*.py)
- 공통 FastAPI 의존성(인증 등)은 core/deps.py에서 관리
- 스키마는 schemas/ 폴더에 Pydantic 모델로 정의
- DB 연결은 database/ 폴더에서만 관리 (get_db는 core/deps.py에서 re-export)
- 환경변수는 .env에서만 관리 (코드에 직접 입력 금지)
- 전체 사용자 목록 조회 등 관리자 전용 기능은 routers/admin.py에 위치
