from fastapi import APIRouter, Depends, status

from app.core.deps import get_user_service
from app.core.rbac import ROLE_PLATFORM, require_roles
from app.schemas.auth import TokenPayload
from app.schemas.user import UserAdminResponse, UserCreate, UserListResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users (RBAC)"])


@router.get("", response_model=UserListResponse)
def list_users(
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    return service.list_users()


@router.post("", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: UserService = Depends(get_user_service),
) -> UserAdminResponse:
    return service.create_user(payload)


@router.put("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    _: TokenPayload = Depends(require_roles(ROLE_PLATFORM)),
    service: UserService = Depends(get_user_service),
) -> UserAdminResponse:
    return service.update_user(user_id, payload)
