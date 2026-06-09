from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.order import OrderCreate, OrderResponse

PaymentStatus = Literal["created", "paid", "failed", "cancelled"]


class RazorpayConfigResponse(BaseModel):
    key_id: str
    currency: str
    company_name: str
    enabled: bool


class CheckoutPaymentRequest(BaseModel):
    order: OrderCreate


class RazorpayCheckoutDetails(BaseModel):
    key_id: str
    razorpay_order_id: str
    amount: int
    currency: str
    company_name: str
    customer_name: str
    customer_phone: str
    description: str
    checkout_config_id: Optional[str] = None


class CheckoutPaymentResponse(BaseModel):
    order: OrderResponse
    payment_record_id: str
    razorpay: RazorpayCheckoutDetails


class PaymentVerifyRequest(BaseModel):
    restaurant_order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentFailedRequest(BaseModel):
    restaurant_order_id: str
    razorpay_order_id: Optional[str] = None
    reason: str = "payment_failed"


class PaymentRecordResponse(BaseModel):
    id: str
    restaurant_order_id: str
    restaurant_order_pk: int
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    amount: float
    amount_paise: int
    currency: str
    status: PaymentStatus
    method: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    customer_name: str
    phone: str


class PaymentVerifyResponse(BaseModel):
    success: bool
    message: str
    payment: PaymentRecordResponse
    order: OrderResponse


class PaymentListResponse(BaseModel):
    items: List[PaymentRecordResponse]
    total: int
