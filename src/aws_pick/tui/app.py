"""Textual TUI application for credential selection."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from textual.app import App

from aws_pick.core.favorites import FavoritesManager
from aws_pick.core.history import HistoryManager
from aws_pick.core.presets import PresetsManager
from aws_pick.models.account import AccountRole
from aws_pick.models.selection import (
    BatchLoginResult,
    LoginResult,
    SelectionResult,
)
from aws_pick.tui.screens.selector import SelectorScreen

_CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"


class CredentialSelectorApp(App[list[AccountRole] | None]):
    """Textual application for AWS credential selection."""

    CSS_PATH = _CSS_PATH
    TITLE = "Select Accounts"

    def __init__(
        self,
        items: list[AccountRole],
        *,
        title: str = "Select Accounts",
        config_dir: Path | None = None,
        on_login: Callable[[dict[str, Any]], LoginResult] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self._items = items
        self._config_dir = config_dir
        self._on_login = on_login
        self._result: SelectionResult | None = None
        self._fav_mgr = FavoritesManager(config_dir=config_dir) if config_dir else None
        self._presets_mgr = PresetsManager(config_dir=config_dir) if config_dir else None
        self._hist_mgr = HistoryManager(config_dir=config_dir) if config_dir else None

    @property
    def result(self) -> SelectionResult:
        if self._result is None:
            return SelectionResult(cancelled=True)
        return self._result

    def on_mount(self) -> None:
        self.push_screen(
            SelectorScreen(
                self._items,
                title=self.title,
                favorites_manager=self._fav_mgr,
                presets_manager=self._presets_mgr,
                history_manager=self._hist_mgr,
            ),
            callback=self._on_screen_dismiss,
        )

    def _on_screen_dismiss(self, selected: list[AccountRole] | None) -> None:
        if selected is None:
            self._result = SelectionResult(cancelled=True)
            self.exit()
            return

        if self._hist_mgr and selected:
            self._hist_mgr.record(selected)

        selected_dicts = [item.to_dict() for item in selected]

        if self._on_login is not None and selected:
            from aws_pick.tui.screens.progress import ProgressScreen

            self.push_screen(
                ProgressScreen(selected, self._on_login),
                callback=self._on_progress_done,
            )
            self._result = SelectionResult(selected=selected_dicts)
        else:
            self._result = SelectionResult(selected=selected_dicts)
            self.exit()

    def _on_progress_done(self, batch_result: BatchLoginResult | None) -> None:
        if self._result is not None and batch_result is not None:
            self._result.login_results = batch_result
        self.exit()
