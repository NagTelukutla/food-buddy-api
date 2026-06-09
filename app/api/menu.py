from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_menu_service, get_optional_tenant_context, get_tenant_context
from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.tenant import TenantContext, require_admin_tenant
from app.schemas.auth import TokenPayload
from app.schemas.menu import MenuItemCreate, MenuItemResponse, MenuItemUpdate, MenuListResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/api/menu", tags=["Menu"])


@router.get("", response_model=MenuListResponse)
def list_menu(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    available_only: bool = Query(False),
    tenant: Optional[TenantContext] = Depends(get_optional_tenant_context),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuListResponse:
    restaurant_id = require_admin_tenant(tenant) if tenant and tenant.is_admin else None
    return menu_service.list_menu(search, category, available_only, restaurant_id)


@router.get("/{item_id}", response_model=MenuItemResponse)
def get_menu_item(
    item_id: int,
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemResponse:
    return menu_service.get_item(item_id)


@router.post("", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    payload: MenuItemCreate,
    current_user: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemResponse:
    return menu_service.create_item(
        payload, user=current_user.username, restaurant_id=require_admin_tenant(tenant)
    )


@router.put("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    current_user: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    menu_service: MenuService = Depends(get_menu_service),
) -> MenuItemResponse:
    rid = require_admin_tenant(tenant)
    return menu_service.update_item(item_id, payload, user=current_user.username, restaurant_id=rid)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    menu_service: MenuService = Depends(get_menu_service),
) -> None:
    menu_service.delete_item(
        item_id, user=current_user.username, restaurant_id=require_admin_tenant(tenant)
    )
