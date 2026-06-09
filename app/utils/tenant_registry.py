"""Collect tenant ids already in use across JSON data stores."""

from pathlib import Path
from typing import Set

from app.core.config import get_settings
from app.utils.json_store import read_json_file


def collect_used_tenant_ids() -> Set[int]:
    """Return all restaurant/branch ids and user-assigned tenant ids."""
    settings = get_settings()
    data_dir: Path = settings.data_path
    used: Set[int] = set()

    restaurants = read_json_file(data_dir / "restaurants.json", {"restaurants": []})
    for row in restaurants.get("restaurants", []):
        if row.get("id") is not None:
            used.add(int(row["id"]))

    branches = read_json_file(data_dir / "branches.json", {"branches": []})
    for row in branches.get("branches", []):
        if row.get("id") is not None:
            used.add(int(row["id"]))

    users = read_json_file(data_dir / "users.json", {"users": []})
    for row in users.get("users", []):
        if row.get("restaurant_id") is not None:
            used.add(int(row["restaurant_id"]))
        if row.get("branch_id") is not None:
            used.add(int(row["branch_id"]))

    return used
