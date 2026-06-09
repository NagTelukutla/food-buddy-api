"""Sequential order status workflow and admin transition rules."""

from typing import Optional

ORDER_STATUSES = (
    "Pending",
    "Accepted",
    "Driver Assigned",
    "Prepared",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
)

DELIVERY_FLOW = (
    "Pending",
    "Accepted",
    "Driver Assigned",
    "Prepared",
    "Out for Delivery",
    "Delivered",
)

NON_DELIVERY_FLOW = (
    "Pending",
    "Accepted",
    "Prepared",
    "Delivered",
)

LEGACY_STATUS_MAP = {
    "Preparing": "Driver Assigned",
    "Ready": "Prepared",
    "Awaiting Driver Acceptance": "Accepted",
    "Assigned to Driver": "Driver Assigned",
    "Ready for Pickup": "Prepared",
}

ADMIN_TRANSITIONS: dict[tuple[str, str], str] = {
    ("Pending", "Delivery"): "Accepted",
    ("Pending", "Pickup"): "Accepted",
    ("Pending", "Dine In"): "Accepted",
    ("Accepted", "Pickup"): "Prepared",
    ("Accepted", "Dine In"): "Prepared",
    ("Driver Assigned", "Delivery"): "Prepared",
    ("Prepared", "Pickup"): "Delivered",
    ("Prepared", "Dine In"): "Delivered",
}

ADMIN_ACTION_LABELS: dict[tuple[str, str], str] = {
    ("Pending", "Delivery"): "Accept Order",
    ("Pending", "Pickup"): "Accept Order",
    ("Pending", "Dine In"): "Accept Order",
    ("Accepted", "Pickup"): "Prepared",
    ("Accepted", "Dine In"): "Prepared",
    ("Driver Assigned", "Delivery"): "Prepared",
    ("Prepared", "Pickup"): "Mark Delivered",
    ("Prepared", "Dine In"): "Mark Delivered",
}

DRIVER_ACCEPT_FROM = frozenset({"Accepted"})
OUT_FOR_DELIVERY_FROM = frozenset({"Prepared"})
DELIVER_FROM = frozenset({"Out for Delivery"})

QUEUEABLE_ORDER_STATUSES = frozenset({"Accepted"})


def normalize_status(status: str) -> str:
    return LEGACY_STATUS_MAP.get(status, status)


def admin_status_after_accept(order_type: str) -> str:
    return ADMIN_TRANSITIONS[("Pending", order_type)]


def get_admin_action(status: str, order_type: str) -> Optional[tuple[str, str]]:
    """Return (button_label, next_status) for the admin's single allowed action."""
    normalized = normalize_status(status)
    key = (normalized, order_type)
    next_status = ADMIN_TRANSITIONS.get(key)
    if not next_status:
        return None
    label = ADMIN_ACTION_LABELS[key]
    return label, next_status


def validate_admin_transition(current: str, order_type: str, next_status: str) -> None:
    from fastapi import HTTPException, status as http_status

    normalized = normalize_status(current)
    if order_type == "Delivery" and next_status == "Delivered":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Delivery orders must be marked delivered by the delivery partner",
        )
    expected = ADMIN_TRANSITIONS.get((normalized, order_type))
    if expected != next_status:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition {order_type} order from '{normalized}' to '{next_status}'",
        )
