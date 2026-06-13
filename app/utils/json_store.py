import json
import logging
import shutil
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _file_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def _backup_path(path: Path) -> Path:
    return path.with_suffix(f"{path.suffix}.bak")


def _load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def _parse_json_text(text: str) -> Any:
    """Parse JSON, ignoring accidental trailing content after the root value."""
    stripped = text.strip()
    if not stripped:
        raise json.JSONDecodeError("Empty file", text, 0)
    decoder = json.JSONDecoder()
    value, end = decoder.raw_decode(stripped)
    trailing = stripped[end:].strip()
    if trailing:
        logger.warning("Ignored trailing content after JSON root (%d chars)", len(trailing))
    return value


def _load_unlocked(path: Path, default: T) -> T:
    if not path.exists():
        return deepcopy(default)
    try:
        return _parse_json_text(_load_text(path))
    except json.JSONDecodeError as exc:
        backup = _backup_path(path)
        if backup.exists():
            try:
                data = _parse_json_text(_load_text(backup))
                logger.warning("Recovered %s from backup after parse error: %s", path.name, exc)
                _save_unlocked(path, data)
                return data
            except (json.JSONDecodeError, OSError):
                pass
        logger.error("JSON parse failed for %s: %s — resetting to default", path.name, exc)
        _save_unlocked(path, deepcopy(default))
        return deepcopy(default)


def _save_unlocked(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            shutil.copy2(path, _backup_path(path))
        except OSError:
            pass
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.flush()
    tmp_path.replace(path)


def read_json_file(path: Path, default: T) -> T:
    with _file_lock(path):
        return _load_unlocked(path, default)


def write_json_file(path: Path, data: Any) -> None:
    with _file_lock(path):
        _save_unlocked(path, data)


def modify_json_file(path: Path, default: T, mutator: Callable[[T], T]) -> T:
    """Atomically read, mutate, and write a JSON file under a single lock."""
    with _file_lock(path):
        data = _load_unlocked(path, default)
        updated = mutator(deepcopy(data))
        _save_unlocked(path, updated)
        return updated
