from typing import Any, Callable, Dict, List, Optional

from app.core.config import get_settings
from app.utils.json_store import modify_json_file, read_json_file, write_json_file


class BaseJsonRepository:
    def __init__(self, filename: str, default: Any):
        settings = get_settings()
        self.file_path = settings.data_path / filename
        self.default = default

    def read(self) -> Any:
        return read_json_file(self.file_path, self.default)

    def write(self, data: Any) -> None:
        write_json_file(self.file_path, data)

    def mutate(self, mutator: Callable[[Any], Any]) -> Any:
        return modify_json_file(self.file_path, self.default, mutator)

    @staticmethod
    def next_id(items: List[Dict[str, Any]], key: str = "id") -> int:
        return max((item.get(key, 0) for item in items), default=0) + 1

    def get_collection(self, key: str) -> List[Dict[str, Any]]:
        data = self.read()
        return list(data.get(key, []))

    def save_collection(self, key: str, items: List[Dict[str, Any]]) -> None:
        def mutator(data: Dict[str, Any]) -> Dict[str, Any]:
            payload = dict(data) if isinstance(data, dict) else dict(self.default)
            payload[key] = items
            return payload

        self.mutate(mutator)

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
        created: Dict[str, Any] = {}

        def mutator(data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal created
            payload = dict(data) if isinstance(data, dict) else dict(self.default)
            items = list(payload.get(key, []))
            new_item = dict(item)
            new_item[id_field] = (
                explicit_id if explicit_id is not None else self.next_id(items, id_field)
            )
            if before_save:
                new_item = before_save(new_item)
            items.append(new_item)
            payload[key] = items
            created = new_item
            return payload

        self.mutate(mutator)
        return created

    def update_item(
        self, key: str, item_id: int, updates: Dict[str, Any], id_field: str = "id"
    ) -> Optional[Dict[str, Any]]:
        updated: Optional[Dict[str, Any]] = None

        def mutator(data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal updated
            payload = dict(data) if isinstance(data, dict) else dict(self.default)
            items = list(payload.get(key, []))
            for index, item in enumerate(items):
                if item.get(id_field) == item_id:
                    merged = {**item, **updates, id_field: item_id}
                    items[index] = merged
                    payload[key] = items
                    updated = merged
                    return payload
            return payload

        self.mutate(mutator)
        return updated

    def delete_item(self, key: str, item_id: int, id_field: str = "id") -> bool:
        deleted = False

        def mutator(data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal deleted
            payload = dict(data) if isinstance(data, dict) else dict(self.default)
            items = list(payload.get(key, []))
            filtered = [item for item in items if item.get(id_field) != item_id]
            if len(filtered) == len(items):
                return payload
            deleted = True
            payload[key] = filtered
            return payload

        self.mutate(mutator)
        return deleted
