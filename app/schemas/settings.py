from typing import List, Optional

from pydantic import BaseModel, Field


class HeroSlide(BaseModel):
    title: str
    subtitle: str
    cta_label: str = "Order Now"
    cta_link: str = "/menu"
    accent: Optional[str] = None
    image: str = "/slides/slide-1.svg"


class RestaurantSettings(BaseModel):
    name: str
    tagline: str
    logo: str
    hero_image: str
    about: str
    address: str
    phone: str
    email: str
    working_hours: str
    featured_dish_ids: list[int] = Field(default_factory=list)
    hero_slides: List[HeroSlide] = Field(default_factory=list)
