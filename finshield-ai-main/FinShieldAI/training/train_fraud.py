import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import joblib
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / 'training' / 'data' / 'PS_20174392719_1491204439457_log.csv'
MODEL_DIR = BASE_DIR / 'models'
FRAUD_MODEL_PATH = MODEL_DIR / 'fraud_model.pkl'

FEATURE_COLUMNS = [
    'amount_log',
    'hour_of_day',
    'day_of_week',
    'is_blacklisted',
    'is_new_receiver',
    'sender_tx_count_7d',
    'sender_avg_amount_30d_log',
    'sender_balance_before_log',
    'amount_to_balance_ratio_log',
]

# SMOTE 후 사기/정상 비율 (소수 → 다수 기준)
_SMOTE_RATIO = 0.015   # 사기 ~6,500건 → ~33,000건
# RandomUnderSampler 후 목표 비율 사기/정상 = 1:5
_UNDER_RATIO = 0.20    # 정상 ~165,000건으로 축소 → 최종 5:1


def load_and_engineer(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    print(f'[1] 데이터 로드: {path}')
    df = pd.read_csv(path)
    print(f'    원본: {len(df):,}행')

    # 컬럼명 오타 수정
    df = df.rename(columns={'oldbalanceOrg': 'oldbalanceOrig'})

    # TRANSFER + CASH_OUT 만 사용 (사기 발생 유형)
    df = df[df['type'].isin(['TRANSFER', 'CASH_OUT'])].copy()
    print(f'    TRANSFER+CASH_OUT 필터: {len(df):,}행')

    # amount == 0 제거
    df = df[df['amount'] > 0].copy()
    print(f'    amount > 0 필터: {len(df):,}행')

    total     = len(df)
    fraud_cnt = int(df['isFraud'].sum())
    print(f'    사기: {fraud_cnt:,}건 ({fraud_cnt/total*100:.3f}%)')

    rng         = np.random.default_rng(42)
    fraud_mask  = df['isFraud'] == 1
    normal_mask = ~fraud_mask

    # 시간 파생 (step 1 = 1시간)
    df['hour_of_day'] = (df['step'] % 24).astype(int)
    df['day_of_week'] = ((df['step'] // 24) % 7).astype(int)

    # 잔액 피처 (사전 잔액만 사용 — 사후 잔액은 실서비스 추론 시 미존재)
    df['sender_balance_before']   = df['oldbalanceOrig']
    df['amount_to_balance_ratio'] = df['amount'] / (df['oldbalanceOrig'] + 1)

    # sender_avg_amount_30d: nameOrig 기준 step 순 누적 이동평균 (현재 거래 제외)
    print('    sender_avg_amount_30d 계산 중...')
    df_sorted = df.sort_values('step')
    cnt  = df_sorted.groupby('nameOrig').cumcount()               # 0-indexed, 현재 행 이전 거래 수
    csum = df_sorted.groupby('nameOrig')['amount'].cumsum()       # 현재 포함 누적합
    df_sorted['sender_avg_amount_30d'] = np.where(
        cnt == 0,
        df_sorted['amount'],                   # 첫 거래는 현재 금액으로 대체
        (csum - df_sorted['amount']) / cnt,    # 이전 거래들의 평균
    )
    df['sender_avg_amount_30d'] = df_sorted['sender_avg_amount_30d'].reindex(df.index)

    # 합성 피처 (실서비스에서 백엔드가 전송)
    df['sender_tx_count_7d'] = 0
    df.loc[normal_mask, 'sender_tx_count_7d'] = rng.poisson(lam=4,  size=normal_mask.sum())
    df.loc[fraud_mask,  'sender_tx_count_7d'] = rng.poisson(lam=12, size=fraud_mask.sum())
    df['sender_tx_count_7d'] = df['sender_tx_count_7d'].clip(1, 50).astype(int)

    df['is_blacklisted'] = 0
    df.loc[fraud_mask,  'is_blacklisted'] = (rng.random(fraud_mask.sum())  < 0.30).astype(int)
    df.loc[normal_mask, 'is_blacklisted'] = (rng.random(normal_mask.sum()) < 0.02).astype(int)

    df['is_new_receiver'] = 0
    df.loc[fraud_mask,  'is_new_receiver'] = (rng.random(fraud_mask.sum())  < 0.70).astype(int)
    df.loc[normal_mask, 'is_new_receiver'] = (rng.random(normal_mask.sum()) < 0.10).astype(int)

    # log1p 변환 (StandardScaler 대체)
    df['amount_log']                  = np.log1p(df['amount'])
    df['sender_balance_before_log']   = np.log1p(df['sender_balance_before'])
    df['amount_to_balance_ratio_log'] = np.log1p(df['amount_to_balance_ratio'])
    df['sender_avg_amount_30d_log']   = np.log1p(df['sender_avg_amount_30d'])

    return df[FEATURE_COLUMNS], df['isFraud']


def print_feature_distribution(X: pd.DataFrame, y: pd.Series) -> None:
    print('\n[피처 분포 비교] 사기(1) vs 정상(0)')
    header = f'{"피처":<32} {"사기 mean":>12} {"정상 mean":>12} {"사기 std":>12} {"정상 std":>12}'
    print(header)
    print('-' * len(header))
    for col in FEATURE_COLUMNS:
        f_vals = X.loc[y == 1, col]
        n_vals = X.loc[y == 0, col]
        print(
            f'{col:<32} '
            f'{f_vals.mean():>12.4f} '
            f'{n_vals.mean():>12.4f} '
            f'{f_vals.std():>12.4f} '
            f'{n_vals.std():>12.4f}'
        )


def balance_classes(
    X_train: pd.DataFrame, y_train: pd.Series
) -> tuple[pd.DataFrame, pd.Series]:
    n_before = int((y_train == 0).sum())
    f_before = int((y_train == 1).sum())
    print(f'    처리 전  정상: {n_before:,} | 사기: {f_before:,} | 비율 약 {n_before//f_before}:1')

    # 1단계: SMOTE 오버샘플링 (사기 소수 → 중간 수준)
    smote = SMOTE(sampling_strategy=_SMOTE_RATIO, random_state=42, k_neighbors=5)
    X_sm, y_sm = smote.fit_resample(X_train, y_train)
    print(f'    SMOTE 후 정상: {int((y_sm==0).sum()):,} | 사기: {int((y_sm==1).sum()):,}')

    # 2단계: RandomUnderSampler 언더샘플링 (최종 5:1)
    rus = RandomUnderSampler(sampling_strategy=_UNDER_RATIO, random_state=42)
    X_res, y_res = rus.fit_resample(X_sm, y_sm)

    n_after = int((y_res == 0).sum())
    f_after = int((y_res == 1).sum())
    print(f'    처리 후  정상: {n_after:,} | 사기: {f_after:,} | 비율 {n_after//f_after}:1')
    print(f'    총 학습 샘플: {len(X_res):,}행')

    return X_res, y_res


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    # early stopping 을 위한 내부 검증셋 (균형 처리된 학습셋의 10%)
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
    )
    print(f'[4/5] XGBoost 학습 중... (학습 {len(X_tr):,} / 내부검증 {len(X_val):,})')

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        scale_pos_weight=1,
        eval_metric='auc',
        early_stopping_rounds=20,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
    print(f'      최적 트리 수: {model.best_iteration + 1} / 300')
    print('      학습 완료')
    return model


def evaluate(model: XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> None:
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    auc       = roc_auc_score(y_test, y_prob)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall    = recall_score(y_test, y_pred, zero_division=0)
    f1        = f1_score(y_test, y_pred, zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)

    print('\n[5/5] 평가 결과 (Test, 원본 분포 유지)')
    print(f'  AUC-ROC   : {auc:.4f}')
    print(f'  Precision : {precision:.4f}')
    print(f'  Recall    : {recall:.4f}')
    print(f'  F1-Score  : {f1:.4f}')
    print()
    print(classification_report(y_test, y_pred, target_names=['정상', '사기'], digits=4))

    tn, fp, fn, tp = cm.ravel()
    print('  Confusion Matrix:')
    print(f'                  예측 정상   예측 사기')
    print(f'  실제 정상  {tn:>10,}  {fp:>10,}')
    print(f'  실제 사기  {fn:>10,}  {tp:>10,}')


def compute_shap(model: XGBClassifier, X_test: pd.DataFrame) -> None:
    print('[SHAP] 피처 중요도 계산 중... (샘플 500건)')
    sample = X_test.sample(min(500, len(X_test)), random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)

    if isinstance(shap_values, list):
        vals = np.abs(shap_values[1]).mean(axis=0)
    else:
        vals = np.abs(shap_values).mean(axis=0)

    ranked = sorted(zip(FEATURE_COLUMNS, vals), key=lambda x: x[1], reverse=True)

    print('\n[SHAP 피처 중요도 Top 5]')
    for feat, imp in ranked[:5]:
        bar = '#' * int(imp * 40 / (ranked[0][1] + 1e-9))
        print(f'  {feat:<32} {imp:.4f}  {bar}')


def main() -> None:
    print('=' * 57)
    print(' FinShieldAI - Fraud Model 학습 및 평가 (4단계)')
    print('=' * 57)

    if not DATA_PATH.exists():
        print(f'\n[오류] 데이터 파일 없음: {DATA_PATH}')
        sys.exit(1)

    MODEL_DIR.mkdir(exist_ok=True)

    X, y = load_and_engineer(DATA_PATH)

    print(f'\n[2] 피처셋: {len(FEATURE_COLUMNS)}개 / {len(X):,}행')

    print('\n[3] 학습/테스트 분할 (8:2, stratify)')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f'    학습: {len(X_train):,}행 | 테스트: {len(X_test):,}행')

    print('\n[3] 불균형 처리 (SMOTE + RandomUnderSampler, 목표 5:1)')
    X_res, y_res = balance_classes(X_train, y_train)

    model = train_model(X_res, y_res)

    evaluate(model, X_test, y_test)

    compute_shap(model, X_test)

    joblib.dump(model, FRAUD_MODEL_PATH)
    print(f'\n[저장 완료]')
    print(f'  -> {FRAUD_MODEL_PATH}')


if __name__ == '__main__':
    main()
