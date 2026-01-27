"""Unit tests for data models (T011)."""

from __future__ import annotations

import pytest

from aws_pick.exceptions import InvalidAccountError
from aws_pick.models.account import AccountRole, AwsAccount, AwsRole, deduplicate
from aws_pick.models.config import EnvironmentPattern, Favorite, HistoryEntry, Preset
from aws_pick.models.selection import BatchLoginResult, ItemLoginResult, LoginResult, SelectionResult

# --- AwsAccount ---


class TestAwsAccount:
    def test_valid_creation(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-account")
        assert acct.account_id == "123456789012"
        assert acct.account_name == "my-account"
        assert acct.environment is None

    def test_with_environment(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="prod", environment="production")
        assert acct.environment == "production"

    def test_invalid_account_id_too_short(self) -> None:
        with pytest.raises(InvalidAccountError, match="12 digits"):
            AwsAccount(account_id="12345", account_name="bad")

    def test_invalid_account_id_letters(self) -> None:
        with pytest.raises(InvalidAccountError, match="12 digits"):
            AwsAccount(account_id="12345678901a", account_name="bad")

    def test_invalid_account_id_too_long(self) -> None:
        with pytest.raises(InvalidAccountError, match="12 digits"):
            AwsAccount(account_id="1234567890123", account_name="bad")

    def test_empty_account_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="must not be empty"):
            AwsAccount(account_id="123456789012", account_name="")

    def test_whitespace_account_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="must not be empty"):
            AwsAccount(account_id="123456789012", account_name="   ")

    def test_frozen(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="test")
        with pytest.raises(AttributeError):
            acct.account_name = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="test")
        d = acct.to_dict()
        assert d == {"account_id": "123456789012", "account_name": "test"}

    def test_to_dict_with_environment(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="test", environment="dev")
        d = acct.to_dict()
        assert d == {"account_id": "123456789012", "account_name": "test", "environment": "dev"}

    def test_from_dict(self) -> None:
        d = {"account_id": "123456789012", "account_name": "test", "environment": "staging"}
        acct = AwsAccount.from_dict(d)
        assert acct.account_id == "123456789012"
        assert acct.account_name == "test"
        assert acct.environment == "staging"

    def test_round_trip(self) -> None:
        original = AwsAccount(account_id="123456789012", account_name="round-trip", environment="production")
        restored = AwsAccount.from_dict(original.to_dict())
        assert original == restored


# --- AwsRole ---


class TestAwsRole:
    def test_valid_creation(self) -> None:
        role = AwsRole(role_name="AdminAccess")
        assert role.role_name == "AdminAccess"

    def test_empty_role_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="must not be empty"):
            AwsRole(role_name="")

    def test_whitespace_role_name(self) -> None:
        with pytest.raises(InvalidAccountError, match="must not be empty"):
            AwsRole(role_name="   ")

    def test_frozen(self) -> None:
        role = AwsRole(role_name="ReadOnly")
        with pytest.raises(AttributeError):
            role.role_name = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        assert AwsRole(role_name="Admin").to_dict() == {"role_name": "Admin"}

    def test_from_dict(self) -> None:
        role = AwsRole.from_dict({"role_name": "Admin"})
        assert role.role_name == "Admin"

    def test_round_trip(self) -> None:
        original = AwsRole(role_name="PowerUser")
        assert AwsRole.from_dict(original.to_dict()) == original


# --- AccountRole ---


class TestAccountRole:
    def test_creation(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test"),
            role=AwsRole(role_name="Admin"),
        )
        assert ar.account.account_id == "123456789012"
        assert ar.role.role_name == "Admin"

    def test_key(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test"),
            role=AwsRole(role_name="Admin"),
        )
        assert ar.key == ("123456789012", "Admin")

    def test_to_dict(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test"),
            role=AwsRole(role_name="Admin"),
        )
        d = ar.to_dict()
        assert d == {"account_id": "123456789012", "account_name": "test", "role_name": "Admin"}

    def test_to_dict_with_environment(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test", environment="prod"),
            role=AwsRole(role_name="Admin"),
        )
        d = ar.to_dict()
        assert d["environment"] == "prod"

    def test_from_dict(self) -> None:
        d = {"account_id": "123456789012", "account_name": "test", "role_name": "Admin", "environment": "dev"}
        ar = AccountRole.from_dict(d)
        assert ar.account.account_id == "123456789012"
        assert ar.account.environment == "dev"
        assert ar.role.role_name == "Admin"

    def test_round_trip(self) -> None:
        original = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test", environment="staging"),
            role=AwsRole(role_name="ReadOnly"),
        )
        restored = AccountRole.from_dict(original.to_dict())
        assert original == restored

    def test_frozen(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test"),
            role=AwsRole(role_name="Admin"),
        )
        with pytest.raises(AttributeError):
            ar.role = AwsRole(role_name="Other")  # type: ignore[misc]


# --- deduplicate ---


class TestDeduplicate:
    def test_no_duplicates(self, small_account_list: list[AccountRole]) -> None:
        result = deduplicate(small_account_list)
        assert len(result) == len(small_account_list)

    def test_removes_duplicates(self) -> None:
        ar = AccountRole(
            account=AwsAccount(account_id="123456789012", account_name="test"),
            role=AwsRole(role_name="Admin"),
        )
        result = deduplicate([ar, ar, ar])
        assert len(result) == 1

    def test_preserves_order(self) -> None:
        items = [
            AccountRole(
                account=AwsAccount(account_id="111111111111", account_name="first"),
                role=AwsRole(role_name="Admin"),
            ),
            AccountRole(
                account=AwsAccount(account_id="222222222222", account_name="second"),
                role=AwsRole(role_name="Admin"),
            ),
            AccountRole(
                account=AwsAccount(account_id="111111111111", account_name="first"),
                role=AwsRole(role_name="Admin"),
            ),
        ]
        result = deduplicate(items)
        assert len(result) == 2
        assert result[0].account.account_name == "first"
        assert result[1].account.account_name == "second"

    def test_empty_list(self) -> None:
        assert deduplicate([]) == []

    def test_different_roles_same_account(self) -> None:
        items = [
            AccountRole(
                account=AwsAccount(account_id="123456789012", account_name="test"),
                role=AwsRole(role_name="Admin"),
            ),
            AccountRole(
                account=AwsAccount(account_id="123456789012", account_name="test"),
                role=AwsRole(role_name="ReadOnly"),
            ),
        ]
        result = deduplicate(items)
        assert len(result) == 2


# --- Favorite ---


class TestFavorite:
    def test_creation(self) -> None:
        fav = Favorite(account_id="123456789012", role_name="Admin")
        assert fav.account_id == "123456789012"
        assert fav.role_name == "Admin"

    def test_frozen(self) -> None:
        fav = Favorite(account_id="123456789012", role_name="Admin")
        with pytest.raises(AttributeError):
            fav.role_name = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        fav = Favorite(account_id="123456789012", role_name="Admin")
        assert fav.to_dict() == {"account_id": "123456789012", "role_name": "Admin"}

    def test_from_dict(self) -> None:
        fav = Favorite.from_dict({"account_id": "123456789012", "role_name": "Admin"})
        assert fav.account_id == "123456789012"
        assert fav.role_name == "Admin"

    def test_round_trip(self) -> None:
        original = Favorite(account_id="123456789012", role_name="ReadOnly")
        assert Favorite.from_dict(original.to_dict()) == original


# --- Preset ---


class TestPreset:
    def test_creation(self) -> None:
        preset = Preset(name="daily", items=(Favorite(account_id="123456789012", role_name="Admin"),))
        assert preset.name == "daily"
        assert len(preset.items) == 1

    def test_empty_items(self) -> None:
        preset = Preset(name="empty")
        assert preset.items == ()

    def test_to_dict(self) -> None:
        preset = Preset(
            name="test",
            items=(Favorite(account_id="123456789012", role_name="Admin"),),
            created_at="2026-01-26T10:00:00Z",
        )
        d = preset.to_dict()
        assert d["created_at"] == "2026-01-26T10:00:00Z"
        assert len(d["items"]) == 1
        assert d["items"][0]["account_id"] == "123456789012"

    def test_from_dict(self) -> None:
        data = {
            "items": [{"account_id": "123456789012", "role_name": "Admin"}],
            "created_at": "2026-01-26T10:00:00Z",
        }
        preset = Preset.from_dict("my-preset", data)
        assert preset.name == "my-preset"
        assert len(preset.items) == 1
        assert preset.created_at == "2026-01-26T10:00:00Z"

    def test_round_trip(self) -> None:
        original = Preset(
            name="roundtrip",
            items=(
                Favorite(account_id="123456789012", role_name="Admin"),
                Favorite(account_id="987654321098", role_name="ReadOnly"),
            ),
            created_at="2026-01-26T12:00:00Z",
        )
        restored = Preset.from_dict(original.name, original.to_dict())
        assert original == restored


# --- HistoryEntry ---


class TestHistoryEntry:
    def test_creation(self) -> None:
        entry = HistoryEntry(account_id="123456789012", role_name="Admin", last_used="2026-01-26T10:00:00Z")
        assert entry.last_used == "2026-01-26T10:00:00Z"

    def test_to_dict(self) -> None:
        entry = HistoryEntry(account_id="123456789012", role_name="Admin", last_used="2026-01-26T10:00:00Z")
        d = entry.to_dict()
        assert d == {"account_id": "123456789012", "role_name": "Admin", "last_used": "2026-01-26T10:00:00Z"}

    def test_round_trip(self) -> None:
        original = HistoryEntry(account_id="123456789012", role_name="Admin", last_used="2026-01-26T10:00:00Z")
        assert HistoryEntry.from_dict(original.to_dict()) == original


# --- EnvironmentPattern ---


class TestEnvironmentPattern:
    def test_creation(self) -> None:
        ep = EnvironmentPattern(pattern="prod", environment="production", color="red")
        assert ep.pattern == "prod"
        assert ep.environment == "production"
        assert ep.color == "red"

    def test_to_dict(self) -> None:
        ep = EnvironmentPattern(pattern="dev", environment="development", color="green")
        assert ep.to_dict() == {"pattern": "dev", "environment": "development", "color": "green"}

    def test_round_trip(self) -> None:
        original = EnvironmentPattern(pattern="stg", environment="staging", color="yellow")
        assert EnvironmentPattern.from_dict(original.to_dict()) == original


# --- SelectionResult ---


class TestSelectionResult:
    def test_empty(self) -> None:
        sr = SelectionResult()
        assert sr.selected == []
        assert sr.cancelled is False
        assert sr.login_results is None

    def test_cancelled(self) -> None:
        sr = SelectionResult(cancelled=True)
        assert sr.cancelled is True

    def test_to_dict(self) -> None:
        sr = SelectionResult(selected=[{"account_id": "123456789012", "role_name": "Admin"}])
        d = sr.to_dict()
        assert d["count"] == 1
        assert d["cancelled"] is False
        assert "login_results" not in d

    def test_to_dict_with_login_results(self) -> None:
        batch = BatchLoginResult(
            results=[ItemLoginResult(account_id="123456789012", account_name="test", role_name="Admin", success=True)]
        )
        sr = SelectionResult(
            selected=[{"account_id": "123456789012", "role_name": "Admin"}],
            login_results=batch,
        )
        d = sr.to_dict()
        assert "login_results" in d
        assert d["login_results"]["total"] == 1
        assert d["login_results"]["succeeded"] == 1


# --- LoginResult ---


class TestLoginResult:
    def test_success(self) -> None:
        lr = LoginResult(success=True)
        assert lr.success is True
        assert lr.error is None

    def test_failure(self) -> None:
        lr = LoginResult(success=False, error="timeout")
        assert lr.success is False
        assert lr.error == "timeout"


# --- BatchLoginResult ---


class TestBatchLoginResult:
    def test_empty(self) -> None:
        blr = BatchLoginResult()
        assert blr.total == 0
        assert blr.succeeded == 0
        assert blr.failed == 0

    def test_mixed_results(self) -> None:
        blr = BatchLoginResult(
            results=[
                ItemLoginResult(account_id="111111111111", account_name="a", role_name="Admin", success=True),
                ItemLoginResult(
                    account_id="222222222222", account_name="b", role_name="Admin", success=False, error="denied"
                ),
                ItemLoginResult(account_id="333333333333", account_name="c", role_name="Admin", success=True),
            ]
        )
        assert blr.total == 3
        assert blr.succeeded == 2
        assert blr.failed == 1

    def test_to_dict(self) -> None:
        blr = BatchLoginResult(
            results=[
                ItemLoginResult(account_id="111111111111", account_name="a", role_name="Admin", success=True),
            ]
        )
        d = blr.to_dict()
        assert d["total"] == 1
        assert d["succeeded"] == 1
        assert d["failed"] == 0
        assert len(d["results"]) == 1


# --- ItemLoginResult ---


class TestItemLoginResult:
    def test_success_to_dict(self) -> None:
        ilr = ItemLoginResult(account_id="123456789012", account_name="test", role_name="Admin", success=True)
        d = ilr.to_dict()
        assert d["success"] is True
        assert "error" not in d

    def test_failure_to_dict(self) -> None:
        ilr = ItemLoginResult(
            account_id="123456789012", account_name="test", role_name="Admin", success=False, error="timeout"
        )
        d = ilr.to_dict()
        assert d["success"] is False
        assert d["error"] == "timeout"
