"""Session history management with JSON persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aws_pick.models.account import AccountRole
from aws_pick.models.config import HistoryEntry
from aws_pick.storage.json_store import JsonStore, default_config_dir

_HISTORY_FILE = "history.json"
_DEFAULT_RETENTION_DAYS = 90


class HistoryManager:
    """Records and queries account/role usage history."""

    def __init__(self, config_dir: Path | None = None, retention_days: int = _DEFAULT_RETENTION_DAYS) -> None:
        self._store = JsonStore(base_dir=config_dir or default_config_dir())
        self._retention_days = retention_days
        self.prune()

    def record(self, items: list[AccountRole]) -> None:
        """Record the current timestamp for each selected item."""
        data = self._store.read(_HISTORY_FILE, defaults={"entries": []})
        entries: list[dict[str, Any]] = data.get("entries", [])
        now = datetime.now(timezone.utc).isoformat()

        existing: dict[tuple[str, str], int] = {}
        for i, entry in enumerate(entries):
            key = (entry.get("account_id", ""), entry.get("role_name", ""))
            existing[key] = i

        for item in items:
            key = (item.account.account_id, item.role.role_name)
            entry_data = {
                "account_id": item.account.account_id,
                "role_name": item.role.role_name,
                "last_used": now,
            }
            if key in existing:
                entries[existing[key]] = entry_data
            else:
                entries.append(entry_data)

        data["entries"] = entries
        self._store.write(_HISTORY_FILE, data)

    def get_last_used(self, account_id: str, role_name: str) -> str | None:
        """Return the ISO timestamp of when this pair was last used, or None."""
        data = self._store.read(_HISTORY_FILE, defaults={"entries": []})
        for entry in data.get("entries", []):
            if entry.get("account_id") == account_id and entry.get("role_name") == role_name:
                return str(entry.get("last_used", ""))
        return None

    def list_entries(self) -> list[HistoryEntry]:
        """Return all history entries."""
        data = self._store.read(_HISTORY_FILE, defaults={"entries": []})
        return [HistoryEntry.from_dict(e) for e in data.get("entries", [])]

    def clear(self) -> None:
        """Clear all history."""
        self._store.write(_HISTORY_FILE, {"entries": []})

    def prune(self) -> None:
        """Remove entries older than retention period."""
        data = self._store.read(_HISTORY_FILE, defaults={"entries": []})
        entries: list[dict[str, Any]] = data.get("entries", [])
        if not entries:
            return

        now = datetime.now(timezone.utc)
        kept: list[dict[str, Any]] = []
        for entry in entries:
            last_used_str = entry.get("last_used", "")
            try:
                last_used = datetime.fromisoformat(last_used_str)
                if last_used.tzinfo is None:
                    last_used = last_used.replace(tzinfo=timezone.utc)
                age = (now - last_used).days
                if age <= self._retention_days:
                    kept.append(entry)
            except (ValueError, TypeError):
                pass

        if len(kept) != len(entries):
            data["entries"] = kept
            self._store.write(_HISTORY_FILE, data)


def format_relative_time(iso_timestamp: str) -> str:
    """Format an ISO timestamp as a relative time string (e.g., '2h ago', '3d ago')."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except (ValueError, TypeError):
        return ""
