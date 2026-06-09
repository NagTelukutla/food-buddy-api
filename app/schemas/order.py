from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.phone import is_valid_phone

OrderStatus = Literal[
    "Pending",
    "Accepted",
    "Driver Assigned",
    "Prepared",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]
OrderType = Literal["Dine In", "Pickup", "Delivery"]


class OrderItemCreate(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20)
    table_number: Optional[str] = Field(None, max_length=20)
    order_type: OrderType
    delivery_address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    items: List[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not is_valid_phone(value):
            raise ValueError("Invalid phone number format")
        return value


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    name: str
    price: float
    quantity: int
    line_total: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    order_id: str
    customer_name: str
    phone: str
    table_number: Optional[str]
    order_type: str
    notes: Optional[str]
    status: str
    payment_status: str = "unpaid"
    razorpay_order_id: Optional[str] = None
    subtotal: float
    tax: float
    total: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    assigned_driver_name: Optional[str] = None
    assigned_driver_phone: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrderTrackResponse(BaseModel):
    order_id: str
    customer_name: str
    status: str
    order_type: str
    total: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    delivery_status: Optional[str] = None
    live_tracking_enabled: bool = False


class OrderAssignDelivery(BaseModel):
    delivery_partner_id: int
