from collections import Counter
from typing import Any, Dict, List

from typing import Optional, Set

from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_metadata_repository import OrderMetadataRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.dashboard import (
    DashboardOrdersResponse,
    DashboardStats,
    OrdersByStatus,
    RevenueDataPoint,
    RevenueResponse,
)


class DashboardService:
    def __init__(
        self,
        order_repository: OrderRepository,
        menu_repository: MenuRepository,
        customer_repository: CustomerRepository | None = None,
        order_metadata_repository: OrderMetadataRepository | None = None,
    ):
        self.order_repository = order_repository
        self.menu_repository = menu_repository
        self.customer_repository = customer_repository
        self.order_metadata_repository = order_metadata_repository

    def _filter_orders(self, orders, restaurant_id: Optional[int]):
        if restaurant_id is None or not self.order_metadata_repository:
            return orders
        allowed = self.order_metadata_repository.list_order_ids_for_restaurant(restaurant_id)
        return [o for o in orders if o.order_id in allowed]

    def get_stats(self, restaurant_id: Optional[int] = None) -> DashboardStats:
        today_orders = self._filter_orders(
            self.order_repository.get_today_orders(), restaurant_id
        )
        completed_statuses = {"Delivered", "Prepared"}
        pending_statuses = {
            "Pending",
            "Accepted",
            "Driver Assigned",
            "Prepared",
            "Out for Delivery",
        }

        today_revenue = sum(
            o.total for o in today_orders if o.status not in ("Cancelled",)
        )
        pending = sum(1 for o in today_orders if o.status in pending_statuses)
        completed = sum(1 for o in today_orders if o.status in completed_statuses)
        avg_value = today_revenue / len(today_orders) if today_orders else 0.0

        item_counter: Counter = Counter()
        for order in today_orders:
            for item in order.items:
                item_counter[item.name] += item.quantity

        popular = [
            {"name": name, "quantity": qty}
            for name, qty in item_counter.most_common(5)
        ]

        return DashboardStats(
            today_orders=len(today_orders),
            today_revenue=round(today_revenue, 2),
            pending_orders=pending,
            completed_orders=completed,
            average_order_value=round(avg_value, 2),
            popular_items=popular,
        )

    def get_revenue(self, days: int = 7, restaurant_id: Optional[int] = None) -> RevenueResponse:
        if restaurant_id is None or not self.order_metadata_repository:
            data = self.order_repository.get_revenue_by_date(days)
        else:
            allowed = self.order_metadata_repository.list_order_ids_for_restaurant(restaurant_id)
            orders = [
                o for o in self.order_repository.get_all_with_items()
                if o.order_id in allowed and o.status != "Cancelled"
            ]
            buckets: dict[str, dict] = {}
            for order in orders:
                date_key = order.created_at.date().isoformat()
                if date_key not in buckets:
                    buckets[date_key] = {"revenue": 0.0, "orders": 0}
                buckets[date_key]["revenue"] += order.total
                buckets[date_key]["orders"] += 1
            sorted_dates = sorted(buckets.keys(), reverse=True)[:days]
            data = [
                (date_key, buckets[date_key]["revenue"], buckets[date_key]["orders"])
                for date_key in sorted(sorted_dates)
            ]
        return RevenueResponse(
            data=[
                RevenueDataPoint(date=date_key, revenue=round(revenue, 2), orders=orders)
                for date_key, revenue, orders in data
            ]
        )

    def get_orders_by_status(self, restaurant_id: Optional[int] = None) -> DashboardOrdersResponse:
        if restaurant_id is None or not self.order_metadata_repository:
            counts = self.order_repository.count_by_status()
        else:
            allowed = self.order_metadata_repository.list_order_ids_for_restaurant(restaurant_id)
            orders = [
                o for o in self.order_repository.get_all_with_items() if o.order_id in allowed
            ]
            counter: Counter = Counter(o.status for o in orders)
            counts = list(counter.items())
        return DashboardOrdersResponse(
            orders_by_status=[
                OrdersByStatus(status=status, count=count) for status, count in counts
            ]
        )

    def get_top_items(self, limit: int = 10, restaurant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        counter: Counter = Counter()
        for order in self._filter_orders(self.order_repository.get_all_with_items(), restaurant_id):
            if order.status == "Cancelled":
                continue
            for item in order.items:
                counter[item.name] += item.quantity
        return [
            {"name": name, "quantity": qty, "revenue": 0}
            for name, qty in counter.most_common(limit)
        ]

    def get_customer_metrics(self, restaurant_id: Optional[int] = None) -> Dict[str, Any]:
        orders = self._filter_orders(self.order_repository.get_all_with_items(), restaurant_id)
        phones = [o.phone for o in orders if o.status != "Cancelled"]
        unique = len(set(phones))
        repeat = len([p for p in set(phones) if phones.count(p) > 1])
        return {
            "total_customers": len(self.customer_repository.get_all()) if self.customer_repository else unique,
            "unique_order_phones": unique,
            "repeat_customers": repeat,
            "repeat_rate": round(repeat / unique, 2) if unique else 0.0,
        }
