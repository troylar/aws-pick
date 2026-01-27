"""Unit tests for JSON store (T012)."""

from __future__ import annotations

import json
from pathlib import Path

from aws_pick.storage.json_store import JsonStore


class TestJsonStoreRead:
    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        result = store.read("nonexistent.json", defaults={"key": "value"})
        assert result == {"key": "value"}

    def test_missing_file_returns_empty_dict_when_no_defaults(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        result = store.read("nonexistent.json")
        assert result == {}

    def test_read_valid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "data.json"
        path.write_text('{"hello": "world"}', encoding="utf-8")
        store = JsonStore(base_dir=tmp_path)
        result = store.read("data.json")
        assert result == {"hello": "world"}

    def test_corrupt_json_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        store = JsonStore(base_dir=tmp_path)
        result = store.read("bad.json", defaults={"fallback": True})
        assert result == {"fallback": True}

    def test_corrupt_json_creates_backup(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        store = JsonStore(base_dir=tmp_path)
        store.read("bad.json")
        backup = tmp_path / "bad.json.corrupt.bak"
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == "{not valid json"

    def test_non_dict_json_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "list.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        store = JsonStore(base_dir=tmp_path)
        result = store.read("list.json", defaults={"default": True})
        assert result == {"default": True}

    def test_defaults_are_copied(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        defaults = {"key": "value"}
        result = store.read("missing.json", defaults=defaults)
        result["key"] = "modified"
        assert defaults["key"] == "value"


class TestJsonStoreWrite:
    def test_write_creates_file(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        store.write("out.json", {"key": "value"})
        path = tmp_path / "out.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == {"key": "value"}

    def test_write_creates_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "sub" / "dir"
        store = JsonStore(base_dir=nested)
        store.write("out.json", {"nested": True})
        assert (nested / "out.json").exists()

    def test_write_overwrites_existing(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        store.write("data.json", {"version": 1})
        store.write("data.json", {"version": 2})
        data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
        assert data == {"version": 2}

    def test_no_tmp_file_left_after_write(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        store.write("data.json", {"clean": True})
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_write_preserves_unicode(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        store.write("unicode.json", {"name": "caf\u00e9"})
        text = (tmp_path / "unicode.json").read_text(encoding="utf-8")
        assert "caf\u00e9" in text

    def test_write_pretty_prints(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        store.write("pretty.json", {"a": 1, "b": 2})
        text = (tmp_path / "pretty.json").read_text(encoding="utf-8")
        assert "\n" in text
        assert text.endswith("\n")


class TestJsonStoreRoundTrip:
    def test_write_then_read(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        data = {
            "favorites": [
                {"account_id": "123456789012", "role_name": "Admin"},
                {"account_id": "987654321098", "role_name": "ReadOnly"},
            ],
            "presets": {
                "daily": {
                    "items": [{"account_id": "123456789012", "role_name": "Admin"}],
                    "created_at": "2026-01-26T10:00:00Z",
                }
            },
        }
        store.write("config.json", data)
        result = store.read("config.json")
        assert result == data

    def test_base_dir_property(self, tmp_path: Path) -> None:
        store = JsonStore(base_dir=tmp_path)
        assert store.base_dir == tmp_path
