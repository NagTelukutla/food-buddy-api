from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class DeliveryRepository(BaseJsonRepository):
    PARTNERS = "partners"
    ASSIGNMENTS = "assignments"
    LOCATIONS = "driver_locations"

    def __init__(self):
        super().__init__(
            "delivery.json",
            {"partners": [], "assignments": [], "driver_locations": []},
        )

    def list_partners(self, restaurant_id: int) -> List[Dict[str, Any]]:
        return [
            p
            for p in self.get_collection(self.PARTNERS)
            if p.get("restaurant_id") == restaurant_id and p.get("is_active", True)
        ]

    def get_partner(self, partner_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.PARTNERS, partner_id)

    def get_partner_by_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.PARTNERS):
            if item.get("user_id") == user_id:
                return item
        return None

    def create_partner(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        payload = {
            **data,
            "status": data.get("status", "offline"),
            "is_active": data.get("is_active", True),
            "created_at": now,
            "updated_at": now,
        }
        return self.create_item(self.PARTNERS, payload)

    def update_partner(self, partner_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.PARTNERS, partner_id, updates)

    def get_assignment_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.ASSIGNMENTS):
            if item.get("order_id") == order_id:
                return item
        return None

    def list_assignments_for_partner(self, partner_id: int) -> List[Dict[str, Any]]:
        return [
            a
            for a in self.get_collection(self.ASSIGNMENTS)
            if a.get("delivery_partner_id") == partner_id
            and a.get("delivery_status") not in ("delivered",)
        ]

    def list_all_assignments_for_partner(self, partner_id: int) -> List[Dict[str, Any]]:
        return [
            a
            for a in self.get_collection(self.ASSIGNMENTS)
            if a.get("delivery_partner_id") == partner_id
        ]

    def list_unassigned_pending(self) -> List[Dict[str, Any]]:
        return [
            a
            for a in self.get_collection(self.ASSIGNMENTS)
            if a.get("delivery_partner_id") is None
            and a.get("delivery_status") == "pending_acceptance"
        ]

    def claim_assignment(self, order_id: str, partner_id: int) -> Optional[Dict[str, Any]]:
        assignment = self.get_assignment_by_order(order_id)
        if not assignment or assignment.get("delivery_partner_id") is not None:
            return None
        return self.update_item(
            self.ASSIGNMENTS,
            assignment["id"],
            {"delivery_partner_id": partner_id, "updated_at": utc_now_iso()},
        )

    def assign_delivery(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        existing = self.get_assignment_by_order(data["order_id"])
        if existing:
            return self.update_item(
                self.ASSIGNMENTS,
                existing["id"],
                {
                    **data,
                    "delivery_status": data.get("delivery_status", "pending_acceptance"),
                    "updated_at": now,
                },
            )
        payload = {
            **data,
            "delivery_status": data.get("delivery_status", "pending_acceptance"),
            "created_at": now,
            "updated_at": now,
        }
        return self.create_item(self.ASSIGNMENTS, payload)

    def update_assignment_status(
        self, order_id: str, delivery_status: str
    ) -> Optional[Dict[str, Any]]:
        assignment = self.get_assignment_by_order(order_id)
        if not assignment:
            return None
        return self.update_item(
            self.ASSIGNMENTS,
            assignment["id"],
            {"delivery_status": delivery_status, "updated_at": utc_now_iso()},
        )

    def upsert_driver_location(
        self,
        order_id: str,
        delivery_partner_id: int,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        for item in self.get_collection(self.LOCATIONS):
            if item.get("order_id") == order_id:
                return self.update_item(
                    self.LOCATIONS,
                    item["id"],
                    {
                        "latitude": latitude,
                        "longitude": longitude,
                        "delivery_partner_id": delivery_partner_id,
                        "updated_at": now,
                    },
                )
        return self.create_item(
            self.LOCATIONS,
            {
                "order_id": order_id,
                "delivery_partner_id": delivery_partner_id,
                "latitude": latitude,
                "longitude": longitude,
                "created_at": now,
                "updated_at": now,
            },
        )

    def get_driver_location(self, order_id: str) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(self.LOCATIONS):
            if item.get("order_id") == order_id:
                return item
        return None

    def clear_driver_location(self, order_id: str) -> None:
        loc = self.get_driver_location(order_id)
        if loc:
            self.delete_item(self.LOCATIONS, loc["id"])
