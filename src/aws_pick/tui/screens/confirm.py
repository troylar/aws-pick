"""Production confirmation modal screen."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static


class ProductionConfirmScreen(ModalScreen[bool]):
    """Modal confirmation dialog for production account selections."""

    BINDINGS = [
        Binding("y", "confirm_yes", "Yes"),
        Binding("n", "confirm_no", "No"),
        Binding("escape", "confirm_no", "Cancel"),
    ]

    DEFAULT_CSS = """
    ProductionConfirmScreen {
        align: center middle;
    }

    #confirm-container {
        width: 60;
        max-height: 50%;
        background: $surface;
        border: thick red;
        padding: 1 2;
    }

    #confirm-title {
        text-style: bold;
        text-align: center;
        color: red;
        width: 100%;
        margin-bottom: 1;
    }

    #confirm-message {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #confirm-hint {
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, prod_count: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._prod_count = prod_count

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="confirm-container"):
                yield Static("WARNING: Production Accounts", id="confirm-title")
                yield Static(
                    f"{self._prod_count} production account(s) selected.\nAre you sure you want to continue?",
                    id="confirm-message",
                )
                yield Static("Press Y to confirm, N or Esc to cancel", id="confirm-hint")

    def action_confirm_yes(self) -> None:
        self.dismiss(True)

    def action_confirm_no(self) -> None:
        self.dismiss(False)
