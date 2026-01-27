"""Unit tests for FavoritesManager (T039)."""

from __future__ import annotations

from pathlib import Path

from aws_pick.core.favorites import FavoritesManager, manage_favorites


class TestFavoritesManager:
    def test_empty_initially(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        assert mgr.list() == []

    def test_add_and_list(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.add("123456789012", "Admin")
        favs = mgr.list()
        assert len(favs) == 1
        assert favs[0].account_id == "123456789012"
        assert favs[0].role_name == "Admin"

    def test_add_duplicate_ignored(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.add("123456789012", "Admin")
        mgr.add("123456789012", "Admin")
        assert len(mgr.list()) == 1

    def test_remove(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.add("123456789012", "Admin")
        mgr.add("987654321098", "ReadOnly")
        mgr.remove("123456789012", "Admin")
        favs = mgr.list()
        assert len(favs) == 1
        assert favs[0].account_id == "987654321098"

    def test_remove_nonexistent_no_error(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.remove("000000000000", "NoRole")

    def test_clear(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.add("123456789012", "Admin")
        mgr.add("987654321098", "ReadOnly")
        mgr.clear()
        assert mgr.list() == []

    def test_is_favorite(self, tmp_path: Path) -> None:
        mgr = FavoritesManager(config_dir=tmp_path)
        mgr.add("123456789012", "Admin")
        assert mgr.is_favorite("123456789012", "Admin") is True
        assert mgr.is_favorite("000000000000", "Other") is False

    def test_persistence(self, tmp_path: Path) -> None:
        mgr1 = FavoritesManager(config_dir=tmp_path)
        mgr1.add("123456789012", "Admin")
        mgr2 = FavoritesManager(config_dir=tmp_path)
        assert len(mgr2.list()) == 1

    def test_corrupt_file_handled(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{broken", encoding="utf-8")
        mgr = FavoritesManager(config_dir=tmp_path)
        assert mgr.list() == []


class TestManageFavorites:
    def test_factory(self, tmp_path: Path) -> None:
        mgr = manage_favorites(config_dir=tmp_path)
        assert isinstance(mgr, FavoritesManager)

    def test_factory_with_str_path(self, tmp_path: Path) -> None:
        mgr = manage_favorites(config_dir=str(tmp_path))
        assert isinstance(mgr, FavoritesManager)
