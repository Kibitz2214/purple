from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    account_number: str = Field(..., description="계좌번호 (하이픈 제외)")
    bank_name: str = Field(..., description="은행명")
    account_name: str = Field(..., description="계좌 별칭 (예: 주거래, 비상금)")


_MAX_BALANCE = 9_999_999_999_999.99


class AccountCreate(AccountBase):
    initial_balance: float = Field(default=0, ge=0, le=_MAX_BALANCE, description="초기 잔액")
    account_type: str = Field(default="checking", description="계좌 유형 (예: checking, savings)")
    status: str = Field(default="active", description="계좌 상태 (예: active, inactive, suspended)")


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    is_active: Optional[bool] = None
    # 보안상 계좌번호나 은행명은 업데이트 대상에서 제외하는 것이 일반적임


class AccountResponse(AccountBase):
    id: int
    user_id: int
    balance: float
    account_type: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountBalanceUpdate(BaseModel):
    amount: float = Field(..., le=_MAX_BALANCE, description="변동 금액 (입금: +, 출금: -)")
