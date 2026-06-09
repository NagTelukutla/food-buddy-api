from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_auth_service, get_current_user_payload, get_customer_service
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPayload, TokenResponse, UserResponse
from app.schemas.customer import CustomerRegister, CustomerResponse
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.register(payload)


@router.post("/register/customer", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_customer(
    payload: CustomerRegister,
    customer_service: CustomerService = Depends(get_customer_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    customer_service.register(payload)
    user = auth_service.user_repository.get_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")
    return auth_service.tokens_for_user(user)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.login(credentials)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.refresh(body.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: TokenPayload = Depends(get_current_user_payload),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return auth_service.get_me(current_user.username)
