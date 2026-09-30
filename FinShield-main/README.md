# FinShield

> AI 기반 금융사기 예방 서비스 — 금융 취약계층을 위한 지능형 보호 시스템

## 팀 정보
- **팀명**: FinShield
- **과제명**: AI 기반 금융사기 예방 시스템
- **팀장**: 황승구
- **팀원**: 이지훈, 조환성, 조원준, 몽흐벌드, 아말자르갈
- **지도교수**: 김광수
- **수행기간**: 2026년 3월 13일 ~ 2026년 12월 18일

## 주요 기능
1. 개인 맞춤형 AI 기반 이상 거래 탐지 (FDS)
2. 설명 가능한 AI (XAI) 위험 스코어링
3. 참여형 사기 신고 및 블랙리스트 시스템
4. 인지 유도형 안전 UI
5. 보호자 교차 승인 시스템

## 프로젝트 구조
```
FinShield/
├── FinShieldBackend/      ← 백엔드 (Python / FastAPI / TiDB / MongoDB)
└── FinShieldFrontend/     ← 프론트엔드 (React Native / Expo)
```

## 기술 스택
| 구분 | 기술 |
|---|---|
| 백엔드 | Python 3.12, FastAPI 0.135.3 |
| 정형 DB | TiDB Cloud (MySQL 호환, SQLAlchemy 2.0 + PyMySQL) |
| 비정형 DB | MongoDB Atlas (motor + pymongo) |
| AI 분석 | OpenAI GPT-4.1-mini (XAI) |
| 프론트엔드 | React Native 0.76, Expo SDK 54, TypeScript |
| 서버 | AWS EC2 (t2.micro) |

## 구현 현황
| 영역 | 상태 |
|---|---|
| 인증 (회원가입·로그인·JWT) | 완료 |
| 사용자 관리 | 완료 |
| 계좌 관리 | 완료 |
| 송금·거래 (블랙리스트 차단·알림 포함) | 완료 |
| 보호자 교차 승인 | 완료 |
| 신고 | 완료 |
| 블랙리스트 | 완료 |
| 알림 | 완료 |
| 관리자 기능 | 완료 |
| XAI 위험도 분석 (`/api/v1/risk/`) | 미구현 (stub) |
| 프론트엔드 | 개발 초기 단계 |

## 개발 시작

### 백엔드
```bash
cd FinShieldBackend
venv\Scripts\activate
uvicorn main:app --reload
# API 문서: http://localhost:8000/docs
```

### 프론트엔드
```bash
cd FinShieldFrontend
npm install
npx expo start
```
