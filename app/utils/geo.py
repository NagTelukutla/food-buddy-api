"""Lightweight geo helpers for Haversine distance calculations."""

import math
from typing import Optional

EARTH_RADIUS_KM = 6371.0


def is_valid_coord(lat: Optional[float], lng: Optional[float]) -> bool:
    if lat is None or lng is None:
        return False
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lat_f) and math.isfinite(lng_f) and abs(lat_f) <= 90 and abs(lng_f) <= 180


def distance_km(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
) -> float:
    """Great-circle distance in kilometres between two lat/lng points."""
    if not is_valid_coord(from_lat, from_lng) or not is_valid_coord(to_lat, to_lng):
        return math.inf
    d_lat = math.radians(to_lat - from_lat)
    d_lng = math.radians(to_lng - from_lng)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(from_lat))
        * math.cos(math.radians(to_lat))
        * math.sin(d_lng / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
