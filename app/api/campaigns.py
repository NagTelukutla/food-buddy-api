from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_campaign_service, get_tenant_context
from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.tenant import TenantContext, require_admin_tenant, resolve_requested_restaurant_id
from app.schemas.auth import TokenPayload
from app.schemas.campaign import CampaignCreate, CampaignListResponse, CampaignResponse, CampaignUpdate
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    restaurant_id: Optional[int] = Query(None, ge=1),
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignListResponse:
    rid = resolve_requested_restaurant_id(tenant, restaurant_id)
    return service.list_campaigns(rid)


@router.get("/active", response_model=CampaignListResponse)
def list_active_campaigns(
    restaurant_id: int = Query(..., ge=1),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignListResponse:
    return service.list_active(restaurant_id)


@router.post("", response_model=CampaignResponse)
def create_campaign(
    payload: CampaignCreate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    return service.create(payload, restaurant_id=require_admin_tenant(tenant))


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    return service.update(campaign_id, payload, restaurant_id=require_admin_tenant(tenant))
