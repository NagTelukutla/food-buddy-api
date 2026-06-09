"""Random 10-digit tenant identifiers for restaurants and branches."""

import secrets
from typing import Iterable, Set


def generate_tenant_id(used_ids: Iterable[int]) -> int:
    """
    Generate a unique random 10-digit integer (1_000_000_000 – 9_999_999_999).
    """
    used: Set[int] = {int(x) for x in used_ids if x is not None}
    for _ in range(100):
        candidate = secrets.randbelow(9_000_000_000) + 1_000_000_000
        if candidate not in used:
            return candidate
    raise RuntimeError("Unable to generate a unique 10-digit tenant id")
