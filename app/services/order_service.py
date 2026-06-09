import math
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.order_workflow import (
    QUEUEABLE_ORDER_STATUSES,
    normalize_status,
    validate_admin_transition,
)
from app.models.order import Order, OrderItem
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_metadata_repository import OrderMetadataRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderTrackResponse,
)
from app.utils.geocode import geocode_address
from app.utils.order_id import format_order_number

LIVE_TRACKING_STATUSES = frozenset({"accepted", "out_for_delivery", "picked_up", "in_transit"})


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        menu_repository: MenuRepository,
        audit_repository: AuditLogRepository,
        order_metadata_repository: OrderMetadataRepository | None = None,
        delivery_repository: DeliveryRepository | None = None,
        restaurant_repository: RestaurantRepository | None = None,
    ):
        self.order_repository = order_repository
        self.menu_repository = menu_repository
        self.audit_repository = audit_repository
        self.order_metadata_repository = order_metadata_repository
        self.delivery_repository = delivery_repository
        self.restaurant_repository = restaurant_repository
        self.settings = get_settings()

    def _default_restaurant_id(self) -> int:
        if self.restaurant_repository:
            restaurants = self.restaurant_repository.get_all(active_only=True)
            if restaurants:
                return restaurants[0]["id"]
        return 1

    def _to_response(self, order: Order) -> OrderResponse:
        response = OrderResponse.model_validate(order)
        response.status = normalize_status(response.status)
        if self.delivery_repository:
            assignment = self.delivery_repository.get_assignment_by_order(order.order_id)
            if assignment and assignment.get("delivery_partner_id"):
                partner = self.delivery_repository.get_partner(assignment["delivery_partner_id"])
                if partner:
                    response.assigned_driver_name = partner.get("name")
                    response.assigned_driver_phone = partner.get("phone")
        return response

    def create_order(
        self,
        payload: OrderCreate,
        payment_status: str = "unpaid",
        order_status: str = "Pending",
        customer_id: Optional[int] = None,
        profile_phone: Optional[str] = None,
    ) -> OrderResponse:
        order_phone = profile_phone if profile_phone else payload.phone

        subtotal = 0.0
        order_items: list[OrderItem] = []

        for cart_item in payload.items:
            menu_item = self.menu_repository.get_by_id(cart_item.menu_item_id)
            if not menu_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item {cart_item.menu_item_id} not found",
                )
            if not menu_item.get("available", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item '{menu_item['name']}' is not available",
                )
            line_total = menu_item["price"] * cart_item.quantity
            subtotal += line_total
            order_items.append(
                OrderItem(
                    menu_item_id=menu_item["id"],
                    name=menu_item["name"],
                    price=menu_item["price"],
                    quantity=cart_item.quantity,
                    line_total=line_total,
                )
            )

        tax = round(subtotal * self.settings.tax_rate, 2)
        total = round(subtotal + tax, 2)
        sequence = self.order_repository.get_next_sequence()
        order_id = format_order_number(sequence)

        order = Order(
            order_id=order_id,
            customer_name=payload.customer_name,
            phone=order_phone,
            table_number=payload.table_number,
            order_type=payload.order_type,
            notes=payload.notes,
            status=order_status,
            payment_status=payment_status,
            subtotal=subtotal,
            tax=tax,
            total=total,
        )
        created = self.order_repository.create(order, order_items)
        if self.order_metadata_repository:
            metadata = {
                "restaurant_id": self._default_restaurant_id(),
                "customer_id": customer_id,
                "order_type": payload.order_type,
            }
            if payload.delivery_address:
                addr = payload.delivery_address.strip()
                metadata["delivery_address"] = addr
                restaurant = None
                if self.restaurant_repository:
                    restaurant = self.restaurant_repository.get_by_id(self._default_restaurant_id())
                base_lat = float(restaurant.get("latitude", 17.435886)) if restaurant else 17.435886
                base_lng = float(restaurant.get("longitude", 78.3618)) if restaurant else 78.3618
                lat, lng = geocode_address(addr, base_lat, base_lng)
                metadata["delivery_lat"] = lat
                metadata["delivery_lng"] = lng
            self.order_metadata_repository.upsert(order_id, metadata)
        self.audit_repository.create(
            action="CREATE",
            entity_type="order",
            entity_id=order_id,
            user="customer",
            details=f"Order placed by {payload.customer_name}",
        )
        return self._to_response(created)

    def _order_ids_for_restaurant(self, restaurant_id: int) -> set:
        if not self.order_metadata_repository:
            return set()
        return self.order_metadata_repository.list_order_ids_for_restaurant(restaurant_id)

    def _assert_order_belongs_to_restaurant(self, order: Order, restaurant_id: int) -> None:
        if not self.order_metadata_repository:
            return
        meta_rid = self.order_metadata_repository.get_restaurant_id(order.order_id)
        if meta_rid is None or meta_rid != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to your restaurant",
            )

    def list_orders(
        self,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        restaurant_id: Optional[int] = None,
    ) -> OrderListResponse:
        order_ids = self._order_ids_for_restaurant(restaurant_id) if restaurant_id else None
        orders, total = self.order_repository.list_orders(
            page, page_size, status_filter, search, order_ids=order_ids
        )
        total_pages = max(1, math.ceil(total / page_size)) if total else 1
        return OrderListResponse(
            items=[self._to_response(order) for order in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def list_orders_by_phone(
        self,
        phone: str,
        page: int = 1,
        page_size: int = 50,
    ) -> OrderListResponse:
        orders, total = self.order_repository.list_orders_by_phone(phone, page, page_size)
        total_pages = max(1, math.ceil(total / page_size)) if total else 1
        return OrderListResponse(
            items=[self._to_response(order) for order in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_order(self, order_pk: int, restaurant_id: Optional[int] = None) -> OrderResponse:
        order = self.order_repository.get_by_id(order_pk)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if restaurant_id is not None:
            self._assert_order_belongs_to_restaurant(order, restaurant_id)
        return self._to_response(order)

    def get_order_by_public_id(self, order_id: str) -> OrderResponse:
        order = self.order_repository.get_by_order_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return self._to_response(order)

    def track_order(self, order_id: str) -> OrderTrackResponse:
        order = self.order_repository.get_by_order_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        response = self._to_response(order)
        delivery_status = None
        live_tracking_enabled = False
        if self.delivery_repository:
            assignment = self.delivery_repository.get_assignment_by_order(order_id)
            if assignment:
                delivery_status = assignment.get("delivery_status")
                live_tracking_enabled = delivery_status in LIVE_TRACKING_STATUSES
        return OrderTrackResponse(
            order_id=response.order_id,
            customer_name=response.customer_name,
            status=response.status,
            order_type=response.order_type,
            total=response.total,
            created_at=response.created_at,
            updated_at=response.updated_at,
            items=response.items,
            delivery_status=delivery_status,
            live_tracking_enabled=live_tracking_enabled,
        )

    def update_status(
        self,
        order_pk: int,
        payload: OrderStatusUpdate,
        user: Optional[str] = None,
        restaurant_id: Optional[int] = None,
    ) -> OrderResponse:
        order = self.order_repository.get_by_id(order_pk)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if restaurant_id is not None:
            self._assert_order_belongs_to_restaurant(order, restaurant_id)
        current = normalize_status(order.status)
        next_status = payload.status
        validate_admin_transition(current, order.order_type, next_status)
        updated = self.order_repository.update_status(order_pk, next_status)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if (
            next_status == "Accepted"
            and updated.order_type == "Delivery"
            and self.delivery_repository
        ):
            self.delivery_repository.assign_delivery(
                {
                    "order_id": updated.order_id,
                    "delivery_partner_id": None,
                    "delivery_status": "pending_acceptance",
                }
            )
        self.audit_repository.create(
            action="STATUS_UPDATE",
            entity_type="order",
            entity_id=updated.order_id,
            user=user,
            details=f"Status changed to {payload.status}",
        )
        return self._to_response(updated)
