"""Multi-select account/role list widget with grouping and favorites support."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.text import Text
from textual import on
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from aws_pick.core.environment import classify
from aws_pick.core.favorites import FavoritesManager
from aws_pick.core.history import HistoryManager, format_relative_time
from aws_pick.models.account import AccountRole


class GroupingMode(Enum):
    BY_ACCOUNT = "account"
    BY_ROLE = "role"
    FLAT = "flat"


_GROUPING_CYCLE = [GroupingMode.BY_ACCOUNT, GroupingMode.BY_ROLE, GroupingMode.FLAT]

_ENV_ABBREVIATIONS: dict[str, str] = {
    "production": "PROD",
    "staging": "STG",
    "development": "DEV",
}


class AccountList(Widget):
    """Grouped multi-select list of account/role items."""

    BINDINGS = [
        ("space", "toggle_selection", "Toggle"),
        ("a", "select_all", "Select all"),
        ("d", "deselect_all", "Deselect all"),
        ("f", "toggle_favorite", "Toggle favorite"),
    ]

    selected_count: reactive[int] = reactive(0)

    @dataclass
    class SelectionChanged(Message):
        """Posted when selections change."""

        count: int

    @dataclass
    class GroupingChanged(Message):
        """Posted when grouping mode changes."""

        mode: GroupingMode

    @dataclass
    class FavoriteToggled(Message):
        """Posted when a favorite is toggled."""

        account_id: str
        role_name: str
        is_favorite: bool

    def __init__(
        self,
        items: list[AccountRole],
        *,
        favorites_manager: FavoritesManager | None = None,
        history_manager: HistoryManager | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._all_items = list(items)
        self._visible_items: list[AccountRole] = list(items)
        self._selected_keys: set[tuple[str, str]] = set()
        self._filter_text = ""
        self._option_key_map: dict[str, AccountRole] = {}
        self._grouping_mode = GroupingMode.BY_ACCOUNT
        self._fav_mgr = favorites_manager
        self._hist_mgr = history_manager
        self._favorite_keys: set[tuple[str, str]] = set()
        if self._fav_mgr:
            for fav in self._fav_mgr.list():
                self._favorite_keys.add((fav.account_id, fav.role_name))

    @property
    def grouping_mode(self) -> GroupingMode:
        return self._grouping_mode

    @property
    def selected_items(self) -> list[AccountRole]:
        """Return currently selected AccountRole items."""
        return [item for item in self._all_items if item.key in self._selected_keys]

    def compose(self) -> object:  # type: ignore[override]
        yield OptionList(id="account-option-list")

    def on_mount(self) -> None:
        self._rebuild_list()

    def cycle_grouping(self) -> None:
        """Cycle to the next grouping mode."""
        idx = _GROUPING_CYCLE.index(self._grouping_mode)
        self._grouping_mode = _GROUPING_CYCLE[(idx + 1) % len(_GROUPING_CYCLE)]
        self.post_message(self.GroupingChanged(mode=self._grouping_mode))
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        """Rebuild the OptionList with current visible items in current grouping mode."""
        option_list = self.query_one("#account-option-list", OptionList)
        prev_highlight = option_list.highlighted
        option_list.clear_options()
        self._option_key_map.clear()

        fav_items = [item for item in self._visible_items if item.key in self._favorite_keys]
        non_fav_items = [item for item in self._visible_items if item.key not in self._favorite_keys]

        if fav_items:
            self._render_favorites_section(option_list, fav_items)
            if non_fav_items:
                option_list.add_option(Option(Text(""), disabled=True))

        if self._grouping_mode == GroupingMode.BY_ACCOUNT:
            self._render_by_account(option_list, non_fav_items)
        elif self._grouping_mode == GroupingMode.BY_ROLE:
            self._render_by_role(option_list, non_fav_items)
        else:
            self._render_flat(option_list, non_fav_items)

        if prev_highlight is not None and option_list.option_count > 0:
            option_list.highlighted = min(prev_highlight, option_list.option_count - 1)

    def _render_favorites_section(self, option_list: OptionList, fav_items: list[AccountRole]) -> None:
        """Render the favorites group at the top."""
        header_text = Text("  ★ Favorites", style="bold yellow")
        option_list.add_option(Option(header_text, id="header:favorites", disabled=True))
        for ar in sorted(fav_items, key=lambda r: f"{r.account.account_name}/{r.role.role_name}"):
            self._add_item_option(
                option_list, ar, label=f"{ar.account.account_name} / {ar.role.role_name}", is_fav=True
            )

    def _render_by_account(self, option_list: OptionList, items: list[AccountRole] | None = None) -> None:
        """Group items by account name."""
        source = items if items is not None else self._visible_items
        grouped: dict[str, list[AccountRole]] = {}
        for item in source:
            grouped.setdefault(item.account.account_name, []).append(item)

        first_group = True
        for account_name, roles in sorted(grouped.items()):
            if not first_group:
                option_list.add_option(Option(Text(""), disabled=True))
            first_group = False

            env_info = classify(roles[0].account)
            header_text = Text(f"  {account_name}", style="bold")
            if env_info:
                header_text.append(f" [{env_info.environment}]", style=_env_style(env_info.environment))
            option_list.add_option(Option(header_text, id=f"header:{account_name}", disabled=True))

            for ar in sorted(roles, key=lambda r: r.role.role_name):
                self._add_item_option(option_list, ar, label=ar.role.role_name, show_env_tag=False)

    def _render_by_role(self, option_list: OptionList, items: list[AccountRole] | None = None) -> None:
        """Group items by role name."""
        source = items if items is not None else self._visible_items
        grouped: dict[str, list[AccountRole]] = {}
        for item in source:
            grouped.setdefault(item.role.role_name, []).append(item)

        first_group = True
        for role_name, role_items in sorted(grouped.items()):
            if not first_group:
                option_list.add_option(Option(Text(""), disabled=True))
            first_group = False

            header_text = Text(f"  {role_name}", style="bold")
            option_list.add_option(Option(header_text, id=f"header:{role_name}", disabled=True))

            for ar in sorted(role_items, key=lambda r: r.account.account_name):
                self._add_item_option(option_list, ar, label=ar.account.account_name)

    def _render_flat(self, option_list: OptionList, items: list[AccountRole] | None = None) -> None:
        """Flat alphabetical list."""
        source = items if items is not None else self._visible_items
        sorted_items = sorted(source, key=lambda ar: f"{ar.account.account_name}/{ar.role.role_name}")
        for ar in sorted_items:
            self._add_item_option(option_list, ar, label=f"{ar.account.account_name} / {ar.role.role_name}")

    def _add_item_option(
        self,
        option_list: OptionList,
        ar: AccountRole,
        label: str,
        *,
        is_fav: bool = False,
        show_env_tag: bool = True,
    ) -> None:
        """Add a single selectable item option."""
        key_str = f"{ar.account.account_id}:{ar.role.role_name}"
        is_selected = ar.key in self._selected_keys
        indicator = "\u2713" if is_selected else "\u25cb"
        prefix = "    " if self._grouping_mode != GroupingMode.FLAT and not is_fav else "  "
        fav_star = "\u2605 " if ar.key in self._favorite_keys else ""
        line = Text(f"{prefix}{indicator} {fav_star}{label}")
        if show_env_tag:
            env_info = classify(ar.account)
            if env_info:
                tag = _ENV_ABBREVIATIONS.get(env_info.environment.lower(), env_info.environment[:4].upper())
                line.append(f" [{tag}]", style=_env_style(env_info.environment))
        if self._hist_mgr:
            last_used = self._hist_mgr.get_last_used(ar.account.account_id, ar.role.role_name)
            if last_used:
                relative = format_relative_time(last_used)
                if relative:
                    line.append(f"  {relative}", style="dim")
        if is_selected:
            line.stylize("bold cyan")
        option_list.add_option(Option(line, id=key_str))
        self._option_key_map[key_str] = ar

    @on(OptionList.OptionSelected)
    def _on_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle Enter/click on an option - toggle its selection."""
        option_id = event.option_id
        if option_id is None or option_id.startswith("header:"):
            return
        self._toggle_key(option_id)

    def action_toggle_selection(self) -> None:
        """Toggle the currently highlighted item."""
        option_list = self.query_one("#account-option-list", OptionList)
        if option_list.highlighted is None:
            return
        option = option_list.get_option_at_index(option_list.highlighted)
        if option.id is None or option.id.startswith("header:"):
            return
        self._toggle_key(option.id)

    def _toggle_key(self, key_str: str) -> None:
        ar = self._option_key_map.get(key_str)
        if ar is None:
            return
        if ar.key in self._selected_keys:
            self._selected_keys.discard(ar.key)
        else:
            self._selected_keys.add(ar.key)
        self.selected_count = len(self._selected_keys)
        self.post_message(self.SelectionChanged(count=self.selected_count))
        self._rebuild_list()

    def action_select_all(self) -> None:
        """Select all visible items."""
        for item in self._visible_items:
            self._selected_keys.add(item.key)
        self.selected_count = len(self._selected_keys)
        self.post_message(self.SelectionChanged(count=self.selected_count))
        self._rebuild_list()

    def action_deselect_all(self) -> None:
        """Deselect all items."""
        self._selected_keys.clear()
        self.selected_count = 0
        self.post_message(self.SelectionChanged(count=self.selected_count))
        self._rebuild_list()

    def action_toggle_favorite(self) -> None:
        """Toggle the favorite status of the currently highlighted item."""
        if self._fav_mgr is None:
            return
        option_list = self.query_one("#account-option-list", OptionList)
        if option_list.highlighted is None:
            return
        option = option_list.get_option_at_index(option_list.highlighted)
        if option.id is None or option.id.startswith("header:"):
            return
        ar = self._option_key_map.get(option.id)
        if ar is None:
            return
        key = ar.key
        if key in self._favorite_keys:
            self._favorite_keys.discard(key)
            self._fav_mgr.remove(ar.account.account_id, ar.role.role_name)
            is_fav = False
        else:
            self._favorite_keys.add(key)
            self._fav_mgr.add(ar.account.account_id, ar.role.role_name)
            is_fav = True
        self.post_message(
            self.FavoriteToggled(account_id=ar.account.account_id, role_name=ar.role.role_name, is_favorite=is_fav)
        )
        self._rebuild_list()

    def select_all_favorites(self) -> None:
        """Select all items that are marked as favorites."""
        for item in self._all_items:
            if item.key in self._favorite_keys:
                self._selected_keys.add(item.key)
        self.selected_count = len(self._selected_keys)
        self.post_message(self.SelectionChanged(count=self.selected_count))
        self._rebuild_list()

    def apply_filter(self, text: str) -> None:
        """Filter items by text match on account_name, account_id, or role_name."""
        self._filter_text = text.strip().lower()
        if not self._filter_text:
            self._visible_items = list(self._all_items)
        else:
            self._visible_items = [
                item
                for item in self._all_items
                if self._filter_text in item.account.account_name.lower()
                or self._filter_text in item.account.account_id
                or self._filter_text in item.role.role_name.lower()
            ]
        self._rebuild_list()


def _env_style(env: str) -> str:
    """Return a Rich style string for the environment."""
    env_lower = env.lower()
    if "prod" in env_lower:
        return "bold red"
    if "stag" in env_lower:
        return "yellow"
    if "dev" in env_lower:
        return "green"
    return "dim"
