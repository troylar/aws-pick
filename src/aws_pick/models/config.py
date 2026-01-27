"""Data models for persisted configuration (favorites, presets, history)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Favorite:
    account_id: str
    role_name: str

    def to_dict(self) -> dict[str, str]:
        return {"account_id": self.account_id, "role_name": self.role_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Favorite:
        return cls(account_id=str(data["account_id"]), role_name=str(data["role_name"]))


@dataclass(frozen=True)
class Preset:
    name: str
    items: tuple[Favorite, ...] = field(default_factory=tuple)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> Preset:
        items = tuple(Favorite.from_dict(item) for item in data.get("items", []))
        return cls(name=name, items=items, created_at=data.get("created_at", ""))


@dataclass(frozen=True)
class HistoryEntry:
    account_id: str
    role_name: str
    last_used: str

    def to_dict(self) -> dict[str, str]:
        return {"account_id": self.account_id, "role_name": self.role_name, "last_used": self.last_used}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        return cls(
            account_id=str(data["account_id"]),
            role_name=str(data["role_name"]),
            last_used=str(data["last_used"]),
        )


@dataclass(frozen=True)
class EnvironmentPattern:
    pattern: str
    environment: str
    color: str

    def to_dict(self) -> dict[str, str]:
        return {"pattern": self.pattern, "environment": self.environment, "color": self.color}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentPattern:
        return cls(pattern=str(data["pattern"]), environment=str(data["environment"]), color=str(data["color"]))
