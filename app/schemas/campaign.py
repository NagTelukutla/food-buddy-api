from typing import List, Literal, Optional

from pydantic import BaseModel, Field

DiscountType = Literal["percentage", "flat"]
TargetSegment = Literal["all", "new_customers", "returning", "loyalty_tier", "manual"]
CampaignStatus = Literal["draft", "active", "paused", "completed"]


class CampaignCreate(BaseModel):
    restaurant_id: int
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: float = Field(..., gt=0)
    promo_code: Optional[str] = None
    target_segment: TargetSegment = "all"
    target_customer_ids: List[int] = Field(default_factory=list)
    min_order_amount: Optional[float] = None
    start_date: str
    end_date: str
    status: CampaignStatus = "draft"


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(None, gt=0)
    promo_code: Optional[str] = None
    target_segment: Optional[TargetSegment] = None
    target_customer_ids: Optional[List[int]] = None
    min_order_amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(BaseModel):
    id: int
    restaurant_id: int
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    promo_code: Optional[str] = None
    target_segment: str
    target_customer_ids: List[int] = Field(default_factory=list)
    min_order_amount: Optional[float] = None
    start_date: str
    end_date: str
    status: str
    created_at: str
    updated_at: str


class CampaignListResponse(BaseModel):
    items: List[CampaignResponse]
