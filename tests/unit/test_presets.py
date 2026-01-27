"""Unit tests for PresetsManager (T067)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aws_pick.core.presets import PresetsManager, manage_presets
from aws_pick.exceptions import PresetNotFoundError
from aws_pick.models.config import Favorite


class TestPresetsManager:
    def test_empty_initially(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        assert mgr.list_names() == []

    def test_save_and_list(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        items = [Favorite(account_id="123456789012", role_name="Admin")]
        mgr.save("daily", items)
        assert mgr.list_names() == ["daily"]

    def test_save_and_get(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        items = [
            Favorite(account_id="123456789012", role_name="Admin"),
            Favorite(account_id="987654321098", role_name="ReadOnly"),
        ]
        mgr.save("my-preset", items)
        preset = mgr.get("my-preset")
        assert preset.name == "my-preset"
        assert len(preset.items) == 2
        assert preset.created_at != ""

    def test_get_nonexistent_raises(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        with pytest.raises(PresetNotFoundError):
            mgr.get("nonexistent")

    def test_save_overwrites(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        mgr.save("test", [Favorite(account_id="123456789012", role_name="Admin")])
        mgr.save("test", [Favorite(account_id="987654321098", role_name="ReadOnly")])
        preset = mgr.get("test")
        assert len(preset.items) == 1
        assert preset.items[0].account_id == "987654321098"

    def test_delete(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        mgr.save("to-delete", [Favorite(account_id="123456789012", role_name="Admin")])
        mgr.delete("to-delete")
        assert mgr.list_names() == []

    def test_delete_nonexistent_raises(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        with pytest.raises(PresetNotFoundError):
            mgr.delete("nonexistent")

    def test_persistence(self, tmp_path: Path) -> None:
        mgr1 = PresetsManager(config_dir=tmp_path)
        mgr1.save("persistent", [Favorite(account_id="123456789012", role_name="Admin")])
        mgr2 = PresetsManager(config_dir=tmp_path)
        assert "persistent" in mgr2.list_names()

    def test_multiple_presets(self, tmp_path: Path) -> None:
        mgr = PresetsManager(config_dir=tmp_path)
        mgr.save("alpha", [Favorite(account_id="123456789012", role_name="Admin")])
        mgr.save("beta", [Favorite(account_id="987654321098", role_name="ReadOnly")])
        assert mgr.list_names() == ["alpha", "beta"]


class TestManagePresets:
    def test_factory(self, tmp_path: Path) -> None:
        mgr = manage_presets(config_dir=tmp_path)
        assert isinstance(mgr, PresetsManager)
