from pydantic import BaseModel, Field


class RiskRequest(BaseModel):
    user_id: int
    total_tx_count: int = Field(..., ge=0)
    avg_amount: float = Field(..., ge=0)
    max_amount: float = Field(..., ge=0)
    fraud_flag_count: int = Field(..., ge=0)
    blacklist_hit_count: int = Field(..., ge=0)
    account_age_days: int = Field(..., ge=0)
    own_blacklist_count: int = Field(0, ge=0)


class RiskResponse(BaseModel):
    user_id: int
    risk_score: float
    trust_score: float
    risk_grade: str
    top_reasons: list[str]
