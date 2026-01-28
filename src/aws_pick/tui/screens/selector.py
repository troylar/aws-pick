"""Main selector screen composing account list, filter bar, and status bar."""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Key
from textual.screen import Screen
from textual.widgets import OptionList, Static

from aws_pick.core.environment import classify
from aws_pick.core.favorites import FavoritesManager
from aws_pick.core.history import HistoryManager
from aws_pick.core.presets import PresetsManager
from aws_pick.models.account import AccountRole
from aws_pick.models.config import Favorite
from aws_pick.tui.screens.confirm import ProductionConfirmScreen
from aws_pick.tui.screens.help import HelpScreen
from aws_pick.tui.screens.preset_load import PresetLoadScreen
from aws_pick.tui.screens.preset_save import PresetSaveScreen
from aws_pick.tui.widgets.account_list import AccountList
from aws_pick.tui.widgets.filter_bar import FilterBar
from aws_pick.tui.widgets.status_bar import StatusBar


class SelectorScreen(Screen[list[AccountRole] | None]):
    """Screen for selecting AWS account/role pairs.

    Dismisses with a list of selected AccountRole items, or None if cancelled.
    """

    BINDINGS = [
        Binding("enter", "confirm", "Confirm", priority=True),
        Binding("escape", "cancel", "Cancel"),
        Binding("question_mark", "show_help", "Help"),
        Binding("slash", "focus_filter", "Filter"),
        Binding("tab", "toggle_focus", "Toggle focus", show=False),
        Binding("g", "cycle_grouping", "Grouping"),
        Binding("F", "select_favorites", "Select favorites"),
        Binding("s", "save_preset", "Save preset"),
        Binding("l", "load_preset", "Load preset"),
    ]

    def __init__(
        self,
        items: list[AccountRole],
        *,
        title: str = "Select Accounts",
        favorites_manager: FavoritesManager | None = None,
        presets_manager: PresetsManager | None = None,
        history_manager: HistoryManager | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._items = items
        self._title = title
        self._fav_mgr = favorites_manager
        self._presets_mgr = presets_manager
        self._hist_mgr = history_manager

    def compose(self) -> ComposeResult:
        with Vertical(id="panel"):
            yield Static(f"[bold cyan]{self._title}[/]", id="panel-title")
            yield FilterBar()
            yield AccountList(
                self._items,
                favorites_manager=self._fav_mgr,
                history_manager=self._hist_mgr,
                id="account-list",
            )
            yield StatusBar()

    def on_mount(self) -> None:
        self._focus_list()

    def _focus_list(self) -> None:
        try:
            option_list = self.query_one("#account-option-list", OptionList)
            option_list.focus()
        except Exception:
            pass

    @on(AccountList.SelectionChanged)
    def _on_selection_changed(self, event: AccountList.SelectionChanged) -> None:
        status_bar = self.query_one(StatusBar)
        status_bar.selected_count = event.count

    @on(FilterBar.FilterChanged)
    def _on_filter_changed(self, event: FilterBar.FilterChanged) -> None:
        account_list = self.query_one(AccountList)
        account_list.apply_filter(event.text)

    @on(FilterBar.FilterBlurred)
    def _on_filter_blurred(self, event: FilterBar.FilterBlurred) -> None:
        self._focus_list()

    def action_confirm(self) -> None:
        account_list = self.query_one(AccountList)
        selected = account_list.selected_items
        prod_items = [
            item
            for item in selected
            if (env := classify(item.account)) is not None and "prod" in env.environment.lower()
        ]
        if prod_items:
            self.app.push_screen(
                ProductionConfirmScreen(len(prod_items)),
                callback=self._on_prod_confirm,
            )
        else:
            self.dismiss(selected)

    def _on_prod_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            account_list = self.query_one(AccountList)
            self.dismiss(account_list.selected_items)
        # If not confirmed, stay on selector screen

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_show_help(self) -> None:
        self.app.push_screen(HelpScreen())

    def action_focus_filter(self) -> None:
        self.query_one(FilterBar).focus()

    def on_key(self, event: Key) -> None:
        """Forward alphanumeric keys to filter bar for typeahead search."""
        filter_bar = self.query_one(FilterBar)
        if filter_bar.has_focus:
            return
        reserved_keys = {"a", "d", "f", "g", "s", "l", "F"}
        if event.character and event.character.isalnum() and event.character not in reserved_keys:
            filter_bar.focus()
            filter_bar.value = event.character
            filter_bar.cursor_position = len(filter_bar.value)
            event.prevent_default()
            event.stop()

    def action_toggle_focus(self) -> None:
        filter_bar = self.query_one(FilterBar)
        if filter_bar.has_focus:
            self._focus_list()
        else:
            filter_bar.focus()

    def action_select_favorites(self) -> None:
        account_list = self.query_one(AccountList)
        account_list.select_all_favorites()

    def action_cycle_grouping(self) -> None:
        account_list = self.query_one(AccountList)
        account_list.cycle_grouping()
        status_bar = self.query_one(StatusBar)
        status_bar.grouping_label = account_list.grouping_mode.value

    def action_save_preset(self) -> None:
        if self._presets_mgr is None:
            return
        self.app.push_screen(PresetSaveScreen(), callback=self._on_preset_saved)

    def _on_preset_saved(self, name: str | None) -> None:
        if name is None or self._presets_mgr is None:
            return
        account_list = self.query_one(AccountList)
        selected = account_list.selected_items
        items = [Favorite(account_id=ar.account.account_id, role_name=ar.role.role_name) for ar in selected]
        self._presets_mgr.save(name, items)

    def action_load_preset(self) -> None:
        if self._presets_mgr is None:
            return
        self.app.push_screen(
            PresetLoadScreen(self._presets_mgr),
            callback=self._on_preset_loaded,
        )

    def _on_preset_loaded(self, items: list[Favorite] | None) -> None:
        if items is None:
            return
        account_list = self.query_one(AccountList)
        preset_keys = {(f.account_id, f.role_name) for f in items}
        for item in account_list._all_items:
            if item.key in preset_keys:
                account_list._selected_keys.add(item.key)
        account_list.selected_count = len(account_list._selected_keys)
        account_list.post_message(AccountList.SelectionChanged(count=account_list.selected_count))
        account_list._rebuild_list()
