from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_delivery_service, get_tenant_context, get_user_repository
from app.core.rbac import (
    ROLE_ADMIN,
    ROLE_DRIVER,
    require_roles,
)
from app.core.tenant import TenantContext, require_admin_tenant, resolve_requested_restaurant_id
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPayload
from app.schemas.delivery import (
    DeliveryAcceptRequest,
    DeliveryAssignmentDetailResponse,
    DeliveryAssignmentListResponse,
    DeliveryLiveTrackResponse,
    DeliveryPartnerCreate,
    DeliveryPartnerResponse,
    DeliveryPartnerUpdate,
    DeliveryReportResponse,
    DeliveryStatusByOrderRequest,
    DeliveryStatusUpdate,
    DriverLiveLocation,
    DriverLocationUpdate,
)
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/api/delivery", tags=["Delivery"])


@router.get("/partners", response_model=List[DeliveryPartnerResponse])
def list_partners(
    restaurant_id: Optional[int] = Query(None, ge=1),
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: DeliveryService = Depends(get_delivery_service),
) -> List[DeliveryPartnerResponse]:
    rid = resolve_requested_restaurant_id(tenant, restaurant_id)
    return service.list_partners(rid)


@router.post("/partners", response_model=DeliveryPartnerResponse, status_code=status.HTTP_201_CREATED)
def create_partner(
    payload: DeliveryPartnerCreate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryPartnerResponse:
    return service.create_partner(payload, restaurant_id=require_admin_tenant(tenant))


@router.put("/partners/{partner_id}", response_model=DeliveryPartnerResponse)
def update_partner(
    partner_id: int,
    payload: DeliveryPartnerUpdate,
    current_user: TokenPayload = Depends(require_roles(ROLE_ADMIN, ROLE_DRIVER)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryPartnerResponse:
    restaurant_id = require_admin_tenant(tenant) if tenant.is_admin else None
    return service.update_partner(partner_id, payload, restaurant_id=restaurant_id)


@router.get("/live-track/{order_id}", response_model=DeliveryLiveTrackResponse)
def live_track_order(
    order_id: str,
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryLiveTrackResponse:
    """Public live driver map data for customers (order ID is the access token)."""
    return service.get_live_track(order_id)


@router.post("/location", response_model=DriverLiveLocation)
def update_driver_location(
    payload: DriverLocationUpdate,
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DriverLiveLocation:
    user = user_repo.get_by_username(current_user.username)
    return service.update_driver_location(user["id"], payload)


@router.get("/report", response_model=DeliveryReportResponse)
def get_delivery_report(
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryReportResponse:
    user = user_repo.get_by_username(current_user.username)
    if not user:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return service.get_partner_report(user)


@router.get("/assignments", response_model=DeliveryAssignmentListResponse)
def list_assignments(
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentListResponse:
    user = user_repo.get_by_username(current_user.username)
    if not user:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return service.list_assignments_for_partner(user)


@router.post("/assignments/accept", response_model=DeliveryAssignmentDetailResponse)
def accept_assignment_post(
    payload: DeliveryAcceptRequest,
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentDetailResponse:
    user = user_repo.get_by_username(current_user.username)
    return service.accept_assignment(payload.order_id, user)


@router.put("/assignments/{order_id}/accept", response_model=DeliveryAssignmentDetailResponse)
def accept_assignment(
    order_id: str,
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentDetailResponse:
    user = user_repo.get_by_username(current_user.username)
    return service.accept_assignment(order_id, user)


@router.post("/assignments/update-status", response_model=DeliveryAssignmentDetailResponse)
def update_assignment_status_post(
    payload: DeliveryStatusByOrderRequest,
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentDetailResponse:
    user = user_repo.get_by_username(current_user.username)
    status_payload = DeliveryStatusUpdate(delivery_status=payload.delivery_status)
    return service.update_delivery_status(payload.order_id, status_payload, user_id=user["id"])


@router.put("/assignments/{order_id}/status", response_model=DeliveryAssignmentDetailResponse)
def update_assignment_status(
    order_id: str,
    payload: DeliveryStatusUpdate,
    current_user: TokenPayload = Depends(require_roles(ROLE_DRIVER)),
    user_repo: UserRepository = Depends(get_user_repository),
    service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryAssignmentDetailResponse:
    user = user_repo.get_by_username(current_user.username)
    return service.update_delivery_status(order_id, payload, user_id=user["id"])
