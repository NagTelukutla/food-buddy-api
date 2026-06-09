from typing import List, Optional

from pydantic import BaseModel, Field


class PlatformSettingsResponse(BaseModel):
    platform_name: str
    default_tax_rate: float
    loyalty_points_per_rupee: Optional[float] = None
    order_id_prefix: str = "ORD"
    featured_restaurant_ids: List[int] = Field(default_factory=list)
    maintenance_mode: bool = False
    updated_at: Optional[str] = None


class PlatformSettingsUpdate(BaseModel):
    platform_name: Optional[str] = None
    default_tax_rate: Optional[float] = None
    loyalty_points_per_rupee: Optional[float] = None
    order_id_prefix: Optional[str] = None
    featured_restaurant_ids: Optional[List[int]] = None
    maintenance_mode: Optional[bool] = None


class PlatformStatsResponse(BaseModel):
    active_restaurants: int
    total_orders: int
    total_gmv: float
    total_customers: int
