from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.settings import HeroSlide


class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    tagline: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    hero_image: Optional[str] = None
    hero_slides: List[HeroSlide] = Field(default_factory=list)
    email: str
    phone: str
    address: Optional[str] = None
    cuisine_type: Optional[str] = None
    working_hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RestaurantCreate(RestaurantBase):
    owner_user_id: int
    slug: Optional[str] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    hero_image: Optional[str] = None
    hero_slides: Optional[List[HeroSlide]] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    cuisine_type: Optional[str] = None
    working_hours: Optional[str] = None
    is_active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RestaurantResponse(RestaurantBase):
    id: int
    slug: str
    owner_user_id: int
    is_active: bool = True
    created_at: str
    updated_at: str


class RestaurantListResponse(BaseModel):
    items: List[RestaurantResponse]
    total: int
