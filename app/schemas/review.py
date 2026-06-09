from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_id: str
    restaurant_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    order_id: str
    restaurant_id: int
    customer_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    owner_response: Optional[str] = None
    created_at: str
    updated_at: str


class ReviewRespondRequest(BaseModel):
    owner_response: str = Field(..., min_length=1, max_length=1000)


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
