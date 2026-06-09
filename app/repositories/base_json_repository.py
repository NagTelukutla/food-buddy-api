from typing import Any, Callable, Dict, List, Optional

from app.core.config import get_settings
from app.utils.json_store import read_json_file, write_json_file


class BaseJsonRepository:
    def __init__(self, filename: str, default: Any):
        settings = get_settings()
        self.file_path = settings.data_path / filename
        self.default = default

    def read(self) -> Any:
        return read_json_file(self.file_path, self.default)

    def write(self, data: Any) -> None:
        write_json_file(self.file_path, data)

    @staticmethod
    def next_id(items: List[Dict[str, Any]], key: str = "id") -> int:
        return max((item.get(key, 0) for item in items), default=0) + 1

    def get_collection(self, key: str) -> List[Dict[str, Any]]:
        data = self.read()
        return list(data.get(key, []))

    def save_collection(self, key: str, items: List[Dict[str, Any]]) -> None:
        data = self.read()
        data[key] = items
        self.write(data)

    def find_by_id(
        self, key: str, item_id: int, id_field: str = "id"
    ) -> Optional[Dict[str, Any]]:
        for item in self.get_collection(key):
            if item.get(id_field) == item_id:
                return item
        return None

    def create_item(
        self,
        key: str,
        item: Dict[str, Any],
        id_field: str = "id",
        before_save: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        explicit_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        items = self.get_collection(key)
        item = dict(item)
        item[id_field] = explicit_id if explicit_id is not None else self.next_id(items, id_field)
        if before_save:
            item = before_save(item)
        items.append(item)
        self.save_collection(key, items)
        return item

    def update_item(
        self, key: str, item_id: int, updates: Dict[str, Any], id_field: str = "id"
    ) -> Optional[Dict[str, Any]]:
        items = self.get_collection(key)
        for index, item in enumerate(items):
            if item.get(id_field) == item_id:
                merged = {**item, **updates, id_field: item_id}
                items[index] = merged
                self.save_collection(key, items)
                return merged
        return None

    def delete_item(self, key: str, item_id: int, id_field: str = "id") -> bool:
        items = self.get_collection(key)
        filtered = [item for item in items if item.get(id_field) != item_id]
        if len(filtered) == len(items):
            return False
        self.save_collection(key, filtered)
        return True
