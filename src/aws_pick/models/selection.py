"""Data models for selection results and login outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoginResult:
    success: bool
    error: str | None = None


@dataclass
class ItemLoginResult:
    account_id: str
    account_name: str
    role_name: str
    success: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "role_name": self.role_name,
            "success": self.success,
        }
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BatchLoginResult:
    results: list[ItemLoginResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
        }


@dataclass
class SelectionResult:
    selected: list[dict[str, Any]] = field(default_factory=list)
    cancelled: bool = False
    login_results: BatchLoginResult | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "selected": self.selected,
            "count": len(self.selected),
            "cancelled": self.cancelled,
        }
        if self.login_results is not None:
            d["login_results"] = self.login_results.to_dict()
        return d
