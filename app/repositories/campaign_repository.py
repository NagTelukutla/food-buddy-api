from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class CampaignRepository(BaseJsonRepository):
    COLLECTION = "campaigns"

    def __init__(self):
        super().__init__("campaigns.json", {"campaigns": []})

    def list_for_restaurant(self, restaurant_id: int) -> List[Dict[str, Any]]:
        return [
            c for c in self.get_collection(self.COLLECTION) if c.get("restaurant_id") == restaurant_id
        ]

    def get_by_id(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, campaign_id)

    def list_active(self, restaurant_id: int) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        active = []
        for campaign in self.list_for_restaurant(restaurant_id):
            if campaign.get("status") != "active":
                continue
            try:
                start = datetime.fromisoformat(campaign["start_date"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(campaign["end_date"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                continue
            if start <= now <= end:
                active.append(campaign)
        return active

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        payload = {
            **data,
            "status": data.get("status", "draft"),
            "created_at": now,
            "updated_at": now,
        }
        return self.create_item(self.COLLECTION, payload)

    def update(self, campaign_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.COLLECTION, campaign_id, updates)
