from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.core.security import get_password_hash
from app.repositories.branch_repository import BranchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAdminResponse, UserCreate, UserListResponse, UserUpdate

VALID_ROLES = {"customer", "admin", "driver", "platform"}


class UserService:
    def __init__(self, user_repo: UserRepository, branch_repo: BranchRepository | None = None):
        self.user_repo = user_repo
        self.branch_repo = branch_repo

    def _resolve_driver_branch_id(self, restaurant_id: int | None) -> int | None:
        if restaurant_id is None or not self.branch_repo:
            return None
        branches = self.branch_repo.get_by_restaurant(restaurant_id, active_only=True)
        if not branches:
            branches = self.branch_repo.get_by_restaurant(restaurant_id)
        return branches[0]["id"] if branches else None

    @staticmethod
    def _to_response(user: Dict[str, Any]) -> UserAdminResponse:
        return UserAdminResponse(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            email=user["email"],
            role=user.get("role", "customer"),
            phone=user.get("phone"),
            restaurant_id=user.get("restaurant_id"),
            branch_id=user.get("branch_id"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
        )

    def list_users(self) -> UserListResponse:
        items = [
            self._to_response(u)
            for u in self.user_repo.get_all()
            if u.get("role") != "platform"
        ]
        return UserListResponse(items=items, total=len(items))

    def create_user(self, payload: UserCreate) -> UserAdminResponse:
        if payload.role == "platform":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super Admin accounts cannot be created from the platform UI",
            )
        if self.user_repo.get_by_username(payload.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        if self.user_repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        restaurant_id = payload.restaurant_id
        branch_id = payload.branch_id
        if payload.role == "admin":
            restaurant_id = None
            branch_id = None
        elif payload.role == "driver":
            restaurant_id = None
            branch_id = None
        created = self.user_repo.create(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            phone=payload.phone,
            restaurant_id=restaurant_id,
            branch_id=branch_id,
        )
        return self._to_response(created)

    def update_user(self, user_id: int, payload: UserUpdate) -> UserAdminResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        updates = payload.model_dump(exclude_unset=True)
        if updates.get("role") == "platform":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign Super Admin role from the platform UI",
            )
        if user.get("role") == "platform":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super Admin accounts cannot be modified from the Users screen",
            )
        if "email" in updates and updates["email"]:
            existing = self.user_repo.get_by_email(updates["email"])
            if existing and existing["id"] != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        if "password" in updates and updates["password"]:
            updates["password_hash"] = get_password_hash(updates.pop("password"))
        effective_role = updates.get("role", user.get("role"))
        if effective_role == "admin":
            updates.pop("restaurant_id", None)
            updates.pop("branch_id", None)
        elif effective_role == "driver":
            updates["restaurant_id"] = None
            updates["branch_id"] = None
        updated = self.user_repo.update(user_id, updates)
        return self._to_response(updated)
