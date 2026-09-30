from pydantic import BaseModel, Field


class FraudRequest(BaseModel):
    transaction_id: int
    amount: float = Field(..., ge=0)
    sender_account_id: int
    receiver_account_id: int
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_blacklisted: bool
    is_new_receiver: bool
    sender_tx_count_7d: int = Field(..., ge=0)
    sender_avg_amount_30d: float = Field(..., ge=0)
    sender_balance_before: float = Field(..., ge=0)
    receiver_risk_score: float = 0.0


class FraudResponse(BaseModel):
    transaction_id: int
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    top_reasons: list[str]
    recommendation: str
