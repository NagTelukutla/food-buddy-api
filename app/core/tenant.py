"""Multi-tenant context and access guards."""

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status

from app.core.rbac import ROLE_ADMIN, ROLE_DRIVER, ROLE_PLATFORM, normalize_role


@dataclass(frozen=True)
class TenantContext:
    username: str
    role: str
    restaurant_id: Optional[int] = None
    branch_id: Optional[int] = None

    @property
    def is_platform(self) -> bool:
        return self.role == ROLE_PLATFORM

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_driver(self) -> bool:
        return self.role == ROLE_DRIVER


def build_tenant_context(
    username: str,
    role: str,
    restaurant_id: Optional[int] = None,
    branch_id: Optional[int] = None,
) -> TenantContext:
    normalized = normalize_role(role)
    return TenantContext(
        username=username,
        role=normalized,
        restaurant_id=restaurant_id,
        branch_id=branch_id,
    )


def require_admin_tenant(tenant: TenantContext) -> int:
    """Return the admin's assigned restaurant ID or raise 403."""
    if tenant.is_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform users must use platform-scoped endpoints",
        )
    if tenant.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant admin access required",
        )
    if not tenant.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No restaurant assigned to this admin account",
        )
    return tenant.restaurant_id


def require_driver_tenant(tenant: TenantContext) -> int:
    if tenant.role != ROLE_DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delivery partner access required",
        )
    if not tenant.restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No restaurant assigned to this driver account",
        )
    return tenant.restaurant_id


def assert_restaurant_access(tenant: TenantContext, restaurant_id: int) -> None:
    """Reject cross-tenant access. Platform (Super Admin) may access any restaurant."""
    if tenant.is_platform:
        return
    if tenant.restaurant_id is None or tenant.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this restaurant",
        )


def resolve_requested_restaurant_id(
    tenant: TenantContext,
    requested: Optional[int] = None,
) -> int:
    """
    Never trust client-supplied restaurant IDs for admin/driver.
    Super Admin may pass an explicit restaurant_id.
    """
    if tenant.is_platform:
        if requested is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="restaurant_id is required",
            )
        return requested

    effective = tenant.restaurant_id
    if tenant.role == ROLE_ADMIN:
        effective = require_admin_tenant(tenant)
    elif tenant.role == ROLE_DRIVER:
        effective = require_driver_tenant(tenant)

    if requested is not None and requested != effective:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another restaurant's data",
        )
    return effective
