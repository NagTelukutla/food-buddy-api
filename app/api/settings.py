from fastapi import APIRouter, Depends

from app.core.deps import get_settings_repository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import RestaurantSettings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=RestaurantSettings)
def get_restaurant_settings(
    settings_repo: SettingsRepository = Depends(get_settings_repository),
) -> RestaurantSettings:
    data = settings_repo.get_settings()
    return RestaurantSettings(**data)
