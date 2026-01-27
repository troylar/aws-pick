"""Presets management with JSON persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aws_pick.exceptions import PresetNotFoundError
from aws_pick.models.config import Favorite, Preset
from aws_pick.storage.json_store import JsonStore, default_config_dir

_CONFIG_FILE = "config.json"


class PresetsManager:
    """CRUD operations for persisted named presets."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self._store = JsonStore(base_dir=config_dir or default_config_dir())

    def list_names(self) -> list[str]:
        data = self._store.read(_CONFIG_FILE)
        presets: dict[str, Any] = data.get("presets", {})
        return sorted(presets.keys())

    def get(self, name: str) -> Preset:
        data = self._store.read(_CONFIG_FILE)
        presets: dict[str, Any] = data.get("presets", {})
        if name not in presets:
            raise PresetNotFoundError(f"Preset '{name}' not found")
        return Preset.from_dict(name, presets[name])

    def save(self, name: str, items: list[Favorite]) -> None:
        data = self._store.read(_CONFIG_FILE)
        presets: dict[str, Any] = data.get("presets", {})
        presets[name] = {
            "items": [item.to_dict() for item in items],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        data["presets"] = presets
        self._store.write(_CONFIG_FILE, data)

    def delete(self, name: str) -> None:
        data = self._store.read(_CONFIG_FILE)
        presets: dict[str, Any] = data.get("presets", {})
        if name not in presets:
            raise PresetNotFoundError(f"Preset '{name}' not found")
        del presets[name]
        data["presets"] = presets
        self._store.write(_CONFIG_FILE, data)


def manage_presets(*, config_dir: str | Path | None = None) -> PresetsManager:
    """Factory function to create a PresetsManager."""
    path = Path(config_dir) if isinstance(config_dir, str) else config_dir
    return PresetsManager(config_dir=path)
