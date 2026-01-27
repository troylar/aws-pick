"""Data models for AWS accounts and roles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aws_pick.exceptions import InvalidAccountError

_ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")


@dataclass(frozen=True)
class AwsAccount:
    account_id: str
    account_name: str
    environment: str | None = None

    def __post_init__(self) -> None:
        if not _ACCOUNT_ID_PATTERN.match(self.account_id):
            raise InvalidAccountError(f"account_id must be 12 digits, got '{self.account_id}'")
        if not self.account_name.strip():
            raise InvalidAccountError("account_name must not be empty")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"account_id": self.account_id, "account_name": self.account_name}
        if self.environment is not None:
            d["environment"] = self.environment
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AwsAccount:
        return cls(
            account_id=str(data["account_id"]),
            account_name=str(data["account_name"]),
            environment=data.get("environment"),
        )


@dataclass(frozen=True)
class AwsRole:
    role_name: str

    def __post_init__(self) -> None:
        if not self.role_name.strip():
            raise InvalidAccountError("role_name must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {"role_name": self.role_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AwsRole:
        return cls(role_name=str(data["role_name"]))


@dataclass(frozen=True)
class AccountRole:
    account: AwsAccount
    role: AwsRole

    @property
    def key(self) -> tuple[str, str]:
        return (self.account.account_id, self.role.role_name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account.account_id,
            "account_name": self.account.account_name,
            "role_name": self.role.role_name,
            **({"environment": self.account.environment} if self.account.environment else {}),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountRole:
        return cls(
            account=AwsAccount(
                account_id=str(data["account_id"]),
                account_name=str(data["account_name"]),
                environment=data.get("environment"),
            ),
            role=AwsRole(role_name=str(data["role_name"])),
        )


def deduplicate(items: list[AccountRole]) -> list[AccountRole]:
    """Remove duplicate AccountRole items by (account_id, role_name) key."""
    seen: set[tuple[str, str]] = set()
    result: list[AccountRole] = []
    for item in items:
        if item.key not in seen:
            seen.add(item.key)
            result.append(item)
    return result
