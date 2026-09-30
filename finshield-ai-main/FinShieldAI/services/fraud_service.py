import logging
import joblib
import pandas as pd
import numpy as np
import shap
from pathlib import Path
from core.config import FRAUD_MODEL_PATH, FEATURE_COLUMNS
from schemas.fraud import FraudRequest, FraudResponse

logger = logging.getLogger(__name__)

# 서버 시작 시 1회 로드 (요청마다 로드 금지)
_model = None
_explainer = None

FEATURE_LABELS = {
    'amount_log':                  '거래 금액 이상',
    'hour_of_day':                 '심야/새벽 시간대',
    'day_of_week':                 '비정상 요일 패턴',
    'is_blacklisted':              '블랙리스트 계좌',
    'is_new_receiver':             '신규/미등록 수신 계좌',
    'sender_tx_count_7d':          '단기 거래 집중',
    'sender_avg_amount_30d_log':   '평소 금액 대비 이상',
    'sender_balance_before_log':   '잔액 대비 고액 출금',
    'amount_to_balance_ratio_log': '잔액 소진율 이상',
}


def load_fraud_model() -> None:
    global _model, _explainer
    if not Path(FRAUD_MODEL_PATH).exists():
        raise RuntimeError('fraud_model.pkl 파일이 없습니다. 먼저 학습을 실행하세요.')

    model = joblib.load(FRAUD_MODEL_PATH)

    # 피처 이름 불일치 시 즉시 감지 (503, 모델 재학습 필요)
    model_features = model.get_booster().feature_names
    if model_features is None or list(model_features) != list(FEATURE_COLUMNS):
        raise RuntimeError(
            f'모델 피처 불일치 — python training/train_fraud.py 로 재학습하세요.\n'
            f'  모델: {model_features}\n'
            f'  코드: {FEATURE_COLUMNS}'
        )

    _model = model
    _explainer = shap.TreeExplainer(_model)


def is_loaded() -> bool:
    return _model is not None


def _get_recommendation(prob: float, is_blacklisted: bool) -> str:
    if is_blacklisted or prob >= 0.8:
        return 'block'
    elif prob >= 0.5:
        return 'guardian_approval'
    elif prob >= 0.3:
        return 'warn'
    return 'allow'


def predict_fraud(req: FraudRequest) -> FraudResponse:
    if not is_loaded():
        raise RuntimeError('모델이 로드되지 않았습니다.')

    amount_log                  = np.log1p(req.amount)
    sender_balance_before_log   = np.log1p(req.sender_balance_before)
    sender_avg_amount_30d_log   = np.log1p(req.sender_avg_amount_30d)
    amount_to_balance_ratio_log = np.log1p(req.amount / (req.sender_balance_before + 1))

    features = pd.DataFrame([{
        'amount_log':                  amount_log,
        'hour_of_day':                 req.hour_of_day,
        'day_of_week':                 req.day_of_week,
        'is_blacklisted':              int(req.is_blacklisted),
        'is_new_receiver':             int(req.is_new_receiver),
        'sender_tx_count_7d':          req.sender_tx_count_7d,
        'sender_avg_amount_30d_log':   sender_avg_amount_30d_log,
        'sender_balance_before_log':   sender_balance_before_log,
        'amount_to_balance_ratio_log': amount_to_balance_ratio_log,
    }], columns=FEATURE_COLUMNS)

    logger.debug(
        '[fraud_service] 입력 피처 | tx_id=%s amount=%s amount_log=%.4f '
        'hour=%s day=%s is_blacklisted=%s is_new_receiver=%s '
        'tx_count_7d=%s avg_amount_30d=%s balance_before=%s',
        req.transaction_id, req.amount, amount_log,
        req.hour_of_day, req.day_of_week, req.is_blacklisted, req.is_new_receiver,
        req.sender_tx_count_7d, req.sender_avg_amount_30d, req.sender_balance_before,
    )

    prob = float(_model.predict_proba(features)[0][1])

    # 방식 C: fraud_score + receiver_risk_score * 0.3 (클램핑 포함)
    # receiver_risk_score = 0.0이면 기존과 동일
    final_score = min(prob * 100 + req.receiver_risk_score * 0.3, 100.0)
    final_prob  = round(final_score / 100, 4)

    is_fraud = final_prob >= 0.5 or req.is_blacklisted

    # 리스크 레벨
    if final_prob >= 0.8:
        risk_level = 'critical'
    elif final_prob >= 0.5:
        risk_level = 'high'
    elif final_prob >= 0.3:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    top_reasons = _get_top_reasons(features)
    recommendation = _get_recommendation(final_prob, req.is_blacklisted)

    logger.debug(
        '[fraud_service] 출력 | tx_id=%s fraud_probability=%.4f '
        'receiver_risk_score=%.1f final_score=%.2f recommendation=%s',
        req.transaction_id, prob,
        req.receiver_risk_score, final_score, recommendation,
    )

    return FraudResponse(
        transaction_id=req.transaction_id,
        fraud_probability=final_prob,
        is_fraud=is_fraud,
        risk_level=risk_level,
        top_reasons=top_reasons,
        recommendation=recommendation,
    )


def _get_top_reasons(features: pd.DataFrame) -> list[str]:
    if _explainer is None:
        return []
    try:
        shap_values = _explainer.shap_values(features)
        # XGBoost 이진 분류: list 이면 [1] = 사기 클래스
        if isinstance(shap_values, list):
            vals = shap_values[1][0]
        else:
            vals = shap_values[0]

        top_indices = np.argsort(np.abs(vals))[::-1][:3]
        return [
            FEATURE_LABELS.get(FEATURE_COLUMNS[i], FEATURE_COLUMNS[i])
            for i in top_indices
            if abs(vals[i]) > 0
        ]
    except Exception:
        return []
