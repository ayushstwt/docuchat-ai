import re
from datetime import datetime
from pydantic import EmailStr, Field, field_validator
from app.schemas.common import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain at least one letter and one number")
        return v


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(CamelModel):
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(CamelModel):
    id: int
    email: str
    full_name: str
    created_on: datetime
