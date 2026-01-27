"""Unit tests for HistoryManager (T072)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from aws_pick.core.history import HistoryManager, format_relative_time
from aws_pick.models.account import AccountRole, AwsAccount, AwsRole


def _make_ar(account_id: str = "123456789012", role_name: str = "Admin") -> AccountRole:
    return AccountRole(
        account=AwsAccount(account_id=account_id, account_name="test"),
        role=AwsRole(role_name=role_name),
    )


class TestHistoryManager:
    def test_empty_initially(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        assert mgr.list_entries() == []

    def test_record_and_retrieve(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        mgr.record([_make_ar()])
        result = mgr.get_last_used("123456789012", "Admin")
        assert result is not None
        assert "T" in result  # ISO format

    def test_record_updates_existing(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        mgr.record([_make_ar()])
        first = mgr.get_last_used("123456789012", "Admin")
        mgr.record([_make_ar()])
        second = mgr.get_last_used("123456789012", "Admin")
        assert first is not None
        assert second is not None
        assert len(mgr.list_entries()) == 1

    def test_multiple_items(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        mgr.record([_make_ar("111111111111", "Admin"), _make_ar("222222222222", "ReadOnly")])
        assert len(mgr.list_entries()) == 2

    def test_get_last_used_nonexistent(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        assert mgr.get_last_used("000000000000", "NoRole") is None

    def test_clear(self, tmp_path: Path) -> None:
        mgr = HistoryManager(config_dir=tmp_path)
        mgr.record([_make_ar()])
        mgr.clear()
        assert mgr.list_entries() == []

    def test_persistence(self, tmp_path: Path) -> None:
        mgr1 = HistoryManager(config_dir=tmp_path)
        mgr1.record([_make_ar()])
        mgr2 = HistoryManager(config_dir=tmp_path)
        assert len(mgr2.list_entries()) == 1

    def test_prune_old_entries(self, tmp_path: Path) -> None:
        import json

        old_time = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        data = {"entries": [{"account_id": "123456789012", "role_name": "Admin", "last_used": old_time}]}
        (tmp_path / "history.json").write_text(json.dumps(data), encoding="utf-8")
        mgr = HistoryManager(config_dir=tmp_path, retention_days=90)
        assert len(mgr.list_entries()) == 0

    def test_prune_keeps_recent(self, tmp_path: Path) -> None:
        import json

        recent_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        data = {"entries": [{"account_id": "123456789012", "role_name": "Admin", "last_used": recent_time}]}
        (tmp_path / "history.json").write_text(json.dumps(data), encoding="utf-8")
        mgr = HistoryManager(config_dir=tmp_path, retention_days=90)
        assert len(mgr.list_entries()) == 1


class TestFormatRelativeTime:
    def test_just_now(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        assert format_relative_time(now) == "just now"

    def test_minutes_ago(self) -> None:
        t = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        result = format_relative_time(t)
        assert "m ago" in result

    def test_hours_ago(self) -> None:
        t = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        result = format_relative_time(t)
        assert "h ago" in result

    def test_days_ago(self) -> None:
        t = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        result = format_relative_time(t)
        assert "d ago" in result

    def test_invalid_timestamp(self) -> None:
        assert format_relative_time("invalid") == ""
