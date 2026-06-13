import math

from fastapi import HTTPException, status

from app.core.config import get_settings
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
    DriverPartnerLocationUpdate,
    MapPoint,
)
from app.utils.geo import distance_km, is_valid_coord

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

    def list_partners(self, restaurant_id: int | None = None) -> list[DeliveryPartnerResponse]:
        return [DeliveryPartnerResponse(**p) for p in self.delivery_repo.list_partners(restaurant_id)]

    def create_partner(
        self, payload: DeliveryPartnerCreate, restaurant_id: int | None = None
    ) -> DeliveryPartnerResponse:
        data = payload.model_dump(exclude_none=True)
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
        if not partner.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery partner is not active",
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

    def _build_assignment_detail(
        self, assignment: dict, distance_km_value: float | None = None
    ) -> DeliveryAssignmentDetailResponse:
        order = self.order_repo.get_by_order_id(assignment["order_id"])
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        delivery_address = None
        delivery_lat = None
        delivery_lng = None
        restaurant_id = None
        if self.order_metadata_repo:
            metadata = self.order_metadata_repo.get_by_order_id(order.order_id)
            if metadata:
                delivery_address = metadata.get("delivery_address")
                delivery_lat = metadata.get("delivery_lat")
                delivery_lng = metadata.get("delivery_lng")
                restaurant_id = metadata.get("restaurant_id")

        restaurant_name = None
        restaurant_address = None
        restaurant_lat = None
        restaurant_lng = None
        if self.restaurant_repo:
            restaurant = (
                self.restaurant_repo.get_by_id(restaurant_id)
                if restaurant_id is not None
                else None
            )
            if restaurant:
                restaurant_name = restaurant.get("name")
                restaurant_address = restaurant.get("address")
                restaurant_lat = restaurant.get("latitude")
                restaurant_lng = restaurant.get("longitude")

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
            delivery_lat=float(delivery_lat) if delivery_lat is not None else None,
            delivery_lng=float(delivery_lng) if delivery_lng is not None else None,
            order_status=normalize_status(order.status),
            order_type=order.order_type,
            total=order.total,
            notes=order.notes,
            driver_name=driver_name,
            restaurant_name=restaurant_name,
            restaurant_address=restaurant_address,
            restaurant_lat=float(restaurant_lat) if restaurant_lat is not None else None,
            restaurant_lng=float(restaurant_lng) if restaurant_lng is not None else None,
            distance_km=distance_km_value,
            items=[
                DeliveryOrderItemSummary(
                    name=item.name,
                    quantity=item.quantity,
                    line_total=item.line_total,
                )
                for item in order.items
            ],
        )

    def _pickup_coords_for_assignment(self, assignment: dict) -> tuple[float | None, float | None]:
        restaurant_id = None
        if self.order_metadata_repo:
            metadata = self.order_metadata_repo.get_by_order_id(assignment["order_id"])
            if metadata:
                restaurant_id = metadata.get("restaurant_id")
        if self.restaurant_repo and restaurant_id is not None:
            restaurant = self.restaurant_repo.get_by_id(restaurant_id)
            if restaurant:
                lat = restaurant.get("latitude")
                lng = restaurant.get("longitude")
                if lat is not None and lng is not None:
                    return float(lat), float(lng)
        return None, None

    def _order_radius_km(self) -> float:
        return get_settings().delivery_partner_order_radius_km

    def _resolve_driver_coords(
        self,
        partner: dict,
        latitude: float | None = None,
        longitude: float | None = None,
        *,
        persist: bool = False,
        required: bool = False,
    ) -> tuple[float | None, float | None]:
        lat = latitude if latitude is not None else partner.get("last_latitude")
        lng = longitude if longitude is not None else partner.get("last_longitude")
        if is_valid_coord(lat, lng):
            if persist and latitude is not None and longitude is not None:
                self.delivery_repo.update_partner_location(partner["id"], float(lat), float(lng))
            return float(lat), float(lng)
        if required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Driver location is required. Enable GPS to see and accept nearby orders.",
            )
        return None, None

    def update_partner_location(self, user: dict, payload: DriverPartnerLocationUpdate) -> None:
        partner = self.resolve_partner(user)
        self.delivery_repo.update_partner_location(
            partner["id"], payload.latitude, payload.longitude
        )

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

    def _is_available_for_driver(
        self,
        assignment: dict,
        driver_lat: float | None = None,
        driver_lng: float | None = None,
    ) -> tuple[bool, float | None]:
        if assignment.get("delivery_partner_id") is not None:
            return False, None
        if assignment.get("delivery_status") != "pending_acceptance":
            return False, None
        order = self.order_repo.get_by_order_id(assignment["order_id"])
        if not order:
            return False, None
        if normalize_status(order.status) not in DRIVER_ACCEPT_FROM:
            return False, None
        if driver_lat is None or driver_lng is None:
            return False, None
        pickup_lat, pickup_lng = self._pickup_coords_for_assignment(assignment)
        if pickup_lat is None or pickup_lng is None:
            return False, None
        dist = distance_km(driver_lat, driver_lng, pickup_lat, pickup_lng)
        if dist > self._order_radius_km():
            return False, dist
        return True, dist

    def resolve_partner(self, user: dict) -> dict:
        """Return the delivery partner profile for a user, creating one if missing."""
        partner = self.delivery_repo.get_partner_by_user(user["id"])
        if partner:
            return partner
        return self.delivery_repo.create_partner(
            {
                "name": user.get("full_name") or user.get("username", "Driver"),
                "phone": user.get("phone") or "",
                "user_id": user["id"],
                "vehicle_type": "bike",
                "status": "available",
            }
        )

    def list_assignments_for_partner(
        self,
        user: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> DeliveryAssignmentListResponse:
        partner = self.resolve_partner(user)
        self.sync_delivery_queue()
        driver_lat, driver_lng = self._resolve_driver_coords(
            partner, latitude, longitude, persist=False
        )
        partner_assignments = self.delivery_repo.list_assignments_for_partner(partner["id"])
        claimed_ids = {a["order_id"] for a in partner_assignments}
        available: list[tuple[dict, float | None]] = []
        for a in self.delivery_repo.list_unassigned_pending():
            if a["order_id"] in claimed_ids:
                continue
            eligible, dist = self._is_available_for_driver(a, driver_lat, driver_lng)
            if eligible:
                available.append((a, dist))
        available.sort(key=lambda item: item[1] if item[1] is not None else math.inf)
        items = []
        for a, dist in available:
            try:
                items.append(self._build_assignment_detail(a, distance_km_value=dist))
            except HTTPException as e:
                if e.status_code == status.HTTP_404_NOT_FOUND and e.detail == "Order not found":
                    continue
                raise e
        for a in partner_assignments:
            try:
                items.append(self._build_assignment_detail(a))
            except HTTPException as e:
                if e.status_code == status.HTTP_404_NOT_FOUND and e.detail == "Order not found":
                    continue
                raise e
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

    def accept_assignment(
        self,
        order_id: str,
        user: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> DeliveryAssignmentDetailResponse:
        partner = self.resolve_partner(user)
        driver_lat, driver_lng = self._resolve_driver_coords(
            partner,
            latitude,
            longitude,
            persist=latitude is not None and longitude is not None,
            required=True,
        )
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
            eligible, _dist = self._is_available_for_driver(assignment, driver_lat, driver_lng)
            if not eligible:
                radius = int(self._order_radius_km())
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Order is outside your service area ({radius} km)",
                )
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

    def _restaurant_point(self, restaurant_id: int | None = None) -> MapPoint:
        restaurant = None
        if self.restaurant_repo:
            if restaurant_id is not None:
                restaurant = self.restaurant_repo.get_by_id(restaurant_id)
            if not restaurant:
                active = self.restaurant_repo.get_all(active_only=True)
                if active:
                    restaurant = active[0]

        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Restaurant details not found for location tracking."
            )

        if restaurant.get("latitude") is None or restaurant.get("longitude") is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Restaurant '{restaurant.get('name')}' is missing location coordinates."
            )

        lat = float(restaurant["latitude"])
        lng = float(restaurant["longitude"])
        label = restaurant.get("address") or restaurant.get("name") or "Restaurant"
        return MapPoint(latitude=lat, longitude=lng, label=label)

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
        restaurant_name = None
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

        restaurant_point = self._restaurant_point(restaurant_id)
        if self.restaurant_repo:
            restaurant = self.restaurant_repo.get_by_id(restaurant_id)
            if restaurant:
                restaurant_name = restaurant.get("name")

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
            restaurant_name=restaurant_name,
            restaurant=restaurant_point,
            destination=destination,
            driver=driver,
        )
