"""Favorites management with JSON persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aws_pick.models.config import Favorite
from aws_pick.storage.json_store import JsonStore, default_config_dir

_CONFIG_FILE = "config.json"


class FavoritesManager:
    """CRUD operations for persisted favorites."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self._store = JsonStore(base_dir=config_dir or default_config_dir())

    def list(self) -> list[Favorite]:
        data = self._store.read(_CONFIG_FILE)
        raw: list[dict[str, Any]] = data.get("favorites", [])
        return [Favorite.from_dict(item) for item in raw]

    def add(self, account_id: str, role_name: str) -> None:
        if self.is_favorite(account_id, role_name):
            return
        data = self._store.read(_CONFIG_FILE)
        favorites: list[dict[str, Any]] = data.get("favorites", [])
        favorites.append({"account_id": account_id, "role_name": role_name})
        data["favorites"] = favorites
        self._store.write(_CONFIG_FILE, data)

    def remove(self, account_id: str, role_name: str) -> None:
        data = self._store.read(_CONFIG_FILE)
        favorites: list[dict[str, Any]] = data.get("favorites", [])
        data["favorites"] = [
            f for f in favorites if not (f.get("account_id") == account_id and f.get("role_name") == role_name)
        ]
        self._store.write(_CONFIG_FILE, data)

    def clear(self) -> None:
        data = self._store.read(_CONFIG_FILE)
        data["favorites"] = []
        self._store.write(_CONFIG_FILE, data)

    def is_favorite(self, account_id: str, role_name: str) -> bool:
        return any(f.account_id == account_id and f.role_name == role_name for f in self.list())


def manage_favorites(*, config_dir: str | Path | None = None) -> FavoritesManager:
    """Factory function to create a FavoritesManager."""
    path = Path(config_dir) if isinstance(config_dir, str) else config_dir
    return FavoritesManager(config_dir=path)
