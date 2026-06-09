from fastapi import APIRouter, Depends, Query, status

from app.core.deps import (
    get_customer_service,
    get_payment_service,
    require_customer_or_guest_for_ordering,
)
from app.core.rbac import ADMIN_ROLES, require_roles
from app.schemas.auth import TokenPayload
from app.schemas.payment import (
    CheckoutPaymentRequest,
    CheckoutPaymentResponse,
    PaymentFailedRequest,
    PaymentListResponse,
    PaymentRecordResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    RazorpayConfigResponse,
)
from app.services.customer_service import CustomerService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("/config", response_model=RazorpayConfigResponse)
def get_razorpay_config(
    payment_service: PaymentService = Depends(get_payment_service),
) -> RazorpayConfigResponse:
    """Public Razorpay key for frontend Checkout (never expose secret)."""
    return payment_service.get_config()


@router.post("/checkout", response_model=CheckoutPaymentResponse, status_code=status.HTTP_201_CREATED)
def checkout_with_payment(
    payload: CheckoutPaymentRequest,
    current_user: TokenPayload = Depends(require_customer_or_guest_for_ordering),
    payment_service: PaymentService = Depends(get_payment_service),
    customer_service: CustomerService = Depends(get_customer_service),
) -> CheckoutPaymentResponse:
    """
    Create restaurant order + Razorpay order.
    Client opens Razorpay Checkout (UPI, cards, netbanking, wallets).
    """
    profile = customer_service.get_profile_by_user(current_user.username)
    return payment_service.initiate_checkout(
        payload, customer_id=profile.id, profile_phone=profile.phone
    )


@router.post("/verify", response_model=PaymentVerifyResponse)
def verify_payment(
    payload: PaymentVerifyRequest,
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentVerifyResponse:
    """Verify Razorpay payment signature after successful checkout."""
    return payment_service.verify_payment(payload)


@router.post("/failed", response_model=PaymentRecordResponse)
def mark_payment_failed(
    payload: PaymentFailedRequest,
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentRecordResponse:
    """Record failed or cancelled payment from frontend."""
    return payment_service.mark_failed(payload)


@router.get("", response_model=PaymentListResponse)
def list_payments(
    limit: int = Query(50, ge=1, le=200),
    _: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentListResponse:
    return payment_service.list_payments(limit)
