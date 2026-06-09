from typing import Any, Dict, List, Optional

from app.repositories.base_json_repository import BaseJsonRepository
from app.schemas.menu import VALID_CATEGORIES


class MenuRepository(BaseJsonRepository):
    def __init__(self):
        super().__init__("menu.json", {"items": [], "categories": VALID_CATEGORIES})

    @staticmethod
    def _item_restaurant_id(item: Dict[str, Any]) -> int:
        return int(item.get("restaurant_id") or 1)

    def get_all_items(self, restaurant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        items = self.read().get("items", [])
        if restaurant_id is None:
            return items
        return [item for item in items if self._item_restaurant_id(item) == restaurant_id]

    def get_categories(self) -> List[str]:
        data = self.read()
        return data.get("categories", VALID_CATEGORIES)

    def get_by_id(
        self, item_id: int, restaurant_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        for item in self.get_all_items(restaurant_id):
            if item.get("id") == item_id:
                return item
        if restaurant_id is not None:
            return None
        for item in self.get_all_items():
            if item.get("id") == item_id:
                return item
        return None

    def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        data = self.read()
        items = data.get("items", [])
        next_id = max((i.get("id", 0) for i in items), default=0) + 1
        item["id"] = next_id
        items.append(item)
        data["items"] = items
        self.write(data)
        return item

    def update(self, item_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = self.read()
        items = data.get("items", [])
        for index, item in enumerate(items):
            if item.get("id") == item_id:
                items[index] = {**item, **updates, "id": item_id}
                data["items"] = items
                self.write(data)
                return items[index]
        return None

    def delete(self, item_id: int) -> bool:
        data = self.read()
        items = data.get("items", [])
        filtered = [item for item in items if item.get("id") != item_id]
        if len(filtered) == len(items):
            return False
        data["items"] = filtered
        self.write(data)
        return True
