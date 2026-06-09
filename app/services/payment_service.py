from typing import Optional

import razorpay
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.payment import (
    CheckoutPaymentRequest,
    CheckoutPaymentResponse,
    PaymentFailedRequest,
    PaymentListResponse,
    PaymentRecordResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    RazorpayCheckoutDetails,
    RazorpayConfigResponse,
)
from app.services.order_service import OrderService


class PaymentService:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        order_repository: OrderRepository,
        order_service: OrderService,
        audit_repository: AuditLogRepository,
    ):
        self.payment_repository = payment_repository
        self.order_repository = order_repository
        self.order_service = order_service
        self.audit_repository = audit_repository
        self.settings = get_settings()
        self._client: Optional[razorpay.Client] = None

    def _get_client(self) -> razorpay.Client:
        if not self.settings.razorpay_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
            )
        if self._client is None:
            self._client = razorpay.Client(
                auth=(self.settings.razorpay_key_id, self.settings.razorpay_key_secret)
            )
        return self._client

    def get_config(self) -> RazorpayConfigResponse:
        return RazorpayConfigResponse(
            key_id=self.settings.razorpay_key_id,
            currency=self.settings.razorpay_currency,
            company_name=self.settings.razorpay_display_name,
            enabled=self.settings.razorpay_enabled,
        )

    def _record_to_response(self, record: dict) -> PaymentRecordResponse:
        return PaymentRecordResponse(
            id=record["id"],
            restaurant_order_id=record["restaurant_order_id"],
            restaurant_order_pk=record["restaurant_order_pk"],
            razorpay_order_id=record.get("razorpay_order_id"),
            razorpay_payment_id=record.get("razorpay_payment_id"),
            amount=record["amount"],
            amount_paise=record["amount_paise"],
            currency=record["currency"],
            status=record["status"],
            method=record.get("method"),
            failure_reason=record.get("failure_reason"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            customer_name=record["customer_name"],
            phone=record["phone"],
        )

    def initiate_checkout(
        self,
        payload: CheckoutPaymentRequest,
        customer_id: Optional[int] = None,
        profile_phone: Optional[str] = None,
    ) -> CheckoutPaymentResponse:
        order_response = self.order_service.create_order(
            payload.order,
            payment_status="pending",
            order_status="Pending",
            customer_id=customer_id,
            profile_phone=profile_phone,
        )
        amount_paise = int(round(order_response.total * 100))
        if amount_paise < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order amount must be at least ₹1.00",
            )

        client = self._get_client()
        receipt = order_response.order_id
        order_payload: dict = {
            "amount": amount_paise,
            "currency": self.settings.razorpay_currency,
            "receipt": receipt,
            "payment_capture": 1,
            "notes": {
                "restaurant_order_id": order_response.order_id,
                "customer_name": order_response.customer_name,
                "phone": order_response.phone,
            },
        }
        if self.settings.razorpay_checkout_config_id:
            order_payload["checkout_config_id"] = self.settings.razorpay_checkout_config_id
        razorpay_order = client.order.create(order_payload)

        payment_record = self.payment_repository.create(
            {
                "restaurant_order_id": order_response.order_id,
                "restaurant_order_pk": order_response.id,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_payment_id": None,
                "amount": order_response.total,
                "amount_paise": amount_paise,
                "currency": self.settings.razorpay_currency,
                "status": "created",
                "method": None,
                "failure_reason": None,
                "customer_name": order_response.customer_name,
                "phone": order_response.phone,
            }
        )

        self.order_repository.update_payment(
            order_response.id,
            payment_status="pending",
            razorpay_order_id=razorpay_order["id"],
        )

        self.audit_repository.create(
            action="PAYMENT_INIT",
            entity_type="payment",
            entity_id=payment_record["id"],
            user="customer",
            details=f"Razorpay order {razorpay_order['id']} for {order_response.order_id}",
        )

        refreshed_order = self.order_service.get_order(order_response.id)
        return CheckoutPaymentResponse(
            order=refreshed_order,
            payment_record_id=payment_record["id"],
            razorpay=RazorpayCheckoutDetails(
                key_id=self.settings.razorpay_key_id,
                razorpay_order_id=razorpay_order["id"],
                amount=amount_paise,
                currency=self.settings.razorpay_currency,
                company_name=self.settings.razorpay_display_name,
                customer_name=order_response.customer_name,
                customer_phone=order_response.phone,
                description=f"Order {order_response.order_id}",
                checkout_config_id=self.settings.razorpay_checkout_config_id or None,
            ),
        )

    def verify_payment(self, payload: PaymentVerifyRequest) -> PaymentVerifyResponse:
        payment_record = self.payment_repository.get_by_razorpay_order_id(payload.razorpay_order_id)
        if not payment_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

        if payment_record["restaurant_order_id"] != payload.restaurant_order_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order mismatch")

        if payment_record.get("status") == "paid":
            order = self.order_service.get_order_by_public_id(payload.restaurant_order_id)
            return PaymentVerifyResponse(
                success=True,
                message="Payment already verified",
                payment=self._record_to_response(payment_record),
                order=order,
            )

        client = self._get_client()
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": payload.razorpay_order_id,
                    "razorpay_payment_id": payload.razorpay_payment_id,
                    "razorpay_signature": payload.razorpay_signature,
                }
            )
        except razorpay.errors.SignatureVerificationError as exc:
            self.payment_repository.update(
                payment_record["id"],
                {
                    "status": "failed",
                    "failure_reason": "signature_verification_failed",
                    "razorpay_payment_id": payload.razorpay_payment_id,
                },
            )
            order = self.order_repository.get_by_order_id(payload.restaurant_order_id)
            if order:
                self.order_repository.update_payment(
                    order.id, payment_status="failed", order_status="Cancelled"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed",
            ) from exc

        payment_method = None
        try:
            rp_payment = client.payment.fetch(payload.razorpay_payment_id)
            payment_method = rp_payment.get("method")
        except Exception:
            payment_method = None

        updated_record = self.payment_repository.update(
            payment_record["id"],
            {
                "status": "paid",
                "razorpay_payment_id": payload.razorpay_payment_id,
                "method": payment_method,
                "failure_reason": None,
            },
        )

        order = self.order_repository.get_by_order_id(payload.restaurant_order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        self.order_repository.update_payment(
            order.id,
            payment_status="paid",
            razorpay_order_id=payload.razorpay_order_id,
            order_status="Pending",
        )

        self.audit_repository.create(
            action="PAYMENT_SUCCESS",
            entity_type="payment",
            entity_id=payment_record["id"],
            user="customer",
            details=f"Paid via {payment_method or 'razorpay'} for {payload.restaurant_order_id}",
        )

        order_response = self.order_service.get_order(order.id)
        return PaymentVerifyResponse(
            success=True,
            message="Payment successful",
            payment=self._record_to_response(updated_record),
            order=order_response,
        )

    def mark_failed(self, payload: PaymentFailedRequest) -> PaymentRecordResponse:
        payment_record = self.payment_repository.get_by_restaurant_order_id(
            payload.restaurant_order_id
        )
        if not payment_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

        status_value = "cancelled" if "cancel" in payload.reason.lower() else "failed"
        updated = self.payment_repository.update(
            payment_record["id"],
            {
                "status": status_value,
                "failure_reason": payload.reason,
            },
        )

        order = self.order_repository.get_by_order_id(payload.restaurant_order_id)
        if order:
            self.order_repository.update_payment(
                order.id,
                payment_status=status_value,
                order_status="Cancelled" if status_value == "cancelled" else order.status,
            )

        self.audit_repository.create(
            action="PAYMENT_FAILED",
            entity_type="payment",
            entity_id=payment_record["id"],
            user="customer",
            details=payload.reason,
        )
        return self._record_to_response(updated)

    def list_payments(self, limit: int = 50) -> PaymentListResponse:
        records = self.payment_repository.list_all(limit)
        items = [self._record_to_response(r) for r in records]
        return PaymentListResponse(items=items, total=len(items))
