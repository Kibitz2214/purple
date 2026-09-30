from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    phone: Optional[str] = Field(None, pattern=r"^01[0-9]-\d{3,4}-\d{4}$")
    is_vulnerable: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    phone: Optional[str]
    is_vulnerable: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
