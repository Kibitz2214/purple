import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
import joblib
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / 'training' / 'data' / 'Loan_Default.csv'
MODEL_DIR = BASE_DIR / 'models'
RISK_MODEL_PATH = MODEL_DIR / 'risk_model.pkl'

# risk_service.py 의 _RISK_FEATURES 와 동일하게 유지
RISK_FEATURES = [
    'total_tx_count',
    'avg_amount',
    'max_amount',
    'fraud_flag_count',
    'blacklist_hit_count',
    'account_age_days',
]


# ── 1. 규칙 기반 risk_score 레이블 산출 (40% 가중치 기준) ──────
def compute_rule_score(df: pd.DataFrame) -> pd.Series:
    '''
    Loan_Default 도메인 지식으로 risk_score(0~100) 레이블 생성.
    XGBoost 가 이 값을 학습 타깃으로 사용.
    '''
    score = np.zeros(len(df))

    # Credit_Score: 낮을수록 고위험 (기여 최대 30점)
    cs = df['Credit_Score'].clip(300, 850)
    score += (1 - (cs - 300) / 550) * 30

    # Default 이력: 가장 강한 신호 (35점)
    score += df['Status'] * 35

    # LTV (담보인정비율): 높을수록 고위험 (15점)
    ltv = df['LTV'].fillna(df['LTV'].median())
    score += (ltv.clip(0, 150) / 150) * 15

    # Debt-to-Income ratio: 높을수록 고위험 (10점)
    dtir = df['dtir1'].fillna(df['dtir1'].median())
    score += (dtir.clip(0, 100) / 100) * 10

    # 금리: 고금리 = 고위험 대출자 (10점)
    roi = df['rate_of_interest'].fillna(df['rate_of_interest'].median())
    score += (roi.clip(0, 15) / 15) * 10

    return pd.Series(score.clip(0, 100), index=df.index)


# ── 2. Loan_Default.csv → RISK_FEATURES 엔지니어링 ────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Loan_Default 컬럼을 risk_service.py 의 RISK_FEATURES 로 변환.
    실서비스에서는 FinShieldBackend 가 user_behavior_logs 로 집계해서 전송.
    '''
    rng = np.random.default_rng(42)
    n = len(df)

    income_med = df['income'].median()
    income = df['income'].fillna(income_med)

    # total_tx_count: 신용도 높을수록 거래 이력 많음
    tx_base = ((df['Credit_Score'].clip(300, 850) - 300) / 550 * 80).astype(int)
    total_tx_count = (tx_base + rng.poisson(5, size=n)).clip(1, 200)

    # avg_amount: 월 소득 기반 평균 거래금액
    avg_amount = (income / 12).clip(10_000, 50_000_000).round(0)

    # max_amount: 대출금액 = 사용자의 최대 단일 거래 금액
    max_amount = df['loan_amount'].clip(100_000, 500_000_000).astype(float)

    # fraud_flag_count: default 이력 + 연체 패턴
    base_fraud = (df['Status'] * rng.poisson(2, size=n)).clip(0, 10)
    fraud_flag_count = base_fraud.astype(int)

    # blacklist_hit_count: 음수 상환(neg_amm) + default 조합
    neg_amm = (df['Neg_ammortization'] == 'neg_amm').astype(int)
    blacklist_hit_count = (neg_amm + df['Status']).clip(0, 5).astype(int)

    # account_age_days: 대출 약정 기간(months) × 30
    term_days = (df['term'].fillna(360) * 30).astype(int).clip(30, 10950)

    out = pd.DataFrame({
        'total_tx_count':    total_tx_count.values,
        'avg_amount':        avg_amount.values,
        'max_amount':        max_amount.values,
        'fraud_flag_count':  fraud_flag_count.values,
        'blacklist_hit_count': blacklist_hit_count.values,
        'account_age_days':  term_days.values,
    }, index=df.index)

    return out[RISK_FEATURES]


# ── 3. XGBoost 학습 ────────────────────────────────────────────
def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBRegressor:
    print('[3/5] XGBoost Regressor 학습 중...')
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        eval_metric='rmse',
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print('      학습 완료')
    return model


# ── 4. 하이브리드 점수 시뮬레이션 (추론 로직 검증용) ────────────
def hybrid_score(rule: np.ndarray, ml: np.ndarray) -> np.ndarray:
    return 0.4 * rule + 0.6 * ml


# ── 5. 평가 ──────────────────────────────────────────────────
def evaluate(model: XGBRegressor,
             X_test: pd.DataFrame,
             y_rule: pd.Series) -> None:
    ml_pred   = model.predict(X_test)
    hybrid    = hybrid_score(y_rule.values, ml_pred)

    mae  = mean_absolute_error(y_rule, hybrid)
    rmse = mean_squared_error(y_rule, hybrid) ** 0.5
    r2   = r2_score(y_rule, hybrid)

    print('\n[평가 결과 - Hybrid (rule 40% + ml 60%)]')
    print(f'  MAE  : {mae:.4f}')
    print(f'  RMSE : {rmse:.4f}')
    print(f'  R2   : {r2:.4f}')

    # risk_grade 분포 확인
    grades = pd.cut(hybrid, bins=[0, 20, 40, 60, 80, 100],
                    labels=['A', 'B', 'C', 'D', 'F'], right=True)
    print('\n  [risk_grade 분포]')
    for g, cnt in grades.value_counts().sort_index().items():
        print(f'    {g}: {cnt:,}건 ({cnt/len(hybrid)*100:.1f}%)')


# ── 6. SHAP 피처 중요도 ───────────────────────────────────────
def compute_shap(model: XGBRegressor, X_test: pd.DataFrame) -> None:
    print('\n[SHAP] 피처 중요도 계산 중... (샘플 500건)')
    sample = X_test.sample(min(500, len(X_test)), random_state=42)

    explainer  = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)
    # XGBRegressor: shap_values shape = (n_samples, n_features)
    vals = np.abs(shap_values).mean(axis=0)

    ranked = sorted(zip(RISK_FEATURES, vals), key=lambda x: x[1], reverse=True)
    max_val = ranked[0][1] + 1e-9

    print('\n[SHAP 피처 중요도]')
    for feat, imp in ranked:
        bar = '#' * int(imp / max_val * 40)
        print(f'  {feat:<25} {imp:.4f}  {bar}')


# ── 메인 ─────────────────────────────────────────────────────
def main() -> None:
    print('=' * 50)
    print(' FinShieldAI - Risk Model 학습 시작')
    print(' 방식: 규칙 기반 40% + XGBoost 60% 하이브리드')
    print('=' * 50)

    if not DATA_PATH.exists():
        print(f'\n[오류] 데이터 파일 없음: {DATA_PATH}')
        sys.exit(1)

    MODEL_DIR.mkdir(exist_ok=True)

    # 1. 로드
    print(f'[1/5] 데이터 로드: {DATA_PATH.name}')
    df = pd.read_csv(DATA_PATH)
    print(f'      전체: {len(df):,}행 | default: {df["Status"].sum():,}건 ({df["Status"].mean()*100:.1f}%)')

    # 2. 피처 엔지니어링 + 레이블 산출
    print('[2/5] 피처 엔지니어링 및 rule_score 레이블 산출')
    X = engineer_features(df)
    y = compute_rule_score(df)
    print(f'      rule_score -> min: {y.min():.1f} | max: {y.max():.1f} | mean: {y.mean():.1f}')

    # 3. 분할
    print('[3/5] 학습/테스트 분할 (8:2)')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 4. XGBoost 학습
    model = train_model(X_train, y_train)

    # 5. 평가 (하이브리드 기준)
    print('[4/5] 하이브리드 평가')
    evaluate(model, X_test, y_test)

    # 6. SHAP
    print('[5/5] SHAP 분석')
    compute_shap(model, X_test)

    # 저장
    joblib.dump(model, RISK_MODEL_PATH)
    print('\n저장 완료')
    print(f'  -> {RISK_MODEL_PATH}')
    print('\n추론 시: final_score = 0.4 * rule_score + 0.6 * model.predict()')
    print('다음 단계: uvicorn main:app --reload --port 8001')


if __name__ == '__main__':
    main()
