from fastapi import HTTPException, status

from app.repositories.customer_repository import CustomerRepository
from app.repositories.loyalty_repository import LoyaltyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.customer import (
    CustomerRegister,
    CustomerResponse,
    CustomerUpdate,
    LoyaltySummaryResponse,
    LoyaltyTransactionResponse,
)


class CustomerService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        user_repo: UserRepository,
        loyalty_repo: LoyaltyRepository,
    ):
        self.customer_repo = customer_repo
        self.user_repo = user_repo
        self.loyalty_repo = loyalty_repo

    def register(self, payload: CustomerRegister) -> CustomerResponse:
        if self.user_repo.get_by_username(payload.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        if self.user_repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user = self.user_repo.create(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role="customer",
            phone=payload.phone,
        )
        customer = self.customer_repo.create(
            {
                "user_id": user["id"],
                "name": payload.full_name,
                "email": payload.email,
                "phone": payload.phone or "",
            }
        )
        return CustomerResponse(**customer)

    def get_profile_by_user(self, username: str) -> CustomerResponse:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        customer = self.customer_repo.get_by_user_id(user["id"])
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")
        return CustomerResponse(**customer)

    def update_profile(self, username: str, payload: CustomerUpdate) -> CustomerResponse:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        customer = self.customer_repo.get_by_user_id(user["id"])
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer profile not found")
        updates = payload.model_dump(exclude_unset=True)
        if "addresses" in updates and updates["addresses"] is not None:
            updates["addresses"] = [a.model_dump() for a in payload.addresses]
        updated = self.customer_repo.update(customer["id"], updates)
        return CustomerResponse(**updated)

    def get_loyalty(self, username: str) -> LoyaltySummaryResponse:
        profile = self.get_profile_by_user(username)
        transactions = self.loyalty_repo.list_for_customer(profile.id)
        return LoyaltySummaryResponse(
            balance=profile.loyalty_points_balance,
            transactions=[LoyaltyTransactionResponse(**t) for t in transactions],
        )
