from typing import Any, Dict

from app.repositories.base_json_repository import BaseJsonRepository


class SettingsRepository(BaseJsonRepository):
    def __init__(self):
        super().__init__("settings.json", {})

    def get_settings(self) -> Dict[str, Any]:
        return self.read()
