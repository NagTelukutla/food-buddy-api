import hashlib
import json
import urllib.parse
import urllib.request
from typing import Tuple

from app.core.config import get_settings


def _fallback_coords(address: str, base_lat: float, base_lng: float) -> Tuple[float, float]:
    digest = hashlib.md5(address.strip().lower().encode()).hexdigest()
    h1 = int(digest[:8], 16)
    h2 = int(digest[8:16], 16)
    lat = base_lat + ((h1 % 1000) - 500) / 80000
    lng = base_lng + ((h2 % 1000) - 500) / 80000
    return round(lat, 6), round(lng, 6)


def geocode_address(
    address: str,
    fallback_lat: float | None = None,
    fallback_lng: float | None = None,
) -> Tuple[float, float]:
    """Resolve address to coordinates. Uses Nominatim with deterministic fallback."""
    settings = get_settings()
    if fallback_lat is None or fallback_lng is None:
        raise ValueError("Dynamic base coordinates must be provided for geocoding")
    
    base_lat = fallback_lat
    base_lng = fallback_lng

    if not address or not address.strip():
        return base_lat, base_lng
    try:
        query = urllib.parse.quote(address.strip())
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": settings.geocode_user_agent})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            if data:
                return round(float(data[0]["lat"]), 6), round(float(data[0]["lon"]), 6)
    except Exception:
        pass
    return _fallback_coords(address, base_lat, base_lng)
