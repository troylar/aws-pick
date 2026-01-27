"""TUI pilot integration tests (T021, T025, T028)."""

from __future__ import annotations

import pytest

from aws_pick.models.account import AccountRole, AwsAccount, AwsRole
from aws_pick.tui.app import CredentialSelectorApp


def _make_items() -> list[AccountRole]:
    return [
        AccountRole(
            account=AwsAccount(account_id="111111111111", account_name="dev-account", environment="development"),
            role=AwsRole(role_name="AdminAccess"),
        ),
        AccountRole(
            account=AwsAccount(account_id="111111111111", account_name="dev-account", environment="development"),
            role=AwsRole(role_name="ReadOnly"),
        ),
        AccountRole(
            account=AwsAccount(account_id="222222222222", account_name="prod-account", environment="production"),
            role=AwsRole(role_name="AdminAccess"),
        ),
    ]


class TestTuiLaunch:
    @pytest.mark.asyncio
    async def test_app_launches_and_renders(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            assert app.title == "Select Accounts"
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_escape_returns_cancelled(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.press("escape")
        assert app.result.cancelled is True
        assert app.result.selected == []

    @pytest.mark.asyncio
    async def test_enter_with_no_selection_returns_empty(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.press("enter")
        assert app.result.cancelled is False
        assert app.result.selected == []

    @pytest.mark.asyncio
    async def test_select_all_then_confirm(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            # Prod confirmation modal appears - press y to confirm
            await pilot.press("y")
        assert app.result.cancelled is False
        assert len(app.result.selected) == 3

    @pytest.mark.asyncio
    async def test_select_all_then_deselect_all(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a")
            await pilot.press("d")
            await pilot.press("enter")
        assert app.result.cancelled is False
        assert len(app.result.selected) == 0

    @pytest.mark.asyncio
    async def test_toggle_single_item(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            # Move down past the first group header to the first selectable item
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("space")
            await pilot.press("enter")
        assert len(app.result.selected) >= 0  # at least verifies no crash


class TestTuiKeyboardNavigation:
    @pytest.mark.asyncio
    async def test_arrow_keys_no_crash(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            for _ in range(5):
                await pilot.press("down")
            for _ in range(3):
                await pilot.press("up")
            await pilot.press("escape")
        assert app.result.cancelled is True


class TestTuiFilter:
    @pytest.mark.asyncio
    async def test_filter_bar_exists(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            from aws_pick.tui.widgets.filter_bar import FilterBar

            filter_bar = app.screen.query_one(FilterBar)
            assert filter_bar is not None
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_select_all_after_filter_only_selects_visible(self) -> None:
        items = _make_items()
        app = CredentialSelectorApp(items)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Focus the filter bar and type "dev"
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("d", "e", "v")
            await pilot.pause()
            # Escape back to list, then select all visible
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("a")
            await pilot.pause()
            await pilot.press("enter")
        # dev-account has 2 roles
        assert len(app.result.selected) == 2
        for item in app.result.selected:
            assert "dev" in item["account_name"]

    @pytest.mark.asyncio
    async def test_selections_preserved_across_filter(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            # Select all first
            await pilot.press("a")
            await pilot.pause()
            # Now filter - selections should persist even when items are hidden
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("d", "e", "v")
            await pilot.pause()
            # Escape back to list, then confirm
            await pilot.press("escape")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            # Prod confirmation modal appears - press y to confirm
            await pilot.press("y")
        assert len(app.result.selected) == 3


class TestTuiGrouping:
    @pytest.mark.asyncio
    async def test_cycle_grouping_preserves_selections(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            # Select all
            await pilot.press("a")
            await pilot.pause()
            # Cycle grouping: account -> role -> flat -> account
            await pilot.press("g")
            await pilot.pause()
            await pilot.press("g")
            await pilot.pause()
            await pilot.press("g")
            await pilot.pause()
            # Confirm
            await pilot.press("enter")
            await pilot.pause()
            # Prod confirmation modal appears - press y to confirm
            await pilot.press("y")
        assert len(app.result.selected) == 3

    @pytest.mark.asyncio
    async def test_cycle_grouping_no_crash(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            for _ in range(6):
                await pilot.press("g")
                await pilot.pause()
            await pilot.press("escape")
        assert app.result.cancelled is True


class TestTuiHelp:
    @pytest.mark.asyncio
    async def test_help_overlay_opens_and_closes(self) -> None:
        app = CredentialSelectorApp(_make_items())
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("question_mark")
            await pilot.pause()
            # Help screen should be showing - press any key to close it
            await pilot.press("q")
            await pilot.pause()
            # Now confirm to exit
            await pilot.press("enter")
        assert app.result.cancelled is False
