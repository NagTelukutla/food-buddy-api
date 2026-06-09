from typing import Any, Dict, List, Optional, Set

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class OrderMetadataRepository(BaseJsonRepository):
    COLLECTION = "metadata"

    def __init__(self):
        super().__init__("order_metadata.json", {"metadata": []})

    def get_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.COLLECTION):
            if item.get("order_id") == order_id:
                return item
        return None

    def get_restaurant_id(self, order_id: str) -> Optional[int]:
        meta = self.get_by_order_id(order_id)
        if not meta:
            return None
        rid = meta.get("restaurant_id")
        return int(rid) if rid is not None else None

    def list_order_ids_for_restaurant(self, restaurant_id: int) -> Set[str]:
        return {
            item["order_id"]
            for item in self.get_collection(self.COLLECTION)
            if item.get("order_id") and item.get("restaurant_id") == restaurant_id
        }

    def upsert(self, order_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self.get_by_order_id(order_id)
        now = utc_now_iso()
        if existing:
            return self.update_item(
                self.COLLECTION,
                existing["id"],
                {**data, "order_id": order_id, "updated_at": now},
            )
        payload = {"order_id": order_id, **data, "created_at": now, "updated_at": now}
        return self.create_item(self.COLLECTION, payload)
