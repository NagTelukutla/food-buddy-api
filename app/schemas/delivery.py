from typing import List, Literal, Optional

from pydantic import BaseModel, Field

DeliveryStatus = Literal[
    "pending_acceptance",
    "accepted",
    "out_for_delivery",
    "delivered",
    "picked_up",
    "in_transit",
]
PartnerStatus = Literal["available", "busy", "offline"]
VehicleType = Literal["bike", "scooter", "car", "bicycle"]


class DeliveryPartnerCreate(BaseModel):
    restaurant_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=10, max_length=20)
    user_id: Optional[int] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_number: Optional[str] = None
    status: PartnerStatus = "offline"


class DeliveryPartnerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_number: Optional[str] = None
    status: Optional[PartnerStatus] = None
    is_active: Optional[bool] = None


class DeliveryPartnerResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    name: str
    phone: str
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    status: str
    is_active: bool = True
    created_at: str
    updated_at: str


class DeliveryAssignRequest(BaseModel):
    delivery_partner_id: int


class DeliveryAssignmentResponse(BaseModel):
    id: int
    order_id: str
    delivery_partner_id: Optional[int] = None
    delivery_status: str
    created_at: str
    updated_at: str


class DeliveryOrderItemSummary(BaseModel):
    name: str
    quantity: int
    line_total: float


class DeliveryAssignmentDetailResponse(BaseModel):
    id: int
    order_id: str
    delivery_partner_id: Optional[int] = None
    delivery_status: str
    created_at: str
    updated_at: str
    customer_name: str
    phone: str
    delivery_address: Optional[str] = None
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    order_status: str
    order_type: str
    total: float
    notes: Optional[str] = None
    items: List[DeliveryOrderItemSummary]
    driver_name: Optional[str] = None
    restaurant_name: Optional[str] = None
    restaurant_address: Optional[str] = None
    restaurant_lat: Optional[float] = None
    restaurant_lng: Optional[float] = None
    distance_km: Optional[float] = None


class DeliveryStatusUpdate(BaseModel):
    delivery_status: DeliveryStatus


class DeliveryAcceptRequest(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=32)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class DeliveryStatusByOrderRequest(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=32)
    delivery_status: DeliveryStatus


class DeliveryAssignmentListResponse(BaseModel):
    items: List[DeliveryAssignmentDetailResponse]


class DeliveryReportResponse(BaseModel):
    total: int
    completed: int
    failed: int


class DriverLocationUpdate(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=32)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DriverPartnerLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class MapPoint(BaseModel):
    latitude: float
    longitude: float
    label: Optional[str] = None


class DriverLiveLocation(BaseModel):
    latitude: float
    longitude: float
    updated_at: str
    partner_name: Optional[str] = None


class DeliveryLiveTrackResponse(BaseModel):
    order_id: str
    order_status: str
    delivery_status: Optional[str] = None
    live_tracking_enabled: bool = False
    delivery_address: Optional[str] = None
    restaurant_name: Optional[str] = None
    restaurant: MapPoint
    destination: Optional[MapPoint] = None
    driver: Optional[DriverLiveLocation] = None
