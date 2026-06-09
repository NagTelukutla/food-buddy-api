from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class ReviewRepository(BaseJsonRepository):
    COLLECTION = "reviews"

    def __init__(self):
        super().__init__("reviews.json", {"reviews": []})

    def get_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.COLLECTION):
            if item.get("order_id") == order_id:
                return item
        return None

    def list_for_restaurant(self, restaurant_id: int) -> List[Dict[str, Any]]:
        items = [
            r for r in self.get_collection(self.COLLECTION) if r.get("restaurant_id") == restaurant_id
        ]
        return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, review_id)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        payload = {**data, "created_at": now, "updated_at": now}
        return self.create_item(self.COLLECTION, payload)

    def add_response(self, review_id: int, response: str) -> Optional[Dict[str, Any]]:
        return self.update_item(
            self.COLLECTION,
            review_id,
            {"owner_response": response, "updated_at": utc_now_iso()},
        )
