from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import (
    get_customer_service,
    get_delivery_service,
    get_order_service,
    get_tenant_context,
    require_customer_or_guest_for_ordering,
)
from app.core.rbac import ADMIN_ROLES, ROLE_CUSTOMER, require_roles
from app.core.tenant import TenantContext, require_admin_tenant
from app.schemas.delivery import DeliveryAssignRequest, DeliveryAssignmentResponse
from app.services.customer_service import CustomerService
from app.services.delivery_service import DeliveryService
from app.schemas.auth import TokenPayload
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderTrackResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    current_user: TokenPayload = Depends(require_customer_or_guest_for_ordering),
    order_service: OrderService = Depends(get_order_service),
    customer_service: CustomerService = Depends(get_customer_service),
) -> OrderResponse:
    profile = customer_service.get_profile_by_user(current_user.username)
    return order_service.create_order(
        payload, customer_id=profile.id, profile_phone=profile.phone
    )


@router.get("/my", response_model=OrderListResponse)
def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    order_service: OrderService = Depends(get_order_service),
    customer_service: CustomerService = Depends(get_customer_service),
) -> OrderListResponse:
    profile = customer_service.get_profile_by_user(current_user.username)
    return order_service.list_orders_by_phone(profile.phone, page, page_size)


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    _: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
    tenant: TenantContext = Depends(get_tenant_context),
    order_service: OrderService = Depends(get_order_service),
) -> OrderListResponse:
    restaurant_id = require_admin_tenant(tenant)
    return order_service.list_orders(page, page_size, status_filter, search, restaurant_id)


@router.get("/track/{order_id}", response_model=OrderTrackResponse)
def track_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
) -> OrderTrackResponse:
    return order_service.track_order(order_id)


@router.get("/{order_pk}", response_model=OrderResponse)
def get_order(
    order_pk: int,
    _: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
    tenant: TenantContext = Depends(get_tenant_context),
    order_service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return order_service.get_order(order_pk, require_admin_tenant(tenant))


@router.put("/{order_pk}/status", response_model=OrderResponse)
def update_order_status(
    order_pk: int,
    payload: OrderStatusUpdate,
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
    tenant: TenantContext = Depends(get_tenant_context),
    order_service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    restaurant_id = require_admin_tenant(tenant)
    return order_service.update_status(
        order_pk, payload, user=current_user.username, restaurant_id=restaurant_id
    )


@router.put("/{order_pk}/assign-delivery", response_model=DeliveryAssignmentResponse)
def assign_delivery(
    order_pk: int,
    payload: DeliveryAssignRequest,
    _: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
    tenant: TenantContext = Depends(get_tenant_context),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentResponse:
    return delivery_service.assign_order(order_pk, payload, require_admin_tenant(tenant))
