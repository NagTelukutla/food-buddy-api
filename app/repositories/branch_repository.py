from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso
from app.utils.tenant_id import generate_tenant_id
from app.utils.tenant_registry import collect_used_tenant_ids


class BranchRepository(BaseJsonRepository):
    COLLECTION = "branches"

    def __init__(self):
        super().__init__("branches.json", {"branches": []})

    def get_by_restaurant(self, restaurant_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
        items = [
            b for b in self.get_collection(self.COLLECTION) if b.get("restaurant_id") == restaurant_id
        ]
        if active_only:
            return [b for b in items if b.get("is_active", True)]
        return items

    def get_by_id(self, branch_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, branch_id)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        payload = {
            **data,
            "is_active": data.get("is_active", True),
            "created_at": now,
            "updated_at": now,
        }
        tenant_id = generate_tenant_id(collect_used_tenant_ids())
        return self.create_item(self.COLLECTION, payload, explicit_id=tenant_id)

    def update(self, branch_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.COLLECTION, branch_id, updates)

    def deactivate(self, branch_id: int) -> Optional[Dict[str, Any]]:
        return self.update(branch_id, {"is_active": False})
