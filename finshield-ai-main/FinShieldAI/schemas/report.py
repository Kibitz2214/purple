from pydantic import BaseModel


class ReportReviewRequest(BaseModel):
    account_number: str
    report_id: int
    report_content: str
    total_report_count: int
    receiver_tx_count: int
    receiver_total_amount: float
    total_tx_count: int
    avg_amount: float
    max_amount: float
    fraud_flag_count: int
    blacklist_hit_count: int
    account_age_days: int


class ReportReviewResponse(BaseModel):
    decision: str       # 'approved' | 'rejected' | 'escalated'
    confidence: float   # 0~1 (AI 확신도)
    risk_score: float
    reason: str
