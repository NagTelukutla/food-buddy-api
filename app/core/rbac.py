from typing import Callable, FrozenSet

from fastapi import Depends, HTTPException, status

from app.schemas.auth import TokenPayload

ROLE_CUSTOMER = "customer"
ROLE_ADMIN = "admin"
ROLE_DRIVER = "driver"
ROLE_PLATFORM = "platform"

VALID_ROLES = frozenset({ROLE_CUSTOMER, ROLE_ADMIN, ROLE_DRIVER, ROLE_PLATFORM})

# Legacy role values stored in older tokens / data
ROLE_ALIASES = {
    "restaurant_owner": ROLE_ADMIN,
    "platform_admin": ROLE_PLATFORM,
    "delivery_partner": ROLE_DRIVER,
}

ADMIN_ROLES = frozenset({ROLE_ADMIN})

NON_CUSTOMER_ORDER_ROLES = frozenset({ROLE_ADMIN, ROLE_DRIVER, ROLE_PLATFORM})


def normalize_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def require_roles(*allowed: str) -> Callable:
    from app.core.deps import get_current_user_payload

    allowed_set: FrozenSet[str] = frozenset(normalize_role(r) for r in allowed)

    def checker(current_user: TokenPayload = Depends(get_current_user_payload)) -> TokenPayload:
        role = normalize_role(current_user.role)
        if role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker
