from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.rbac import NON_CUSTOMER_ORDER_ROLES, ROLE_CUSTOMER, normalize_role
from app.core.tenant import TenantContext, build_tenant_context
from app.core.security import decode_token
from app.database.sqlite import get_db_session
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.loyalty_repository import LoyaltyRepository
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_metadata_repository import OrderMetadataRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPayload
from app.services.auth_service import AuthService
from app.services.campaign_service import CampaignService
from app.services.customer_service import CustomerService
from app.services.dashboard_service import DashboardService
from app.services.delivery_service import DeliveryService
from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.platform_service import PlatformService
from app.services.restaurant_service import RestaurantService
from app.services.review_service import ReviewService
from app.services.user_service import UserService

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_menu_repository() -> MenuRepository:
    return MenuRepository()


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_settings_repository() -> SettingsRepository:
    return SettingsRepository()


def get_restaurant_repository() -> RestaurantRepository:
    return RestaurantRepository()


def get_branch_repository() -> BranchRepository:
    return BranchRepository()


def get_customer_repository() -> CustomerRepository:
    return CustomerRepository()


def get_delivery_repository() -> DeliveryRepository:
    return DeliveryRepository()


def get_loyalty_repository() -> LoyaltyRepository:
    return LoyaltyRepository()


def get_campaign_repository() -> CampaignRepository:
    return CampaignRepository()


def get_review_repository() -> ReviewRepository:
    return ReviewRepository()


def get_platform_settings_repository() -> PlatformSettingsRepository:
    return PlatformSettingsRepository()


def get_order_metadata_repository() -> OrderMetadataRepository:
    return OrderMetadataRepository()


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)


def get_audit_log_repository(db: Session = Depends(get_db)) -> AuditLogRepository:
    return AuditLogRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> AuthService:
    return AuthService(user_repo, customer_repo)


def get_menu_service(
    menu_repo: MenuRepository = Depends(get_menu_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> MenuService:
    return MenuService(menu_repo, audit_repo)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
    order_metadata_repo: OrderMetadataRepository = Depends(get_order_metadata_repository),
    delivery_repo: DeliveryRepository = Depends(get_delivery_repository),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository),
) -> OrderService:
    return OrderService(
        order_repo,
        menu_repo,
        audit_repo,
        order_metadata_repo,
        delivery_repo,
        restaurant_repo,
    )


def get_dashboard_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    menu_repo: MenuRepository = Depends(get_menu_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    order_metadata_repo: OrderMetadataRepository = Depends(get_order_metadata_repository),
) -> DashboardService:
    return DashboardService(order_repo, menu_repo, customer_repo, order_metadata_repo)


def get_payment_repository() -> PaymentRepository:
    return PaymentRepository()


def get_payment_service(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    order_service: OrderService = Depends(get_order_service),
    audit_repo: AuditLogRepository = Depends(get_audit_log_repository),
) -> PaymentService:
    return PaymentService(payment_repo, order_repo, order_service, audit_repo)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    branch_repo: BranchRepository = Depends(get_branch_repository),
) -> UserService:
    return UserService(user_repo, branch_repo)


def get_restaurant_service(
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository),
    branch_repo: BranchRepository = Depends(get_branch_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> RestaurantService:
    return RestaurantService(restaurant_repo, branch_repo, user_repo)


def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    loyalty_repo: LoyaltyRepository = Depends(get_loyalty_repository),
) -> CustomerService:
    return CustomerService(customer_repo, user_repo, loyalty_repo)


def get_delivery_service(
    delivery_repo: DeliveryRepository = Depends(get_delivery_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    order_metadata_repo: OrderMetadataRepository = Depends(get_order_metadata_repository),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository),
) -> DeliveryService:
    return DeliveryService(delivery_repo, order_repo, order_metadata_repo, restaurant_repo)


def get_campaign_service(
    campaign_repo: CampaignRepository = Depends(get_campaign_repository),
) -> CampaignService:
    return CampaignService(campaign_repo)


def get_review_service(
    review_repo: ReviewRepository = Depends(get_review_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> ReviewService:
    return ReviewService(review_repo, order_repo, user_repo, customer_repo)


def get_platform_service(
    platform_repo: PlatformSettingsRepository = Depends(get_platform_settings_repository),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository),
    order_repo: OrderRepository = Depends(get_order_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> PlatformService:
    return PlatformService(platform_repo, restaurant_repo, order_repo, customer_repo)


def get_optional_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    if credentials is None or not credentials.credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None
    username = payload.get("sub")
    if not username:
        return None
    role = normalize_role(payload.get("role", ROLE_CUSTOMER))
    return TokenPayload(username=username, role=role)


def require_customer_or_guest_for_ordering(
    current_user: Optional[TokenPayload] = Depends(get_optional_user_payload),
) -> TokenPayload:
    """Customer login required to place orders; non-customer roles are rejected."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in as a customer to place orders.",
        )
    role = normalize_role(current_user.role)
    if role in NON_CUSTOMER_ORDER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can place orders. Please sign out from your admin account.",
        )
    if role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can place orders.",
        )
    return current_user


def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> TokenPayload:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    role = normalize_role(user.get("role", payload.get("role", "admin")))
    return TokenPayload(
        username=username,
        role=role,
        restaurant_id=user.get("restaurant_id"),
        branch_id=user.get("branch_id"),
    )


def get_tenant_context(
    current_user: TokenPayload = Depends(get_current_user_payload),
) -> TenantContext:
    return build_tenant_context(
        username=current_user.username,
        role=current_user.role,
        restaurant_id=current_user.restaurant_id,
        branch_id=current_user.branch_id,
    )


def get_optional_tenant_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Optional[TenantContext]:
    if credentials is None or not credentials.credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = user_repo.get_by_username(username)
    if not user or not user.get("is_active", True):
        return None
    role = normalize_role(user.get("role", payload.get("role", "admin")))
    return build_tenant_context(
        username=username,
        role=role,
        restaurant_id=user.get("restaurant_id"),
        branch_id=user.get("branch_id"),
    )
