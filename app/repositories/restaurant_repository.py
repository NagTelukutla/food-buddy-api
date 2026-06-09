import re
from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso
from app.utils.tenant_id import generate_tenant_id
from app.utils.tenant_registry import collect_used_tenant_ids


class RestaurantRepository(BaseJsonRepository):
    COLLECTION = "restaurants"

    def __init__(self):
        super().__init__("restaurants.json", {"restaurants": []})

    def get_all(self, active_only: bool = False) -> List[Dict[str, Any]]:
        items = self.get_collection(self.COLLECTION)
        if active_only:
            return [r for r in items if r.get("is_active", True)]
        return items

    def get_by_id(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, restaurant_id)

    def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.COLLECTION):
            if item.get("slug") == slug:
                return item
        return None

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug or "restaurant"

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        slug = data.get("slug") or self._slugify(data["name"])
        base_slug = slug
        counter = 1
        while self.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        payload = {
            **data,
            "slug": slug,
            "is_active": data.get("is_active", True),
            "created_at": now,
            "updated_at": now,
        }
        tenant_id = generate_tenant_id(collect_used_tenant_ids())
        return self.create_item(self.COLLECTION, payload, explicit_id=tenant_id)

    def update(self, restaurant_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.COLLECTION, restaurant_id, updates)
