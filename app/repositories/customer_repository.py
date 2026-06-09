from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class CustomerRepository(BaseJsonRepository):
    COLLECTION = "customers"

    def __init__(self):
        super().__init__("customers.json", {"customers": []})

    def get_all(self) -> List[Dict[str, Any]]:
        return self.get_collection(self.COLLECTION)

    def get_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, customer_id)

    def get_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.COLLECTION):
            if item.get("user_id") == user_id:
                return item
        return None

    def get_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.COLLECTION):
            if item.get("phone") == phone:
                return item
        return None

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        payload = {
            **data,
            "addresses": data.get("addresses", []),
            "loyalty_points_balance": data.get("loyalty_points_balance", 0),
            "created_at": now,
            "updated_at": now,
        }
        return self.create_item(self.COLLECTION, payload)

    def update(self, customer_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.COLLECTION, customer_id, updates)
