from fastapi import APIRouter, Depends

from app.core.deps import get_platform_service
from app.core.rbac import ROLE_PLATFORM, require_roles
from app.schemas.auth import TokenPayload
from app.schemas.platform import PlatformSettingsResponse, PlatformSettingsUpdate, PlatformStatsResponse
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/api/admin", tags=["Platform Admin"])


@router.get("/platform-stats", response_model=PlatformStatsResponse)
def platform_stats(
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: PlatformService = Depends(get_platform_service),
) -> PlatformStatsResponse:
    return service.get_stats()


@router.get("/platform-settings", response_model=PlatformSettingsResponse)
def get_platform_settings(
    service: PlatformService = Depends(get_platform_service),
) -> PlatformSettingsResponse:
    return service.get_settings()


@router.put("/platform-settings", response_model=PlatformSettingsResponse)
def update_platform_settings(
    payload: PlatformSettingsUpdate,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: PlatformService = Depends(get_platform_service),
) -> PlatformSettingsResponse:
    return service.update_settings(payload)
