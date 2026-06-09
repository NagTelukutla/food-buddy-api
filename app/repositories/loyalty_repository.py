from typing import Any, Dict, List

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class LoyaltyRepository(BaseJsonRepository):
    COLLECTION = "transactions"

    def __init__(self):
        super().__init__("loyalty_points.json", {"transactions": []})

    def list_for_customer(self, customer_id: int, restaurant_id: int | None = None) -> List[Dict[str, Any]]:
        items = [
            t for t in self.get_collection(self.COLLECTION) if t.get("customer_id") == customer_id
        ]
        if restaurant_id is not None:
            items = [t for t in items if t.get("restaurant_id") == restaurant_id]
        return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

    def add_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {**data, "created_at": utc_now_iso()}
        return self.create_item(self.COLLECTION, payload)
