from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BlacklistBase(BaseModel):
    account_number: str = Field(..., description="블랙리스트 계좌번호")
    bank_name: str = Field(..., description="은행명")
    account_holder: Optional[str] = Field(None, description="예금주 이름")
    reason: str = Field(..., description="등록 사유")


class BlacklistCreate(BlacklistBase):
    pass


class BlacklistUpdate(BaseModel):
    reason: Optional[str] = None
    report_count: Optional[int] = None


class BlacklistResponse(BlacklistBase):
    id: int
    report_count: int
    registered_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BlacklistCheckResponse(BaseModel):
    is_blacklisted: bool
    reason: Optional[str] = None
    registered_at: Optional[datetime] = None
