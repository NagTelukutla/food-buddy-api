"""Copy bundled JSON files into DATA_DIR on first production startup (Render disk)."""

import shutil
from pathlib import Path

from app.core.config import get_settings


def bootstrap_json_data() -> None:
    """Seed persistent DATA_DIR from repo `data/` when empty (first deploy on Render)."""
    settings = get_settings()
    target = settings.data_path
    source = settings.base_dir / "data"

    target.mkdir(parents=True, exist_ok=True)

    if any(target.glob("*.json")):
        return

    if not source.is_dir():
        return

    for json_file in source.glob("*.json"):
        dest = target / json_file.name
        if not dest.exists():
            shutil.copy2(json_file, dest)
