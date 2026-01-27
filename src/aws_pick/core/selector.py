"""Core selection logic - primary library entry point."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from aws_pick.exceptions import InvalidAccountError, InvalidSelectionError
from aws_pick.models.account import AccountRole, AwsAccount, AwsRole, deduplicate
from aws_pick.models.selection import (
    BatchLoginResult,
    ItemLoginResult,
    LoginResult,
    SelectionResult,
)


def select_accounts(
    accounts: list[dict[str, Any]],
    *,
    interactive: bool = True,
    selections: list[str] | None = None,
    on_login: Callable[[dict[str, Any]], LoginResult] | None = None,
    config_dir: str | Path | None = None,
    title: str = "Select Accounts",
) -> SelectionResult:
    """Launch the credential selector.

    Args:
        accounts: List of account/role dicts with account_id, account_name, role_name.
        interactive: If True, launch the TUI. If False, use selections parameter.
        selections: List of "account_id:role_name" strings for non-interactive mode.
        on_login: Optional callback for each selected pair. Receives a dict, returns LoginResult.
        config_dir: Override config directory for favorites/presets/history.
        title: Title displayed in the TUI panel header.

    Returns:
        SelectionResult with selected items and optional login results.
    """
    if not accounts:
        return SelectionResult()

    items = _validate_and_convert(accounts)
    items = deduplicate(items)

    if interactive:
        result = _run_interactive(items, title=title)
    else:
        if selections is None:
            raise ValueError("selections parameter is required when interactive=False")
        result = _run_non_interactive(items, selections)

    if result.cancelled or not result.selected:
        return result

    if on_login is not None:
        batch = _run_login(result.selected, on_login)
        result.login_results = batch

    return result


def _validate_and_convert(accounts: list[dict[str, Any]]) -> list[AccountRole]:
    """Validate input dicts and convert to AccountRole objects."""
    items: list[AccountRole] = []
    for i, acct in enumerate(accounts):
        if not isinstance(acct, dict):
            raise InvalidAccountError(f"accounts[{i}] must be a dict, got {type(acct).__name__}")
        for field in ("account_id", "account_name", "role_name"):
            if field not in acct:
                raise InvalidAccountError(f"accounts[{i}] missing required field '{field}'")
        items.append(
            AccountRole(
                account=AwsAccount(
                    account_id=str(acct["account_id"]),
                    account_name=str(acct["account_name"]),
                    environment=acct.get("environment"),
                ),
                role=AwsRole(role_name=str(acct["role_name"])),
            )
        )
    return items


def _run_interactive(items: list[AccountRole], *, title: str = "Select Accounts") -> SelectionResult:
    """Launch the TUI and return the result."""
    from aws_pick.tui.app import CredentialSelectorApp

    app = CredentialSelectorApp(items, title=title)
    app.run()
    return app.result


def _run_non_interactive(
    items: list[AccountRole],
    selections: list[str],
) -> SelectionResult:
    """Select items by account_id:role_name strings without launching TUI."""
    lookup = {f"{item.account.account_id}:{item.role.role_name}": item for item in items}
    selected: list[dict[str, Any]] = []
    for sel in selections:
        if sel not in lookup:
            raise InvalidSelectionError(f"Selection '{sel}' not found in available accounts")
        selected.append(lookup[sel].to_dict())
    return SelectionResult(selected=selected)


def _run_login(
    selected: list[dict[str, Any]],
    on_login: Callable[[dict[str, Any]], LoginResult],
) -> BatchLoginResult:
    """Run the login callback for each selected item."""
    results: list[ItemLoginResult] = []
    for item in selected:
        try:
            lr = on_login(item)
            results.append(
                ItemLoginResult(
                    account_id=item["account_id"],
                    account_name=item["account_name"],
                    role_name=item["role_name"],
                    success=lr.success,
                    error=lr.error,
                )
            )
        except Exception as exc:
            results.append(
                ItemLoginResult(
                    account_id=item["account_id"],
                    account_name=item["account_name"],
                    role_name=item["role_name"],
                    success=False,
                    error=str(exc),
                )
            )
    return BatchLoginResult(results=results)
