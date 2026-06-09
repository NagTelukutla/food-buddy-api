from typing import Any, Dict, List

from pydantic import BaseModel


class DashboardStats(BaseModel):
    today_orders: int
    today_revenue: float
    pending_orders: int
    completed_orders: int
    average_order_value: float
    popular_items: List[Dict[str, Any]]


class RevenueDataPoint(BaseModel):
    date: str
    revenue: float
    orders: int


class RevenueResponse(BaseModel):
    data: List[RevenueDataPoint]


class OrdersByStatus(BaseModel):
    status: str
    count: int


class DashboardOrdersResponse(BaseModel):
    orders_by_status: List[OrdersByStatus]


class TopItemStat(BaseModel):
    name: str
    quantity: int
    revenue: float = 0


class TopItemsResponse(BaseModel):
    items: List[TopItemStat]


class CustomerMetricsResponse(BaseModel):
    total_customers: int
    unique_order_phones: int
    repeat_customers: int
    repeat_rate: float
