import numpy as np
import services.risk_service as risk_service
from schemas.report import ReportReviewRequest, ReportReviewResponse


# 규칙 기반 스코어 (40% 가중치)
def _rule_score(req: ReportReviewRequest) -> float:
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

    # 최대 거래금액이 평균의 5배 초과
    if req.avg_amount > 0 and req.max_amount / req.avg_amount > 5:
        score += 10

    # 신고 횟수 반영: 건당 5점, 최대 20점
    score += min(req.total_report_count * 5, 20)

    return min(score, 100.0)


def predict_report_review(req: ReportReviewRequest) -> ReportReviewResponse:
    # 모듈을 통해 접근해야 lifespan 이후 로드된 모델 객체를 참조함
    if not risk_service.is_loaded():
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
    ml_score   = float(risk_service._risk_model.predict(features)[0])
    rule_score = _rule_score(req)
    risk_score = round(max(0.0, min(100.0, 0.4 * rule_score + 0.6 * ml_score)), 2)
    confidence = round(risk_score / 100.0, 4)

    # 판단 기준
    if risk_score >= 70 and req.total_report_count >= 2:
        decision = 'approved'
        reason   = (
            f'리스크 스코어 {risk_score}점, 신고 건수 {req.total_report_count}건으로 '
            '블랙리스트 등록을 승인합니다.'
        )
    elif risk_score <= 30 and req.total_report_count <= 1:
        decision   = 'rejected'
        confidence = round((100.0 - risk_score) / 100.0, 4)
        reason     = (
            f'리스크 스코어 {risk_score}점, 신고 건수 {req.total_report_count}건으로 '
            '정상 계좌로 판단합니다.'
        )
    else:
        decision = 'escalated'
        reason   = (
            f'리스크 스코어 {risk_score}점으로 명확한 판단이 어려워 관리자 검토가 필요합니다.'
        )

    return ReportReviewResponse(
        decision=decision,
        confidence=confidence,
        risk_score=risk_score,
        reason=reason,
    )
