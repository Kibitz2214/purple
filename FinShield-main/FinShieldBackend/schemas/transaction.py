from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    FLAGGED = "flagged"


class TransactionCreate(BaseModel):
    sender_account_id: int = Field(..., description="보내는 계좌 ID")
    receiver_account_number: str = Field(..., description="받는 계좌번호")
    receiver_bank_name: str = Field(..., description="받는 은행명")
    receiver_account_holder: Optional[str] = Field(None, description="받는 예금주 이름")
    amount: float = Field(..., gt=0, le=9_999_999_999_999.99, description="거래 금액")
    memo: Optional[str] = Field(None, max_length=255, description="거래 메모")


class AccountBrief(BaseModel):
    id: int
    account_number: str
    bank_name: str

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: int
    sender_account_id: int
    receiver_account_id: int
    receiver_account: Optional[AccountBrief] = None
    amount: float
    memo: Optional[str]
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
