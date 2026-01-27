"""Unit tests for core selector logic (T020)."""

from __future__ import annotations

from typing import Any

import pytest

from aws_pick.core.selector import _run_login, _run_non_interactive, _validate_and_convert, select_accounts
from aws_pick.exceptions import InvalidAccountError, InvalidSelectionError
from aws_pick.models.selection import LoginResult, SelectionResult

# --- Input validation ---


class TestValidateAndConvert:
    def test_valid_input(self) -> None:
        accounts = [
            {"account_id": "123456789012", "account_name": "test", "role_name": "Admin"},
        ]
        result = _validate_and_convert(accounts)
        assert len(result) == 1
        assert result[0].account.account_id == "123456789012"
        assert result[0].role.role_name == "Admin"

    def test_missing_account_id(self) -> None:
        with pytest.raises(InvalidAccountError, match="account_id"):
            _validate_and_convert([{"account_name": "test", "role_name": "Admin"}])

    def test_missing_account_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="account_name"):
            _validate_and_convert([{"account_id": "123456789012", "role_name": "Admin"}])

    def test_missing_role_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="role_name"):
            _validate_and_convert([{"account_id": "123456789012", "account_name": "test"}])

    def test_invalid_account_id_format(self) -> None:
        with pytest.raises(InvalidAccountError, match="12 digits"):
            _validate_and_convert([{"account_id": "12345", "account_name": "test", "role_name": "Admin"}])

    def test_non_dict_item(self) -> None:
        with pytest.raises(InvalidAccountError, match="must be a dict"):
            _validate_and_convert(["not_a_dict"])  # type: ignore[list-item]

    def test_with_environment(self) -> None:
        accounts = [
            {"account_id": "123456789012", "account_name": "test", "role_name": "Admin", "environment": "production"},
        ]
        result = _validate_and_convert(accounts)
        assert result[0].account.environment == "production"

    def test_without_environment(self) -> None:
        accounts = [
            {"account_id": "123456789012", "account_name": "test", "role_name": "Admin"},
        ]
        result = _validate_and_convert(accounts)
        assert result[0].account.environment is None

    def test_error_includes_index(self) -> None:
        accounts: list[dict[str, Any]] = [
            {"account_id": "123456789012", "account_name": "good", "role_name": "Admin"},
            {"account_id": "123456789012", "account_name": "bad"},  # missing role_name
        ]
        with pytest.raises(InvalidAccountError, match="accounts\\[1\\]"):
            _validate_and_convert(accounts)


# --- Empty list handling ---


class TestSelectAccountsEmpty:
    def test_empty_list_returns_empty_result(self) -> None:
        result = select_accounts([])
        assert result.selected == []
        assert result.cancelled is False


# --- Deduplication ---


class TestDeduplication:
    def test_duplicates_removed(self) -> None:
        accounts = [
            {"account_id": "123456789012", "account_name": "test", "role_name": "Admin"},
            {"account_id": "123456789012", "account_name": "test", "role_name": "Admin"},
        ]
        items = _validate_and_convert(accounts)
        from aws_pick.models.account import deduplicate

        deduped = deduplicate(items)
        assert len(deduped) == 1


# --- Non-interactive mode ---


class TestNonInteractive:
    def test_valid_selections(self) -> None:
        items = _validate_and_convert(
            [
                {"account_id": "123456789012", "account_name": "a", "role_name": "Admin"},
                {"account_id": "987654321098", "account_name": "b", "role_name": "ReadOnly"},
            ]
        )
        result = _run_non_interactive(items, ["123456789012:Admin"])
        assert len(result.selected) == 1
        assert result.selected[0]["account_id"] == "123456789012"

    def test_invalid_selection_raises(self) -> None:
        items = _validate_and_convert([{"account_id": "123456789012", "account_name": "a", "role_name": "Admin"}])
        with pytest.raises(InvalidSelectionError, match="not found"):
            _run_non_interactive(items, ["000000000000:NoRole"])

    def test_multiple_selections(self) -> None:
        items = _validate_and_convert(
            [
                {"account_id": "123456789012", "account_name": "a", "role_name": "Admin"},
                {"account_id": "987654321098", "account_name": "b", "role_name": "ReadOnly"},
            ]
        )
        result = _run_non_interactive(items, ["123456789012:Admin", "987654321098:ReadOnly"])
        assert len(result.selected) == 2

    def test_requires_selections_param(self) -> None:
        with pytest.raises(ValueError, match="selections parameter is required"):
            select_accounts(
                [{"account_id": "123456789012", "account_name": "a", "role_name": "Admin"}],
                interactive=False,
            )

    def test_non_interactive_returns_result(self) -> None:
        result = select_accounts(
            [{"account_id": "123456789012", "account_name": "a", "role_name": "Admin"}],
            interactive=False,
            selections=["123456789012:Admin"],
        )
        assert isinstance(result, SelectionResult)
        assert len(result.selected) == 1
        assert result.cancelled is False


# --- Login handler ---


class TestLoginHandler:
    def test_successful_login(self) -> None:
        selected = [{"account_id": "123456789012", "account_name": "test", "role_name": "Admin"}]
        batch = _run_login(selected, lambda _: LoginResult(success=True))
        assert batch.total == 1
        assert batch.succeeded == 1
        assert batch.failed == 0

    def test_failed_login(self) -> None:
        selected = [{"account_id": "123456789012", "account_name": "test", "role_name": "Admin"}]
        batch = _run_login(selected, lambda _: LoginResult(success=False, error="denied"))
        assert batch.total == 1
        assert batch.succeeded == 0
        assert batch.failed == 1
        assert batch.results[0].error == "denied"

    def test_exception_in_handler(self) -> None:
        selected = [{"account_id": "123456789012", "account_name": "test", "role_name": "Admin"}]

        def bad_handler(item: dict[str, Any]) -> LoginResult:
            raise RuntimeError("connection failed")

        batch = _run_login(selected, bad_handler)
        assert batch.total == 1
        assert batch.failed == 1
        assert "connection failed" in (batch.results[0].error or "")

    def test_mixed_results(self) -> None:
        selected = [
            {"account_id": "111111111111", "account_name": "a", "role_name": "Admin"},
            {"account_id": "222222222222", "account_name": "b", "role_name": "Admin"},
            {"account_id": "333333333333", "account_name": "c", "role_name": "Admin"},
        ]
        call_count = 0

        def handler(item: dict[str, Any]) -> LoginResult:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return LoginResult(success=False, error="failed")
            return LoginResult(success=True)

        batch = _run_login(selected, handler)
        assert batch.total == 3
        assert batch.succeeded == 2
        assert batch.failed == 1

    def test_on_login_with_non_interactive(self) -> None:
        accounts = [{"account_id": "123456789012", "account_name": "test", "role_name": "Admin"}]
        result = select_accounts(
            accounts,
            interactive=False,
            selections=["123456789012:Admin"],
            on_login=lambda _: LoginResult(success=True),
        )
        assert result.login_results is not None
        assert result.login_results.succeeded == 1
