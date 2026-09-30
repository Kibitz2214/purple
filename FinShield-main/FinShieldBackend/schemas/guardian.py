from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GuardianBase(BaseModel):
    guardian_id: int


class GuardianCreate(GuardianBase):
    pass


class GuardianUpdate(BaseModel):
    approval_status: ApprovalStatus


class GuardianResponse(BaseModel):
    id: int
    user_id: int
    guardian_id: int
    approval_status: ApprovalStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuardianUserDetail(BaseModel):
    id: int
    username: str
    phone: str


class GuardianRelationInfo(GuardianResponse):
    guardian_info: Optional[GuardianUserDetail] = None
    user_info: Optional[GuardianUserDetail] = None

    model_config = ConfigDict(from_attributes=True)
