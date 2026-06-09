from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.phone import is_valid_phone


class CustomerAddress(BaseModel):
    label: str
    line1: str
    city: str
    pincode: str
    is_default: bool = False


class CustomerRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    addresses: Optional[List[CustomerAddress]] = None


class CustomerResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: str
    addresses: List[CustomerAddress] = Field(default_factory=list)
    loyalty_points_balance: int = 0
    created_at: str
    updated_at: str


class LoyaltyTransactionResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    order_id: Optional[int] = None
    type: str
    points: int
    balance_after: int
    description: Optional[str] = None
    created_at: str


class LoyaltySummaryResponse(BaseModel):
    balance: int
    transactions: List[LoyaltyTransactionResponse]
