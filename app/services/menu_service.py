from typing import List, Optional

from fastapi import HTTPException, status

from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.menu_repository import MenuRepository
from app.schemas.menu import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
    MenuListResponse,
)


class MenuService:
    def __init__(self, menu_repository: MenuRepository, audit_repository: AuditLogRepository):
        self.menu_repository = menu_repository
        self.audit_repository = audit_repository

    def list_menu(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        available_only: bool = False,
        restaurant_id: Optional[int] = None,
    ) -> MenuListResponse:
        items = self.menu_repository.get_all_items(restaurant_id)
        if search:
            term = search.lower()
            items = [
                item
                for item in items
                if term in item.get("name", "").lower()
                or term in item.get("description", "").lower()
            ]
        if category:
            items = [item for item in items if item.get("category") == category]
        if available_only:
            items = [item for item in items if item.get("available", True)]
        return MenuListResponse(
            items=[MenuItemResponse(**item) for item in items],
            categories=self.menu_repository.get_categories(),
        )

    def get_item(self, item_id: int, restaurant_id: Optional[int] = None) -> MenuItemResponse:
        item = self.menu_repository.get_by_id(item_id, restaurant_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        return MenuItemResponse(**item)

    def create_item(
        self,
        payload: MenuItemCreate,
        user: Optional[str] = None,
        restaurant_id: Optional[int] = None,
    ) -> MenuItemResponse:
        data = payload.model_dump()
        if restaurant_id is not None:
            data["restaurant_id"] = restaurant_id
        created = self.menu_repository.create(data)
        self.audit_repository.create(
            action="CREATE",
            entity_type="menu",
            entity_id=str(created["id"]),
            user=user,
            details=f"Created menu item: {created['name']}",
        )
        return MenuItemResponse(**created)

    def update_item(
        self,
        item_id: int,
        payload: MenuItemUpdate,
        user: Optional[str] = None,
        restaurant_id: Optional[int] = None,
    ) -> MenuItemResponse:
        if restaurant_id is not None and not self.menu_repository.get_by_id(item_id, restaurant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Menu item not in your restaurant")
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return self.get_item(item_id, restaurant_id)
        updated = self.menu_repository.update(item_id, updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        self.audit_repository.create(
            action="UPDATE",
            entity_type="menu",
            entity_id=str(item_id),
            user=user,
            details=f"Updated menu item: {updated['name']}",
        )
        return MenuItemResponse(**updated)

    def delete_item(
        self, item_id: int, user: Optional[str] = None, restaurant_id: Optional[int] = None
    ) -> None:
        if restaurant_id is not None and not self.menu_repository.get_by_id(item_id, restaurant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Menu item not in your restaurant")
        deleted = self.menu_repository.delete(item_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        self.audit_repository.create(
            action="DELETE",
            entity_type="menu",
            entity_id=str(item_id),
            user=user,
            details=f"Deleted menu item id: {item_id}",
        )
