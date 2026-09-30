from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["홍길동"])
    email: EmailStr = Field(..., examples=["hong@example.com"])
    password: str = Field(..., min_length=8, examples=["password123"])
    age: int = Field(..., ge=0, le=150, examples=[30])
    phone: Optional[str] = Field(None, pattern=r"^01[0-9]-\d{3,4}-\d{4}$", examples=["010-1234-5678"])
    is_vulnerable: bool = Field(False, description="금융 취약계층 여부 (고령층·미성년자·지적장애인 등)")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["hong@example.com"])
    password: str = Field(..., examples=["password123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int
    phone: Optional[str]
    is_vulnerable: bool

    model_config = {"from_attributes": True}
