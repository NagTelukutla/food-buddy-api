from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = [
    "Starters",
    "Soups",
    "Main Course",
    "Biryani",
    "Beverages",
    "Desserts",
]


class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(..., min_length=2, max_length=500)
    price: float = Field(..., gt=0)
    image: str = Field(default="default.jpg", max_length=200)
    available: bool = True
    category: str
    restaurant_id: Optional[int] = 1

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return value


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = Field(None, min_length=2, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    image: Optional[str] = Field(None, max_length=200)
    available: Optional[bool] = None
    category: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(VALID_CATEGORIES)}")
        return value


class MenuItemResponse(MenuItemBase):
    id: int


class MenuListResponse(BaseModel):
    items: List[MenuItemResponse]
    categories: List[str]
