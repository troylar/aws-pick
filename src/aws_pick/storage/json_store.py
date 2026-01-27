"""Persistent JSON storage with atomic writes and corruption handling."""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

logger = logging.getLogger(__name__)

_APP_NAME = "aws-pick"


def default_config_dir() -> Path:
    return Path(user_config_dir(_APP_NAME))


class JsonStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or default_config_dir()

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _ensure_dir(self) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, filename: str) -> Path:
        return self._base_dir / filename

    def read(self, filename: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        path = self._path(filename)
        if defaults is None:
            defaults = {}
        if not path.exists():
            return dict(defaults)
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data).__name__}")
            return data
        except (json.JSONDecodeError, ValueError) as exc:
            backup_path = path.with_suffix(f"{path.suffix}.corrupt.bak")
            logger.warning("Corrupt config file %s: %s. Backing up to %s", path, exc, backup_path)
            try:
                shutil.copy2(str(path), str(backup_path))
            except OSError:
                pass
            return dict(defaults)

    def write(self, filename: str, data: dict[str, Any]) -> None:
        self._ensure_dir()
        path = self._path(filename)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(str(tmp_path), str(path))
