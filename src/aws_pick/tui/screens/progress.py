"""Progress screen showing batch login status."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Static

from aws_pick.core.login import process_batch
from aws_pick.models.account import AccountRole
from aws_pick.models.selection import (
    BatchLoginResult,
    ItemLoginResult,
    LoginResult,
)
from aws_pick.tui.widgets.progress_item import ProgressItem


class ProgressScreen(Screen[BatchLoginResult]):
    """Screen showing real-time login progress for each selected item."""

    BINDINGS = [
        Binding("escape", "cancel_batch", "Cancel remaining"),
    ]

    DEFAULT_CSS = """
    #progress-summary {
        height: 1;
        dock: bottom;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(
        self,
        items: list[AccountRole],
        handler: Callable[[dict[str, Any]], LoginResult],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._items = items
        self._handler = handler
        self._progress_widgets: list[ProgressItem] = []
        self._batch_result: BatchLoginResult | None = None
        self._completed = 0
        self._failed = 0
        self._cancelled = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Processing logins...", id="progress-title")
        with VerticalScroll():
            for item in self._items:
                pw = ProgressItem(
                    account_name=item.account.account_name,
                    role_name=item.role.role_name,
                    account_id=item.account.account_id,
                )
                self._progress_widgets.append(pw)
                yield pw
        yield Static(f"0/{len(self._items)} complete", id="progress-summary")

    async def on_mount(self) -> None:
        self.run_worker(self._run_batch(), exclusive=True)

    async def _run_batch(self) -> None:
        def on_progress(result: ItemLoginResult) -> None:
            self._completed += 1
            if not result.success:
                self._failed += 1
            for pw in self._progress_widgets:
                if pw._account_id == result.account_id and pw._role_name == result.role_name:
                    pw.set_result(result.success, result.error)
                    break
            self._update_summary()

        # Mark items as processing one by one
        for pw in self._progress_widgets:
            pw.set_processing()

        self._batch_result = await process_batch(
            self._items,
            self._handler,
            on_progress=on_progress,
        )
        self._update_summary(done=True)

    def _update_summary(self, done: bool = False) -> None:
        total = len(self._items)
        try:
            summary = self.query_one("#progress-summary", Static)
            text = f"{self._completed}/{total} complete"
            if self._failed:
                text += f" ({self._failed} failed)"
            if done:
                text += " - Press Esc to close"
            summary.update(text)
        except Exception:
            pass

    def action_cancel_batch(self) -> None:
        if self._batch_result is not None:
            self.dismiss(self._batch_result)
        else:
            self._cancelled = True
            self.dismiss(BatchLoginResult(results=[]))
