from typing import Any, Dict

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class PlatformSettingsRepository(BaseJsonRepository):
    def __init__(self):
        super().__init__(
            "platform_settings.json",
            {
                "platform_name": "Restaurant Platform",
                "default_tax_rate": 0.05,
                "loyalty_points_per_rupee": 0.1,
                "order_id_prefix": "ORD",
                "featured_restaurant_ids": [],
                "maintenance_mode": False,
            },
        )

    def get_settings(self) -> Dict[str, Any]:
        return self.read()

    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        data = self.read()
        data.update(updates)
        data["updated_at"] = utc_now_iso()
        self.write(data)
        return data
