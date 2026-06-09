from typing import List

from fastapi import APIRouter, Depends, status

from app.core.deps import get_restaurant_service, get_tenant_context
from app.core.rbac import ROLE_ADMIN, ROLE_PLATFORM, require_roles
from app.core.tenant import TenantContext, assert_restaurant_access
from app.schemas.auth import TokenPayload
from app.schemas.branch import BranchCreate, BranchListResponse, BranchResponse
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.schemas.user import (
    RestaurantAdminListResponse,
    RestaurantAdminMapRequest,
    RestaurantOnboardRequest,
    RestaurantOnboardResponse,
)
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/api/restaurants", tags=["Restaurants"])


@router.get("", response_model=List[RestaurantResponse])
def list_restaurants(service: RestaurantService = Depends(get_restaurant_service)) -> List[RestaurantResponse]:
    return service.list_restaurants(active_only=True)


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: int,
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantResponse:
    return service.get_restaurant(restaurant_id)


@router.post("/onboard", response_model=RestaurantOnboardResponse, status_code=status.HTTP_201_CREATED)
def onboard_restaurant(
    payload: RestaurantOnboardRequest,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantOnboardResponse:
    return service.onboard_restaurant(payload)


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    payload: RestaurantCreate,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantResponse:
    return service.create_restaurant(payload)


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN, ROLE_PLATFORM)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantResponse:
    if tenant.is_admin:
        assert_restaurant_access(tenant, restaurant_id)
    return service.update_restaurant(restaurant_id, payload)


@router.get("/{restaurant_id}/admins", response_model=RestaurantAdminListResponse)
def list_restaurant_admins(
    restaurant_id: int,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantAdminListResponse:
    return service.get_restaurant_admins(restaurant_id)


@router.put("/{restaurant_id}/admins", response_model=RestaurantAdminListResponse)
def map_restaurant_admins(
    restaurant_id: int,
    payload: RestaurantAdminMapRequest,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: RestaurantService = Depends(get_restaurant_service),
) -> RestaurantAdminListResponse:
    return service.map_restaurant_admins(restaurant_id, payload)


@router.get("/{restaurant_id}/branches", response_model=BranchListResponse)
def list_branches(
    restaurant_id: int,
    service: RestaurantService = Depends(get_restaurant_service),
) -> BranchListResponse:
    items = service.list_branches(restaurant_id)
    return BranchListResponse(items=items)


@router.post("/{restaurant_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    restaurant_id: int,
    payload: BranchCreate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: RestaurantService = Depends(get_restaurant_service),
) -> BranchResponse:
    assert_restaurant_access(tenant, restaurant_id)
    payload.restaurant_id = restaurant_id
    return service.create_branch(payload)
