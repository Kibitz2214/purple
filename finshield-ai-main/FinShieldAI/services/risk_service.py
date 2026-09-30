import joblib
import numpy as np
from pathlib import Path
from core.config import RISK_MODEL_PATH
from schemas.risk import RiskRequest, RiskResponse

# 서버 시작 시 1회 로드 (요청마다 로드 금지)
_risk_model = None
_explainer = None

_RISK_FEATURES = [
    'total_tx_count',
    'avg_amount',
    'max_amount',
    'fraud_flag_count',
    'blacklist_hit_count',
    'account_age_days',
]

_SHAP_LABEL_MAP = {
    'total_tx_count':      '거래 횟수 부족',
    'avg_amount':          '평균 거래 금액 이상',
    'max_amount':          '최대 거래 금액 이상',
    'fraud_flag_count':    '사기 신고 이력',
    'blacklist_hit_count': '블랙리스트 접촉 이력',
    'account_age_days':    '계정 생성 후 경과일 부족',
}

# 낮을수록 위험한 피처 (SHAP 음수 → 위험 기여)
_LOW_RISK_FEATURES  = {'total_tx_count', 'account_age_days'}
# 높을수록 위험한 피처 (SHAP 양수 → 위험 기여)
_HIGH_RISK_FEATURES = {'fraud_flag_count', 'blacklist_hit_count', 'avg_amount', 'max_amount'}


def load_risk_model() -> None:
    global _risk_model, _explainer
    if not Path(RISK_MODEL_PATH).exists():
        raise RuntimeError('risk_model.pkl 파일이 없습니다. 먼저 학습을 실행하세요.')

    _risk_model = joblib.load(RISK_MODEL_PATH)

    import shap
    _explainer = shap.TreeExplainer(_risk_model)


def is_loaded() -> bool:
    return _risk_model is not None


# ── 규칙 기반 스코어 (40% 가중치) ─────────────────────────────
def _rule_score(req: RiskRequest) -> float:
    score = 0.0

    # 사기 신고 이력: 건당 15점, 최대 40점
    score += min(req.fraud_flag_count * 15, 40)

    # 블랙리스트 접촉: 건당 20점, 최대 30점
    score += min(req.blacklist_hit_count * 20, 30)

    # 계정 연령: 신규일수록 위험
    if req.account_age_days < 90:
        score += 20
    elif req.account_age_days < 365:
        score += 10

    # 거래 이력 부족
    if req.total_tx_count < 5:
        score += 10

    # 최대 거래금액이 평균의 5배 초과 → 이상 고액 거래
    if req.avg_amount > 0 and req.max_amount / req.avg_amount > 5:
        score += 10

    return min(score, 100.0)


def predict_risk(req: RiskRequest) -> RiskResponse:
    if not is_loaded():
        raise RuntimeError('리스크 모델이 로드되지 않았습니다.')

    features = np.array([[
        req.total_tx_count,
        req.avg_amount,
        req.max_amount,
        req.fraud_flag_count,
        req.blacklist_hit_count,
        req.account_age_days,
    ]])

    # 하이브리드: 규칙 기반 40% + XGBoost 60%
    ml_score   = float(_risk_model.predict(features)[0])
    rule_score = _rule_score(req)
    risk_score = 0.4 * rule_score + 0.6 * ml_score
    risk_score = max(0.0, min(100.0, risk_score))

    # 본인 계좌 블랙리스트 보유 시 최소값 보장
    if req.own_blacklist_count >= 2:
        risk_score = max(risk_score, 90.0)
    elif req.own_blacklist_count >= 1:
        risk_score = max(risk_score, 80.0)

    risk_score = round(risk_score, 2)
    trust_score = round(100.0 - risk_score, 2)

    # 등급 산정 (A~F)
    if risk_score < 20:
        risk_grade = 'A'
    elif risk_score < 40:
        risk_grade = 'B'
    elif risk_score < 60:
        risk_grade = 'C'
    elif risk_score < 80:
        risk_grade = 'D'
    else:
        risk_grade = 'F'

    top_reasons = _get_top_reasons(features)

    return RiskResponse(
        user_id=req.user_id,
        risk_score=risk_score,
        trust_score=trust_score,
        risk_grade=risk_grade,
        top_reasons=top_reasons,
    )


def _get_top_reasons(features: np.ndarray) -> list[str]:
    if _explainer is None:
        return []
    try:
        shap_values = _explainer.shap_values(features)
        # XGBRegressor: shape = (n_samples, n_features)
        if isinstance(shap_values, list):
            vals = shap_values[0][0]
        else:
            vals = shap_values[0]

        top_indices = np.argsort(np.abs(vals))[::-1][:3]
        return [
            _SHAP_LABEL_MAP.get(_RISK_FEATURES[i], _RISK_FEATURES[i])
            for i in top_indices
            if (
                (_RISK_FEATURES[i] in _LOW_RISK_FEATURES  and vals[i] < -0.01) or
                (_RISK_FEATURES[i] in _HIGH_RISK_FEATURES and vals[i] >  0.01)
            )
        ]
    except Exception:
        return []
