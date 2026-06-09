import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.phone import is_valid_phone

_USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,49}$")

AssignableRole = Literal["customer", "admin", "driver", "platform"]


class UserAdminResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    phone: Optional[str] = None
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserListResponse(BaseModel):
    items: List[UserAdminResponse]
    total: int


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)
    role: AssignableRole
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "")
        if not _USERNAME_RE.match(normalized):
            raise ValueError(
                "Username must be 3–50 characters: lowercase letters, numbers, dots, dashes, or underscores (no spaces)"
            )
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value and not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[str] = Field(None, min_length=5, max_length=120)
    role: Optional[AssignableRole] = None
    phone: Optional[str] = None
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value and not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class RestaurantOnboardRequest(BaseModel):
    restaurant_name: str = Field(..., min_length=2, max_length=120)
    email: str
    phone: str
    address: str
    tagline: Optional[str] = None
    cuisine_type: Optional[str] = None
    working_hours: Optional[str] = None
    owner_username: str = Field(..., min_length=3, max_length=50)
    owner_email: str
    owner_password: str = Field(..., min_length=6, max_length=128)
    owner_full_name: str = Field(..., min_length=2, max_length=120)
    owner_phone: Optional[str] = None

    @field_validator("owner_phone")
    @classmethod
    def validate_owner_phone(cls, value: Optional[str]) -> Optional[str]:
        if value and not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class RestaurantOnboardResponse(BaseModel):
    restaurant_id: int
    branch_id: int
    owner_user_id: int
    restaurant_name: str
    owner_username: str
    message: str = "Restaurant onboarded successfully"


class RestaurantAdminOption(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    phone: Optional[str] = None
    is_mapped: bool = False
    is_active: bool = True


class RestaurantAdminListResponse(BaseModel):
    restaurant_id: int
    restaurant_name: str
    mapped_admin_ids: List[int]
    items: List[RestaurantAdminOption]


class RestaurantAdminMapRequest(BaseModel):
    admin_ids: List[int] = Field(default_factory=list)
