from typing import Any, Dict, List, Optional

from app.core.security import get_password_hash
from app.repositories.base_json_repository import BaseJsonRepository
from app.utils.datetime_util import utc_now_iso


class UserRepository(BaseJsonRepository):
    COLLECTION = "users"

    def __init__(self):
        super().__init__("users.json", {"users": []})

    def get_all(self) -> List[Dict[str, Any]]:
        return self.get_collection(self.COLLECTION)

    @staticmethod
    def normalize_username(username: str) -> str:
        return username.strip().lower().replace(" ", "")

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        key = self.normalize_username(username)
        for user in self.get_all():
            if self.normalize_username(user.get("username", "")) == key:
                return user
        return None

    def get_by_login(self, identity: str) -> Optional[Dict[str, Any]]:
        """Resolve a user by username or email (login forms often use either)."""
        user = self.get_by_username(identity)
        if user:
            return user
        return self.get_by_email(identity)

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for user in self.get_all():
            if user.get("email", "").lower() == email.lower():
                return user
        return None

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.find_by_id(self.COLLECTION, user_id)

    def list_by_role(self, role: str) -> List[Dict[str, Any]]:
        return [u for u in self.get_all() if u.get("role") == role]

    def list_admins_for_restaurant(self, restaurant_id: int) -> List[Dict[str, Any]]:
        return [
            u
            for u in self.get_all()
            if u.get("role") == "admin" and u.get("restaurant_id") == restaurant_id
        ]

    def create(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "customer",
        phone: Optional[str] = None,
        restaurant_id: Optional[int] = None,
        branch_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        normalized_username = self.normalize_username(username)
        payload = {
            "username": normalized_username,
            "email": email,
            "password_hash": get_password_hash(password),
            "full_name": full_name,
            "phone": phone,
            "role": role,
            "is_customer": role == "customer",
            "restaurant_id": restaurant_id,
            "branch_id": branch_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        return self.create_item(self.COLLECTION, payload)

    def update(self, user_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = {**updates, "updated_at": utc_now_iso()}
        return self.update_item(self.COLLECTION, user_id, updates)

    def normalize_role(self, role: str) -> str:
        from app.core.rbac import normalize_role

        return normalize_role(role)
