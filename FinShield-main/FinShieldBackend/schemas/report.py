from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ReportBase(BaseModel):
    account_number: str = Field(..., description="신고 대상 계좌번호")
    bank_name: str = Field(..., description="은행명")
    account_holder: Optional[str] = Field(None, description="예금주 이름")
    content: str = Field(..., description="신고 내용")


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    admin_note: Optional[str] = None


class ReportResponse(ReportBase):
    id: int
    reporter_id: int
    status: ReportStatus
    admin_note: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
