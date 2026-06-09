from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.phone import is_valid_phone

UserRole = Literal["customer", "admin", "driver", "platform"]


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value and not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Optional[str] = None
    is_customer: bool = False
    customer_id: Optional[int] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    username: str
    role: str = "admin"
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    phone: Optional[str] = None
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_customer: bool = False
    customer_id: Optional[int] = None
