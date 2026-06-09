from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem
from app.utils.phone import phone_match_suffix, phones_match


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_next_sequence(self) -> int:
        year_prefix = f"ORD-{datetime.now().year}"
        count = (
            self.db.query(func.count(Order.id))
            .filter(Order.order_id.like(f"{year_prefix}%"))
            .scalar()
        )
        return int(count or 0) + 1

    def create(self, order: Order, items: List[OrderItem]) -> Order:
        self.db.add(order)
        self.db.flush()
        for item in items:
            item.order_id = order.id
            self.db.add(item)
        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)

    def get_by_id(self, order_pk: int) -> Optional[Order]:
        return (
            self.db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.id == order_pk)
            .first()
        )

    def get_by_order_id(self, order_id: str) -> Optional[Order]:
        return (
            self.db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.order_id == order_id)
            .first()
        )

    def list_orders(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        search: Optional[str] = None,
        order_ids: Optional[set] = None,
    ) -> Tuple[List[Order], int]:
        query = self.db.query(Order).options(joinedload(Order.items))
        if order_ids is not None:
            if not order_ids:
                return [], 0
            query = query.filter(Order.order_id.in_(order_ids))
        if status:
            query = query.filter(Order.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Order.order_id.ilike(term))
                | (Order.customer_name.ilike(term))
                | (Order.phone.ilike(term))
            )
        total = query.count()
        orders = (
            query.order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return orders, total

    def list_orders_by_phone(
        self,
        phone: str,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Order], int]:
        suffix = phone_match_suffix(phone)
        if not suffix or len(suffix) < 10:
            return [], 0
        query = self.db.query(Order).options(joinedload(Order.items))
        candidates = (
            query.filter(Order.phone.ilike(f"%{suffix}%"))
            .order_by(Order.created_at.desc())
            .all()
        )
        matched = [order for order in candidates if phones_match(order.phone, phone)]
        total = len(matched)
        start = (page - 1) * page_size
        return matched[start : start + page_size], total

    def update_status(self, order_pk: int, status: str) -> Optional[Order]:
        order = self.get_by_id(order_pk)
        if not order:
            return None
        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_payment(
        self,
        order_pk: int,
        payment_status: str,
        razorpay_order_id: Optional[str] = None,
        order_status: Optional[str] = None,
    ) -> Optional[Order]:
        order = self.get_by_id(order_pk)
        if not order:
            return None
        order.payment_status = payment_status
        if razorpay_order_id is not None:
            order.razorpay_order_id = razorpay_order_id
        if order_status is not None:
            order.status = order_status
        order.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_today_orders(self) -> List[Order]:
        today = datetime.now(timezone.utc).date()
        orders = self.db.query(Order).options(joinedload(Order.items)).all()
        return [o for o in orders if o.created_at.date() == today]

    def get_all_with_items(self) -> List[Order]:
        return self.db.query(Order).options(joinedload(Order.items)).all()

    def get_revenue_by_date(self, days: int = 7) -> List[Tuple[str, float, int]]:
        orders = self.get_all_with_items()
        buckets: dict[str, dict] = {}
        for order in orders:
            date_key = order.created_at.date().isoformat()
            if date_key not in buckets:
                buckets[date_key] = {"revenue": 0.0, "orders": 0}
            if order.status not in ("Cancelled",):
                buckets[date_key]["revenue"] += order.total
                buckets[date_key]["orders"] += 1
        sorted_dates = sorted(buckets.keys(), reverse=True)[:days]
        return [
            (date_key, buckets[date_key]["revenue"], buckets[date_key]["orders"])
            for date_key in sorted(sorted_dates)
        ]

    def count_by_status(self) -> List[Tuple[str, int]]:
        results = (
            self.db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )
        return [(status, count) for status, count in results]
