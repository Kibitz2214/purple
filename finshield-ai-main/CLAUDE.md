# FinShieldAI — Claude CLI 컨텍스트

## 프로젝트 개요
FinShield 금융사기 예방 시스템의 AI 추론 서버.
XGBoost + SHAP 기반 이상거래 탐지(FDS), 리스크 스코어링, 블랙리스트 신고 심사 제공.
FinShieldBackend(별도 리포)와 내부 API로 통신.

## 기술 스택
- Python 3.12
- FastAPI 0.115.0 / uvicorn
- XGBoost 2.1.1 + SHAP 0.46.0
- scikit-learn / imbalanced-learn (SMOTE + RandomUnderSampler)
- joblib (모델 직렬화)
- 포트: 8001 (백엔드는 8000)

## 폴더 구조
```
finshield-ai/
├── CLAUDE.md
├── .gitignore
├── .env                       ← AI_SERVER_PORT=8001 (Git 제외)
├── README.md
└── FinShieldAI/
    ├── main.py                ← FastAPI 진입점 (lifespan, CORSMiddleware)
    ├── requirements.txt
    ├── venv/                  ← 가상환경 (Git 제외)
    ├── core/
    │   ├── __init__.py
    │   └── config.py          ← 모델 경로, 포트, FEATURE_COLUMNS
    ├── models/                ← .pkl 파일 (Git 제외)
    │   ├── fraud_model.pkl    ← PaySim 기반 9-피처 XGBClassifier
    │   └── risk_model.pkl     ← 6-피처 XGBRegressor
    ├── routers/
    │   ├── __init__.py
    │   ├── health.py          ← GET  /health
    │   ├── fraud.py           ← POST /predict/fraud
    │   ├── risk.py            ← POST /predict/risk-score
    │   └── report.py          ← POST /predict/report-review
    ├── schemas/
    │   ├── __init__.py
    │   ├── fraud.py           ← FraudRequest / FraudResponse
    │   ├── risk.py            ← RiskRequest / RiskResponse
    │   └── report.py          ← ReportReviewRequest / ReportReviewResponse
    ├── services/
    │   ├── __init__.py
    │   ├── fraud_service.py   ← XGBoost 추론 + SHAP + 피처 검증
    │   ├── risk_service.py    ← 하이브리드 추론 (규칙 40% + XGBoost 60%)
    │   └── report_service.py  ← 블랙리스트 신고 심사 (risk_model 재활용)
    └── training/
        ├── train_fraud.py     ← FDS 모델 학습 (SMOTE + RandomUnderSampler + XGBoost)
        ├── train_risk.py      ← 리스크 모델 학습 (규칙 기반 레이블 + XGBRegressor)
        └── data/              ← .csv 파일 (Git 제외)
            ├── PS_20174392719_1491204439457_log.csv  ← FDS 학습용 (PaySim, Kaggle)
            └── Loan_Default.csv                      ← 리스크 학습용 (Kaggle)
```

> 참고: AI 서버는 FinShieldBackend 의 호출을 받는 쪽이므로 백엔드 호출용 클라이언트는 두지 않는다.
> MongoDB user_behavior_logs CRUD 와 고위험 거래 냉각기는 FinShieldBackend 에 구현되어 있다.

## API 엔드포인트

### POST /predict/fraud
송금 시 FinShieldBackend에서 호출. 이상거래 탐지.

Request:
```json
{
  "transaction_id": 1234,
  "amount": 5000000,
  "sender_account_id": 1,
  "receiver_account_id": 2,
  "hour_of_day": 3,
  "day_of_week": 6,
  "is_blacklisted": false,
  "is_new_receiver": true,
  "sender_tx_count_7d": 15,
  "sender_avg_amount_30d": 200000,
  "sender_balance_before": 3000000,
  "receiver_risk_score": 45.0
}
```

필드 제약:
- `amount`, `sender_avg_amount_30d`, `sender_balance_before` : `>= 0`
- `hour_of_day` : `0~23`
- `day_of_week` : `0~6` (0=월)
- `sender_tx_count_7d` : `>= 0`
- `receiver_risk_score` : 선택값, 기본 `0.0` (수신자 리스크 스코어 0~100)

Response:
```json
{
  "transaction_id": 1234,
  "fraud_probability": 0.87,
  "is_fraud": true,
  "risk_level": "critical",
  "top_reasons": ["거래 금액 이상", "심야/새벽 시간대", "단기 거래 집중"],
  "recommendation": "block"
}
```

recommendation 기준:
- `allow`             : `final_prob < 0.3`
- `warn`              : `0.3 ≤ final_prob < 0.5`
- `guardian_approval` : `0.5 ≤ final_prob < 0.8`
- `block`             : `final_prob ≥ 0.8` 또는 `is_blacklisted = true`

최종 확률 산출 (방식 C):
```
final_score = min(fraud_prob * 100 + receiver_risk_score * 0.3, 100.0)
final_prob  = round(final_score / 100, 4)
```

### POST /predict/risk-score
사용자 신뢰점수 + 리스크 스코어 반환.
추론 방식: 규칙 기반 40% + XGBoost 60% 하이브리드.

Request:
```json
{
  "user_id": 1,
  "total_tx_count": 120,
  "avg_amount": 200000,
  "max_amount": 1500000,
  "fraud_flag_count": 0,
  "blacklist_hit_count": 0,
  "account_age_days": 365,
  "own_blacklist_count": 0
}
```

필드 제약: 모든 수치 필드 `>= 0`. `own_blacklist_count` 기본값 `0`.

Response:
```json
{
  "user_id": 1,
  "risk_score": 12.5,
  "trust_score": 87.5,
  "risk_grade": "A",
  "top_reasons": []
}
```

등급 기준: A(<20) / B(<40) / C(<60) / D(<80) / F(≥80)

블랙리스트 계좌 보유 시 최솟값 보장:
- `own_blacklist_count >= 1` → `risk_score >= 80.0`
- `own_blacklist_count >= 2` → `risk_score >= 90.0`

### POST /predict/report-review
블랙리스트 신고 AI 심사. 리스크 모델을 재활용해 등록 여부 판단.

Request:
```json
{
  "account_number": "1234567890",
  "report_id": 1,
  "report_content": "피싱 의심",
  "total_report_count": 3,
  "receiver_tx_count": 50,
  "receiver_total_amount": 5000000,
  "total_tx_count": 30,
  "avg_amount": 300000,
  "max_amount": 2000000,
  "fraud_flag_count": 2,
  "blacklist_hit_count": 1,
  "account_age_days": 45
}
```

Response:
```json
{
  "decision": "approved",
  "confidence": 0.82,
  "risk_score": 82.0,
  "reason": "리스크 스코어 82.0점, 신고 건수 3건으로 블랙리스트 등록을 승인합니다."
}
```

decision 기준:
- `approved`  : `risk_score >= 70` AND `total_report_count >= 2`
- `rejected`  : `risk_score <= 30` AND `total_report_count <= 1`
- `escalated` : 그 외 (관리자 검토)

### GET /health
모델 메모리 로드 상태 확인. 백엔드에서 주기적으로 호출.

Response:
```json
{
  "status": "ok",
  "fraud_model": "loaded",
  "risk_model": "loaded"
}
```

값: `"loaded"` / `"not_loaded"`

## 구현 현황

### 완료
| 기능 | 상세 |
|---|---|
| 이상거래 탐지 (FDS) | PaySim 기반 XGBClassifier + SMOTE/UnderSampler (`services/fraud_service.py`) |
| 수신자 리스크 가산 (방식 C) | `final_score = min(fraud_prob*100 + receiver_risk_score*0.3, 100)` |
| 피처 이름 검증 | `load_fraud_model()` 에서 모델 내부 피처 vs FEATURE_COLUMNS 불일치 시 RuntimeError → 503 |
| 리스크 스코어 하이브리드 | 규칙 기반 40% + XGBRegressor 60% (`services/risk_service.py`) |
| 블랙리스트 계좌 최솟값 보장 | `own_blacklist_count >= 1` → 80점, `>= 2` → 90점 |
| XAI 한국어 위험 요인 | SHAP TreeExplainer + 피처 방향성 필터 (낮을수록/높을수록 위험 구분) |
| 블랙리스트 신고 심사 | `services/report_service.py` — risk_model 재활용, 3단계 판단 |
| API 라우터 4종 | `/health`, `/predict/fraud`, `/predict/risk-score`, `/predict/report-review` |
| 입력값 범위 검증 | Pydantic `Field(ge=0/le=23/le=6)` → 422 자동 반환 |
| 모델 1회 로드 | `lifespan` 에서 서버 시작 시 모델·Explainer 1회 로드 |

### 미구현 / 미완료
현재 AI 서버 측 미구현 항목 없음.

> 다음 기능은 AI 서버가 아닌 FinShieldBackend 담당이다.
> - MongoDB user_behavior_logs CRUD (개인 행동 베이스라인)
> - 고위험 거래 냉각기 (guardian_approval/block 10분 대기·HTTP 429)
> - 참여형 블랙리스트 자동 검증 (신고 5회 누적 시 자동 등록)

## 데이터셋 현황
| 모델 | 데이터 | 건수 |
|---|---|---|
| FDS (fraud_model) | PaySim `PS_20174392719_1491204439457_log.csv` (Kaggle) | TRANSFER+CASH_OUT 필터 후 사용 |
| 리스크 (risk_model) | `Loan_Default.csv` (Kaggle) | 148,670건 |

## 모델 상세

### fraud_model (XGBClassifier)
- 데이터: PaySim — TRANSFER / CASH_OUT 거래 유형만 사용
- 클래스 불균형 처리: SMOTE (sampling_strategy=0.015) → RandomUnderSampler (5:1)
- 피처 전처리: log1p 변환 (StandardScaler 미사용)
- 피처 수: 9개 (아래 FEATURE_COLUMNS 참조)
- 모델 로드 시 피처 이름 자동 검증 → 불일치 시 서버 경고 + 503 반환

### risk_model (XGBRegressor)
- 피처 수: 6개 (아래 RISK_FEATURES 참조)
- 추론: 규칙 기반 점수(40%) + XGBoost 회귀(60%) 가중합
- SHAP 위험 요인: 방향성 기반 필터 적용
  - 낮을수록 위험 (`total_tx_count`, `account_age_days`): SHAP 음수 기여만 표시
  - 높을수록 위험 (`fraud_flag_count`, `blacklist_hit_count`, `avg_amount`, `max_amount`): SHAP 양수 기여만 표시

## 피처 컬럼 (학습/추론 동일하게 유지 필수)
- `FEATURE_COLUMNS` : `core/config.py` 에 정의 (`fraud_service`, `train_fraud` 공용)
- `RISK_FEATURES` : `services/risk_service.py` 의 `_RISK_FEATURES` 와 `training/train_risk.py` 의 `RISK_FEATURES` 에 각각 정의 — 두 곳을 항상 동일하게 유지할 것.

```python
# FDS 모델 (core/config.py)
FEATURE_COLUMNS = [
    'amount_log',                  # log1p(amount)
    'hour_of_day',                 # 거래 시각 0~23
    'day_of_week',                 # 요일 0=월 ~ 6=일
    'is_blacklisted',              # 블랙리스트 여부 0/1
    'is_new_receiver',             # 신규/미등록 수신 계좌 0/1
    'sender_tx_count_7d',          # 최근 7일 거래 횟수
    'sender_avg_amount_30d_log',   # log1p(30일 평균 거래 금액)
    'sender_balance_before_log',   # log1p(송금 전 잔액)
    'amount_to_balance_ratio_log', # log1p(amount / (balance + 1))
]

# 리스크 모델 (risk_service._RISK_FEATURES / train_risk.RISK_FEATURES)
RISK_FEATURES = [
    'total_tx_count',        # 전체 거래 횟수
    'avg_amount',            # 평균 거래 금액
    'max_amount',            # 최대 거래 금액
    'fraud_flag_count',      # 과거 이상거래 탐지 횟수
    'blacklist_hit_count',   # 블랙리스트 계좌 거래 횟수
    'account_age_days',      # 계좌 개설 후 경과일
]
```

## 제외 기능
- OpenAI / Gemma 등 외부 LLM API 사용 금지 (데이터 보안)
- 딥페이크 탐지 (범위 제외)

## 코딩 규칙
- 언어: Python 3.12
- 들여쓰기: 4칸
- 따옴표: 작은따옴표 ('')
- 주석: 한국어
- 라우터는 `routers/` 에서만, 비즈니스 로직은 `services/` 에서만
- 모델 로드는 서버 시작 시 1회만 (요청마다 로드 금지)
- SHAP Explainer도 서버 시작 시 1회만 초기화 (전역 캐싱)
- 환경변수는 `.env` 에서만 관리
- 모델 파일(`.pkl`), 학습 데이터(`.csv`)는 Git 커밋 금지

## 연동 프로젝트
- FinShieldBackend: git_capstone_2team/FinShieldBackend
- 백엔드 포트: 8000
- AI 서버 포트: 8001
- 통신: 내부 httpx 비동기 호출

## 개발 시작
```bash
cd FinShieldAI
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 모델 재학습 순서
```bash
cd FinShieldAI
# 1. training/data/ 에 CSV 배치
#    - FDS  : PS_20174392719_1491204439457_log.csv
#    - 리스크: Loan_Default.csv
python training/train_fraud.py   # → models/fraud_model.pkl
python training/train_risk.py    # → models/risk_model.pkl
# 2. 서버 재시작
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 다음 단계
1. EC2 배포 및 운영 모니터링 설정 (CloudWatch / 헬스체크)
2. TiDB 실데이터로 모델 재학습
3. CORS `allow_origins` 운영 환경에서 백엔드 IP로 제한
