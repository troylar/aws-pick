"""API contract tests (T076) - verify public API surface."""

from __future__ import annotations

import inspect

import aws_pick
from aws_pick.core.selector import select_accounts
from aws_pick.models.selection import (
    BatchLoginResult,
    ItemLoginResult,
    LoginResult,
    SelectionResult,
)


class TestPublicApiSurface:
    def test_all_exports_present(self) -> None:
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

    def test_select_accounts_signature(self) -> None:
        sig = inspect.signature(select_accounts)
        params = list(sig.parameters.keys())
        assert "accounts" in params
        assert "interactive" in params
        assert "selections" in params
        assert "on_login" in params
        assert "config_dir" in params
        assert "title" in params


class TestSelectionResultContract:
    def test_has_selected_field(self) -> None:
        r = SelectionResult()
        assert hasattr(r, "selected")
        assert isinstance(r.selected, list)

    def test_has_cancelled_field(self) -> None:
        r = SelectionResult()
        assert hasattr(r, "cancelled")

    def test_has_login_results_field(self) -> None:
        r = SelectionResult()
        assert hasattr(r, "login_results")

    def test_to_dict_method(self) -> None:
        r = SelectionResult(selected=[{"account_id": "123456789012"}])
        d = r.to_dict()
        assert "selected" in d
        assert "cancelled" in d


class TestLoginResultContract:
    def test_has_success_field(self) -> None:
        r = LoginResult(success=True)
        assert r.success is True

    def test_has_error_field(self) -> None:
        r = LoginResult(success=False, error="test")
        assert r.error == "test"


class TestBatchLoginResultContract:
    def test_has_results_field(self) -> None:
        b = BatchLoginResult(results=[])
        assert hasattr(b, "results")

    def test_has_total_property(self) -> None:
        b = BatchLoginResult(results=[])
        assert b.total == 0

    def test_has_succeeded_property(self) -> None:
        b = BatchLoginResult(results=[])
        assert b.succeeded == 0

    def test_has_failed_property(self) -> None:
        b = BatchLoginResult(results=[])
        assert b.failed == 0


class TestItemLoginResultContract:
    def test_has_required_fields(self) -> None:
        r = ItemLoginResult(
            account_id="123456789012",
            account_name="test",
            role_name="Admin",
            success=True,
        )
        assert r.account_id == "123456789012"
        assert r.account_name == "test"
        assert r.role_name == "Admin"
        assert r.success is True
        assert r.error is None
