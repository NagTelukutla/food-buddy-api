from fastapi import HTTPException, status

from app.core.order_workflow import (
    DELIVER_FROM,
    DRIVER_ACCEPT_FROM,
    OUT_FOR_DELIVERY_FROM,
    QUEUEABLE_ORDER_STATUSES,
    normalize_status,
)
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.order_metadata_repository import OrderMetadataRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryAssignmentDetailResponse,
    DeliveryAssignmentListResponse,
    DeliveryAssignmentResponse,
    DeliveryLiveTrackResponse,
    DeliveryOrderItemSummary,
    DeliveryPartnerCreate,
    DeliveryPartnerResponse,
    DeliveryPartnerUpdate,
    DeliveryReportResponse,
    DeliveryStatusUpdate,
    DriverLiveLocation,
    DriverLocationUpdate,
    MapPoint,
)

DELIVERY_TRANSITIONS = {
    "pending_acceptance": {"accepted"},
    "accepted": {"out_for_delivery"},
    "out_for_delivery": {"delivered"},
    "picked_up": {"delivered"},
    "in_transit": {"delivered"},
}

LEGACY_DELIVERY_STATUS_MAP = {
    "picked_up": "out_for_delivery",
    "in_transit": "out_for_delivery",
}

LIVE_TRACKING_STATUSES = frozenset({"accepted", "out_for_delivery", "picked_up", "in_transit"})
DEFAULT_RESTAURANT_LAT = 17.435886
DEFAULT_RESTAURANT_LNG = 78.3618


def normalize_delivery_status(delivery_status: str) -> str:
    return LEGACY_DELIVERY_STATUS_MAP.get(delivery_status, delivery_status)


class DeliveryService:
    def __init__(
        self,
        delivery_repo: DeliveryRepository,
        order_repo: OrderRepository,
        order_metadata_repo: OrderMetadataRepository | None = None,
        restaurant_repo: RestaurantRepository | None = None,
    ):
        self.delivery_repo = delivery_repo
        self.order_repo = order_repo
        self.order_metadata_repo = order_metadata_repo
        self.restaurant_repo = restaurant_repo

    def list_partners(self, restaurant_id: int) -> list[DeliveryPartnerResponse]:
        return [DeliveryPartnerResponse(**p) for p in self.delivery_repo.list_partners(restaurant_id)]

    def create_partner(
        self, payload: DeliveryPartnerCreate, restaurant_id: int | None = None
    ) -> DeliveryPartnerResponse:
        data = payload.model_dump()
        if restaurant_id is not None:
            data["restaurant_id"] = restaurant_id
        created = self.delivery_repo.create_partner(data)
        return DeliveryPartnerResponse(**created)

    def update_partner(
        self,
        partner_id: int,
        payload: DeliveryPartnerUpdate,
        restaurant_id: int | None = None,
    ) -> DeliveryPartnerResponse:
        partner = self.delivery_repo.get_partner(partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
        if restaurant_id is not None and partner.get("restaurant_id") != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Delivery partner not in your restaurant",
            )
        updated = self.delivery_repo.update_partner(partner_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
        return DeliveryPartnerResponse(**updated)

    def _assert_order_belongs_to_restaurant(self, order, restaurant_id: int) -> None:
        if not self.order_metadata_repo:
            return
        meta_rid = self.order_metadata_repo.get_restaurant_id(order.order_id)
        if meta_rid is None or meta_rid != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to your restaurant",
            )

    def assign_order(
        self, order_pk: int, payload: DeliveryAssignRequest, restaurant_id: int
    ) -> DeliveryAssignmentResponse:
        order = self.order_repo.get_by_id(order_pk)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        self._assert_order_belongs_to_restaurant(order, restaurant_id)
        if order.order_type != "Delivery":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only delivery orders can be assigned",
            )
        partner = self.delivery_repo.get_partner(payload.delivery_partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
        if partner.get("restaurant_id") != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Delivery partner not in your restaurant",
            )
        assignment = self.delivery_repo.assign_delivery(
            {
                "order_id": order.order_id,
                "delivery_partner_id": payload.delivery_partner_id,
                "delivery_status": "pending_acceptance",
            }
        )
        self.delivery_repo.update_partner(payload.delivery_partner_id, {"status": "busy"})
        return DeliveryAssignmentResponse(**assignment)

    def _build_assignment_detail(self, assignment: dict) -> DeliveryAssignmentDetailResponse:
        order = self.order_repo.get_by_order_id(assignment["order_id"])
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        delivery_address = None
        if self.order_metadata_repo:
            metadata = self.order_metadata_repo.get_by_order_id(order.order_id)
            if metadata:
                delivery_address = metadata.get("delivery_address")
        driver_name = None
        if assignment.get("delivery_partner_id"):
            driver = self.delivery_repo.get_partner(assignment["delivery_partner_id"])
            driver_name = driver.get("name") if driver else None
        return DeliveryAssignmentDetailResponse(
            id=assignment["id"],
            order_id=assignment["order_id"],
            delivery_partner_id=assignment["delivery_partner_id"],
            delivery_status=normalize_delivery_status(assignment["delivery_status"]),
            created_at=assignment["created_at"],
            updated_at=assignment["updated_at"],
            customer_name=order.customer_name,
            phone=order.phone,
            delivery_address=delivery_address,
            order_status=normalize_status(order.status),
            order_type=order.order_type,
            total=order.total,
            notes=order.notes,
            driver_name=driver_name,
            items=[
                DeliveryOrderItemSummary(
                    name=item.name,
                    quantity=item.quantity,
                    line_total=item.line_total,
                )
                for item in order.items
            ],
        )

    def _assignment_matches_restaurant(self, assignment: dict, restaurant_id: int) -> bool:
        if not self.order_metadata_repo:
            return restaurant_id == 1
        metadata = self.order_metadata_repo.get_by_order_id(assignment["order_id"])
        if not metadata:
            return restaurant_id == 1
        return metadata.get("restaurant_id", 1) == restaurant_id

    def ensure_delivery_pool_entry(self, order_id: str) -> None:
        """Ensure an Accepted delivery order has an unassigned driver-pool entry."""
        order = self.order_repo.get_by_order_id(order_id)
        if not order or order.order_type != "Delivery":
            return
        if normalize_status(order.status) not in QUEUEABLE_ORDER_STATUSES:
            return
        pool_payload = {
            "order_id": order_id,
            "delivery_partner_id": None,
            "delivery_status": "pending_acceptance",
        }
        existing = self.delivery_repo.get_assignment_by_order(order_id)
        if not existing:
            self.delivery_repo.assign_delivery(pool_payload)
            return
        if existing.get("delivery_status") == "delivered":
            self.delivery_repo.assign_delivery(pool_payload)
            return
        if existing.get("delivery_partner_id") is None and existing.get("delivery_status") != "pending_acceptance":
            self.delivery_repo.update_assignment_status(order_id, "pending_acceptance")

    def sync_delivery_queue(self) -> None:
        """Ensure accepted delivery orders without an active assignment appear in the driver pool."""
        for order in self.order_repo.get_all_with_items():
            if order.order_type != "Delivery" or normalize_status(order.status) not in QUEUEABLE_ORDER_STATUSES:
                continue
            self.ensure_delivery_pool_entry(order.order_id)

    def _is_available_for_driver(self, assignment: dict, restaurant_id: int) -> bool:
        if assignment.get("delivery_partner_id") is not None:
            return False
        if assignment.get("delivery_status") != "pending_acceptance":
            return False
        if not self._assignment_matches_restaurant(assignment, restaurant_id):
            return False
        order = self.order_repo.get_by_order_id(assignment["order_id"])
        if not order:
            return False
        return normalize_status(order.status) in DRIVER_ACCEPT_FROM

    def resolve_partner(self, user: dict) -> dict:
        """Return the delivery partner profile for a user, creating one if missing."""
        partner = self.delivery_repo.get_partner_by_user(user["id"])
        if partner:
            return partner
        return self.delivery_repo.create_partner(
            {
                "restaurant_id": user.get("restaurant_id") or 1,
                "name": user.get("full_name") or user.get("username", "Driver"),
                "phone": user.get("phone") or "",
                "user_id": user["id"],
                "vehicle_type": "bike",
                "status": "available",
            }
        )

    def list_assignments_for_partner(self, user: dict) -> DeliveryAssignmentListResponse:
        partner = self.resolve_partner(user)
        self.sync_delivery_queue()
        partner_assignments = self.delivery_repo.list_assignments_for_partner(partner["id"])
        claimed_ids = {a["order_id"] for a in partner_assignments}
        available = [
            a
            for a in self.delivery_repo.list_unassigned_pending()
            if a["order_id"] not in claimed_ids and self._is_available_for_driver(a, partner["restaurant_id"])
        ]
        combined = available + partner_assignments
        items = [self._build_assignment_detail(a) for a in combined]
        return DeliveryAssignmentListResponse(items=items)

    def get_partner_report(self, user: dict) -> DeliveryReportResponse:
        partner = self.resolve_partner(user)
        assignments = self.delivery_repo.list_all_assignments_for_partner(partner["id"])
        completed = 0
        failed = 0
        for assignment in assignments:
            if assignment.get("delivery_status") == "delivered":
                completed += 1
                continue
            order = self.order_repo.get_by_order_id(assignment["order_id"])
            if order and normalize_status(order.status) == "Cancelled":
                failed += 1
        return DeliveryReportResponse(
            total=len(assignments),
            completed=completed,
            failed=failed,
        )

    def accept_assignment(self, order_id: str, user: dict) -> DeliveryAssignmentDetailResponse:
        partner = self.resolve_partner(user)
        assignment = self.delivery_repo.get_assignment_by_order(order_id)
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        if assignment["delivery_status"] != "pending_acceptance":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not awaiting acceptance",
            )
        partner_id = assignment.get("delivery_partner_id")
        if partner_id is None:
            if not self._assignment_matches_restaurant(assignment, partner["restaurant_id"]):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not available for your restaurant")
            claimed = self.delivery_repo.claim_assignment(order_id, partner["id"])
            if not claimed:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another driver already accepted this order",
                )
            assignment = claimed
        elif partner_id != partner["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your assignment")
        order = self.order_repo.get_by_order_id(order_id)
        if not order or normalize_status(order.status) not in DRIVER_ACCEPT_FROM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not available for driver acceptance",
            )
        updated = self.delivery_repo.update_assignment_status(order_id, "accepted")
        self.order_repo.update_status(order.id, "Driver Assigned")
        self.delivery_repo.update_partner(partner["id"], {"status": "busy"})
        return self._build_assignment_detail(updated)

    def update_delivery_status(
        self, order_id: str, payload: DeliveryStatusUpdate, user_id: int | None = None
    ) -> DeliveryAssignmentDetailResponse:
        assignment = self.delivery_repo.get_assignment_by_order(order_id)
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
        if user_id is not None:
            partner = self.delivery_repo.get_partner_by_user(user_id)
            if not partner or assignment["delivery_partner_id"] != partner["id"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your assignment")
        current = assignment["delivery_status"]
        normalized_current = normalize_delivery_status(current)
        next_status = payload.delivery_status
        if next_status in LEGACY_DELIVERY_STATUS_MAP:
            next_status = LEGACY_DELIVERY_STATUS_MAP[next_status]
        allowed = DELIVERY_TRANSITIONS.get(current, set())
        if next_status not in allowed and next_status not in DELIVERY_TRANSITIONS.get(normalized_current, set()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {current} to {payload.delivery_status}",
            )
        order = self.order_repo.get_by_order_id(order_id)
        order_status = normalize_status(order.status) if order else None
        if next_status == "out_for_delivery":
            if not order or order_status not in OUT_FOR_DELIVERY_FROM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Restaurant must mark the order as Prepared before you can start delivery",
                )
        if next_status == "delivered":
            if not order or order_status not in DELIVER_FROM:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order must be out for delivery before marking delivered",
                )
        updated = self.delivery_repo.update_assignment_status(order_id, next_status)
        if next_status == "out_for_delivery" and order:
            self.order_repo.update_status(order.id, "Out for Delivery")
        if next_status == "delivered" and order:
            self.order_repo.update_status(order.id, "Delivered")
            self.delivery_repo.update_partner(assignment["delivery_partner_id"], {"status": "available"})
            self.delivery_repo.clear_driver_location(order_id)
        return self._build_assignment_detail(updated)

    def _restaurant_point(self, restaurant_id: int = 1) -> MapPoint:
        restaurant = self.restaurant_repo.get_by_id(restaurant_id) if self.restaurant_repo else None
        lat = float(restaurant.get("latitude", DEFAULT_RESTAURANT_LAT)) if restaurant else DEFAULT_RESTAURANT_LAT
        lng = float(restaurant.get("longitude", DEFAULT_RESTAURANT_LNG)) if restaurant else DEFAULT_RESTAURANT_LNG
        name = restaurant.get("name", "Restaurant") if restaurant else "Restaurant"
        return MapPoint(latitude=lat, longitude=lng, label=name)

    def update_driver_location(self, user_id: int, payload: DriverLocationUpdate) -> DriverLiveLocation:
        partner = self.delivery_repo.get_partner_by_user(user_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found")
        assignment = self.delivery_repo.get_assignment_by_order(payload.order_id)
        if not assignment or assignment["delivery_partner_id"] != partner["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your active delivery")
        if assignment["delivery_status"] not in LIVE_TRACKING_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location sharing is only active during delivery",
            )
        record = self.delivery_repo.upsert_driver_location(
            payload.order_id,
            partner["id"],
            payload.latitude,
            payload.longitude,
        )
        return DriverLiveLocation(
            latitude=record["latitude"],
            longitude=record["longitude"],
            updated_at=record["updated_at"],
            partner_name=partner.get("name"),
        )

    def get_live_track(self, order_id: str) -> DeliveryLiveTrackResponse:
        order = self.order_repo.get_by_order_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        assignment = self.delivery_repo.get_assignment_by_order(order_id)
        raw_delivery_status = assignment.get("delivery_status") if assignment else None
        delivery_status = normalize_delivery_status(raw_delivery_status) if raw_delivery_status else None
        live = bool(raw_delivery_status in LIVE_TRACKING_STATUSES)

        restaurant_id = 1
        delivery_address = None
        destination = None
        if self.order_metadata_repo:
            meta = self.order_metadata_repo.get_by_order_id(order_id)
            if meta:
                restaurant_id = meta.get("restaurant_id", 1)
                delivery_address = meta.get("delivery_address")
                if meta.get("delivery_lat") is not None and meta.get("delivery_lng") is not None:
                    destination = MapPoint(
                        latitude=float(meta["delivery_lat"]),
                        longitude=float(meta["delivery_lng"]),
                        label="Delivery address",
                    )

        driver = None
        if live:
            loc = self.delivery_repo.get_driver_location(order_id)
            if loc:
                partner = self.delivery_repo.get_partner(loc.get("delivery_partner_id"))
                driver = DriverLiveLocation(
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    updated_at=loc["updated_at"],
                    partner_name=partner.get("name") if partner else None,
                )

        return DeliveryLiveTrackResponse(
            order_id=order_id,
            order_status=normalize_status(order.status),
            delivery_status=delivery_status,
            live_tracking_enabled=live,
            delivery_address=delivery_address,
            restaurant=self._restaurant_point(restaurant_id),
            destination=destination,
            driver=driver,
        )
