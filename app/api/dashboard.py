from fastapi import APIRouter, Depends, Query

from app.core.deps import get_dashboard_service, get_tenant_context
from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.tenant import TenantContext, require_admin_tenant
from app.schemas.auth import TokenPayload
from app.schemas.dashboard import (
    CustomerMetricsResponse,
    DashboardOrdersResponse,
    DashboardStats,
    RevenueResponse,
    TopItemStat,
    TopItemsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStats:
    return dashboard_service.get_stats(require_admin_tenant(tenant))


@router.get("/revenue", response_model=RevenueResponse)
def get_revenue_data(
    days: int = Query(7, ge=1, le=30),
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> RevenueResponse:
    return dashboard_service.get_revenue(days, require_admin_tenant(tenant))


@router.get("/orders", response_model=DashboardOrdersResponse)
def get_orders_by_status(
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOrdersResponse:
    return dashboard_service.get_orders_by_status(require_admin_tenant(tenant))


@router.get("/top-items", response_model=TopItemsResponse)
def get_top_items(
    limit: int = Query(10, ge=1, le=50),
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> TopItemsResponse:
    items = dashboard_service.get_top_items(limit, require_admin_tenant(tenant))
    return TopItemsResponse(items=[TopItemStat(**i) for i in items])


@router.get("/customers", response_model=CustomerMetricsResponse)
def get_customer_metrics(
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> CustomerMetricsResponse:
    return CustomerMetricsResponse(
        **dashboard_service.get_customer_metrics(require_admin_tenant(tenant))
    )
