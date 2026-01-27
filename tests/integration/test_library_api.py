"""Library API integration tests (T046)."""

from __future__ import annotations

from pathlib import Path

import pytest

import aws_pick
from aws_pick import (
    LoginResult,
    manage_favorites,
    manage_presets,
    select_accounts,
)
from aws_pick.exceptions import InvalidAccountError, InvalidSelectionError


def _sample_accounts() -> list[dict]:
    return [
        {"account_id": "111111111111", "account_name": "dev-account", "role_name": "Admin"},
        {"account_id": "222222222222", "account_name": "prod-account", "role_name": "ReadOnly"},
        {"account_id": "333333333333", "account_name": "staging-account", "role_name": "Admin"},
    ]


class TestPublicApiExports:
    def test_select_accounts_exported(self) -> None:
        assert hasattr(aws_pick, "select_accounts")

    def test_selection_result_exported(self) -> None:
        assert hasattr(aws_pick, "SelectionResult")

    def test_login_result_exported(self) -> None:
        assert hasattr(aws_pick, "LoginResult")

    def test_batch_login_result_exported(self) -> None:
        assert hasattr(aws_pick, "BatchLoginResult")

    def test_item_login_result_exported(self) -> None:
        assert hasattr(aws_pick, "ItemLoginResult")

    def test_manage_favorites_exported(self) -> None:
        assert hasattr(aws_pick, "manage_favorites")

    def test_manage_presets_exported(self) -> None:
        assert hasattr(aws_pick, "manage_presets")

    def test_version_exported(self) -> None:
        assert hasattr(aws_pick, "__version__")
        assert isinstance(aws_pick.__version__, str)
        parts = aws_pick.__version__.split(".")
        assert len(parts) >= 2

    def test_all_list(self) -> None:
        expected = {
            "select_accounts",
            "manage_favorites",
            "manage_presets",
            "SelectionResult",
            "LoginResult",
            "BatchLoginResult",
            "ItemLoginResult",
        }
        assert set(aws_pick.__all__) == expected


class TestNonInteractiveSelection:
    def test_select_single(self) -> None:
        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin"],
        )
        assert not result.cancelled
        assert len(result.selected) == 1
        assert result.selected[0]["account_id"] == "111111111111"

    def test_select_multiple(self) -> None:
        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin", "222222222222:ReadOnly"],
        )
        assert len(result.selected) == 2

    def test_empty_accounts_returns_empty(self) -> None:
        result = select_accounts([], interactive=False, selections=[])
        assert result.selected == []

    def test_invalid_selection_raises(self) -> None:
        with pytest.raises(InvalidSelectionError):
            select_accounts(
                _sample_accounts(),
                interactive=False,
                selections=["999999999999:NoRole"],
            )

    def test_missing_selections_param_raises(self) -> None:
        with pytest.raises(ValueError, match="selections parameter is required"):
            select_accounts(_sample_accounts(), interactive=False)

    def test_invalid_account_format_raises(self) -> None:
        with pytest.raises(InvalidAccountError):
            select_accounts(
                [{"account_id": "short", "account_name": "test", "role_name": "Admin"}],
                interactive=False,
                selections=["short:Admin"],
            )


class TestLoginHandlerIntegration:
    def test_successful_login(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=True)

        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin"],
            on_login=handler,
        )
        assert result.login_results is not None
        assert result.login_results.total == 1
        assert result.login_results.succeeded == 1

    def test_failed_login(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=False, error="Auth failed")

        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin"],
            on_login=handler,
        )
        assert result.login_results is not None
        assert result.login_results.failed == 1

    def test_mixed_login_results(self) -> None:
        call_count = 0

        def handler(item: dict) -> LoginResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return LoginResult(success=True)
            return LoginResult(success=False, error="Failed")

        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin", "222222222222:ReadOnly"],
            on_login=handler,
        )
        assert result.login_results is not None
        assert result.login_results.total == 2
        assert result.login_results.succeeded == 1
        assert result.login_results.failed == 1

    def test_handler_exception_caught(self) -> None:
        def handler(item: dict) -> LoginResult:
            raise RuntimeError("Connection timeout")

        result = select_accounts(
            _sample_accounts(),
            interactive=False,
            selections=["111111111111:Admin"],
            on_login=handler,
        )
        assert result.login_results is not None
        assert result.login_results.failed == 1
        assert "Connection timeout" in (result.login_results.results[0].error or "")


class TestManageFavoritesIntegration:
    def test_crud_lifecycle(self, tmp_path: Path) -> None:
        mgr = manage_favorites(config_dir=tmp_path)
        assert mgr.list() == []
        mgr.add("111111111111", "Admin")
        assert len(mgr.list()) == 1
        assert mgr.is_favorite("111111111111", "Admin")
        mgr.remove("111111111111", "Admin")
        assert mgr.list() == []

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        mgr1 = manage_favorites(config_dir=tmp_path)
        mgr1.add("111111111111", "Admin")
        mgr2 = manage_favorites(config_dir=tmp_path)
        assert len(mgr2.list()) == 1


class TestManagePresetsIntegration:
    def test_crud_lifecycle(self, tmp_path: Path) -> None:
        from aws_pick.models.config import Favorite

        mgr = manage_presets(config_dir=tmp_path)
        assert mgr.list_names() == []
        mgr.save("test", [Favorite(account_id="111111111111", role_name="Admin")])
        assert "test" in mgr.list_names()
        preset = mgr.get("test")
        assert len(preset.items) == 1
        mgr.delete("test")
        assert mgr.list_names() == []
