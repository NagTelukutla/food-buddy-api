from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        customer_repository: Optional[CustomerRepository] = None,
    ):
        self.user_repository = user_repository
        self.customer_repository = customer_repository

    def _token_data(self, user: dict) -> dict:
        role = self.user_repository.normalize_role(user.get("role", "admin"))
        return {"sub": user["username"], "role": role}

    def _customer_flags(self, user: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
        is_customer = bool(user.get("is_customer", user.get("role") == "customer"))
        customer_id = None
        if is_customer and self.customer_repository:
            customer = self.customer_repository.get_by_user_id(user["id"])
            if customer:
                customer_id = customer["id"]
        return is_customer, customer_id

    def _token_response(self, user: dict) -> TokenResponse:
        token_data = self._token_data(user)
        role = token_data["role"]
        is_customer, customer_id = self._customer_flags(user)
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            role=role,
            is_customer=is_customer,
            customer_id=customer_id,
        )

    def tokens_for_user(self, user: dict) -> TokenResponse:
        return self._token_response(user)

    def login(self, credentials: LoginRequest) -> TokenResponse:
        user = self.user_repository.get_by_login(credentials.username)
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
        return self._token_response(user)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        if self.user_repository.get_by_username(payload.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        if self.user_repository.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user = self.user_repository.create(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role="customer",
            phone=payload.phone,
        )
        if self.customer_repository:
            self.customer_repository.create(
                {
                    "user_id": user["id"],
                    "name": payload.full_name,
                    "email": payload.email,
                    "phone": payload.phone or "",
                }
            )
        return self._token_response(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        username = payload.get("sub")
        user = self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
        return self._token_response(user)

    def get_me(self, username: str) -> UserResponse:
        user = self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        is_customer, customer_id = self._customer_flags(user)
        return UserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            email=user["email"],
            role=self.user_repository.normalize_role(user.get("role", "admin")),
            phone=user.get("phone"),
            restaurant_id=user.get("restaurant_id"),
            branch_id=user.get("branch_id"),
            is_customer=is_customer,
            customer_id=customer_id,
        )
