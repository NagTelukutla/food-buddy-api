from typing import List, Optional

from pydantic import BaseModel, Field


class BranchBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class BranchCreate(BranchBase):
    restaurant_id: int


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    working_hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    restaurant_id: int
    is_active: bool = True
    created_at: str
    updated_at: str


class BranchListResponse(BaseModel):
    items: List[BranchResponse]
