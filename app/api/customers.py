from fastapi import APIRouter, Depends

from app.core.deps import get_customer_service, get_order_service
from app.core.rbac import ROLE_CUSTOMER, require_roles
from app.schemas.auth import TokenPayload
from app.schemas.customer import CustomerResponse, CustomerUpdate, LoyaltySummaryResponse
from app.schemas.order import OrderListResponse
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("/me", response_model=CustomerResponse)
def get_my_profile(
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return service.get_profile_by_user(current_user.username)


@router.put("/me", response_model=CustomerResponse)
def update_my_profile(
    payload: CustomerUpdate,
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    return service.update_profile(current_user.username, payload)


@router.get("/me/orders", response_model=OrderListResponse)
def get_my_orders(
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    order_service: OrderService = Depends(get_order_service),
    service: CustomerService = Depends(get_customer_service),
) -> OrderListResponse:
    profile = service.get_profile_by_user(current_user.username)
    return order_service.list_orders_by_phone(profile.phone, page=1, page_size=50)


@router.get("/me/loyalty", response_model=LoyaltySummaryResponse)
def get_my_loyalty(
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    service: CustomerService = Depends(get_customer_service),
) -> LoyaltySummaryResponse:
    return service.get_loyalty(current_user.username)
