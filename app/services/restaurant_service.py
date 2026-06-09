from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.repositories.branch_repository import BranchRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.repositories.user_repository import UserRepository
from app.schemas.branch import BranchCreate, BranchResponse
from app.schemas.restaurant import RestaurantCreate, RestaurantResponse, RestaurantUpdate
from app.schemas.user import (
    RestaurantAdminListResponse,
    RestaurantAdminMapRequest,
    RestaurantAdminOption,
    RestaurantOnboardRequest,
    RestaurantOnboardResponse,
)


class RestaurantService:
    def __init__(
        self,
        restaurant_repo: RestaurantRepository,
        branch_repo: BranchRepository,
        user_repo: UserRepository | None = None,
    ):
        self.restaurant_repo = restaurant_repo
        self.branch_repo = branch_repo
        self.user_repo = user_repo

    def _to_response(self, data: Dict[str, Any]) -> RestaurantResponse:
        return RestaurantResponse(**data)

    def list_restaurants(self, active_only: bool = True) -> List[RestaurantResponse]:
        return [self._to_response(r) for r in self.restaurant_repo.get_all(active_only)]

    def get_restaurant(self, restaurant_id: int) -> RestaurantResponse:
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
        return self._to_response(restaurant)

    def create_restaurant(self, payload: RestaurantCreate) -> RestaurantResponse:
        data = payload.model_dump()
        if payload.hero_slides:
            data["hero_slides"] = [s.model_dump() for s in payload.hero_slides]
        created = self.restaurant_repo.create(data)
        if payload.address:
            self.branch_repo.create(
                {
                    "restaurant_id": created["id"],
                    "name": f"{created['name']} — Main",
                    "address": payload.address,
                    "phone": payload.phone,
                    "email": payload.email,
                    "working_hours": payload.working_hours,
                }
            )
        return self._to_response(created)

    def update_restaurant(self, restaurant_id: int, payload: RestaurantUpdate) -> RestaurantResponse:
        updates = payload.model_dump(exclude_unset=True)
        if "hero_slides" in updates and updates["hero_slides"] is not None:
            updates["hero_slides"] = [
                s.model_dump() if hasattr(s, "model_dump") else s for s in updates["hero_slides"]
            ]
        updated = self.restaurant_repo.update(restaurant_id, updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
        return self._to_response(updated)

    def list_branches(self, restaurant_id: int) -> List[BranchResponse]:
        if not self.restaurant_repo.get_by_id(restaurant_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
        return [BranchResponse(**b) for b in self.branch_repo.get_by_restaurant(restaurant_id)]

    def create_branch(self, payload: BranchCreate) -> BranchResponse:
        if not self.restaurant_repo.get_by_id(payload.restaurant_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
        created = self.branch_repo.create(payload.model_dump())
        return BranchResponse(**created)

    def onboard_restaurant(self, payload: RestaurantOnboardRequest) -> RestaurantOnboardResponse:
        if not self.user_repo:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User service unavailable")
        if self.user_repo.get_by_username(payload.owner_username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner username already exists")
        if self.user_repo.get_by_email(payload.owner_email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner email already registered")

        owner = self.user_repo.create(
            username=payload.owner_username,
            email=payload.owner_email,
            password=payload.owner_password,
            full_name=payload.owner_full_name,
            role="admin",
            phone=payload.owner_phone,
        )

        restaurant = self.restaurant_repo.create(
            {
                "name": payload.restaurant_name,
                "email": payload.email,
                "phone": payload.phone,
                "address": payload.address,
                "tagline": payload.tagline,
                "cuisine_type": payload.cuisine_type,
                "working_hours": payload.working_hours,
                "owner_user_id": owner["id"],
            }
        )

        branch = self.branch_repo.create(
            {
                "restaurant_id": restaurant["id"],
                "name": f"{restaurant['name']} — Main",
                "address": payload.address,
                "phone": payload.phone,
                "email": payload.email,
                "working_hours": payload.working_hours,
            }
        )

        self.user_repo.update(
            owner["id"],
            {"restaurant_id": restaurant["id"], "branch_id": branch["id"]},
        )

        return RestaurantOnboardResponse(
            restaurant_id=restaurant["id"],
            branch_id=branch["id"],
            owner_user_id=owner["id"],
            restaurant_name=restaurant["name"],
            owner_username=owner["username"],
        )

    def get_restaurant_admins(self, restaurant_id: int) -> RestaurantAdminListResponse:
        if not self.user_repo:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User service unavailable")
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

        admins = self.user_repo.list_by_role("admin")
        mapped_ids = [
            u["id"] for u in admins if u.get("restaurant_id") == restaurant_id and u.get("is_active", True)
        ]
        items = [
            RestaurantAdminOption(
                id=u["id"],
                username=u["username"],
                full_name=u["full_name"],
                email=u["email"],
                phone=u.get("phone"),
                is_mapped=u["id"] in mapped_ids,
                is_active=u.get("is_active", True),
            )
            for u in admins
        ]
        return RestaurantAdminListResponse(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant["name"],
            mapped_admin_ids=mapped_ids,
            items=items,
        )

    def map_restaurant_admins(
        self, restaurant_id: int, payload: RestaurantAdminMapRequest
    ) -> RestaurantAdminListResponse:
        if not self.user_repo:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User service unavailable")
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

        admin_ids = set(payload.admin_ids)
        for admin_id in admin_ids:
            user = self.user_repo.get_by_id(admin_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {admin_id} not found",
                )
            if user.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {user['username']} is not an admin account",
                )
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {user['username']} is inactive",
                )

        branches = self.branch_repo.get_by_restaurant(restaurant_id)
        default_branch_id = branches[0]["id"] if branches else None

        for user in self.user_repo.list_by_role("admin"):
            if user.get("restaurant_id") == restaurant_id and user["id"] not in admin_ids:
                self.user_repo.update(user["id"], {"restaurant_id": None, "branch_id": None})

        for admin_id in admin_ids:
            self.user_repo.update(
                admin_id,
                {"restaurant_id": restaurant_id, "branch_id": default_branch_id},
            )

        return self.get_restaurant_admins(restaurant_id)
