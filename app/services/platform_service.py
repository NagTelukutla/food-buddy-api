from app.repositories.customer_repository import CustomerRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.platform import PlatformSettingsResponse, PlatformSettingsUpdate, PlatformStatsResponse


class PlatformService:
    def __init__(
        self,
        platform_repo: PlatformSettingsRepository,
        restaurant_repo: RestaurantRepository,
        order_repo: OrderRepository,
        customer_repo: CustomerRepository,
    ):
        self.platform_repo = platform_repo
        self.restaurant_repo = restaurant_repo
        self.order_repo = order_repo
        self.customer_repo = customer_repo

    def get_settings(self) -> PlatformSettingsResponse:
        return PlatformSettingsResponse(**self.platform_repo.get_settings())

    def update_settings(self, payload: PlatformSettingsUpdate) -> PlatformSettingsResponse:
        updated = self.platform_repo.update(payload.model_dump(exclude_unset=True))
        return PlatformSettingsResponse(**updated)

    def get_stats(self) -> PlatformStatsResponse:
        restaurants = self.restaurant_repo.get_all(active_only=True)
        orders = self.order_repo.get_all_with_items()
        gmv = sum(o.total for o in orders if o.status not in ("Cancelled",))
        return PlatformStatsResponse(
            active_restaurants=len(restaurants),
            total_orders=len(orders),
            total_gmv=round(gmv, 2),
            total_customers=len(self.customer_repo.get_all()),
        )
