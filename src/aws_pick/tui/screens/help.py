"""Keyboard shortcut help overlay screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

_SHORTCUTS = [
    ("Up / Down", "Navigate items"),
    ("Space", "Toggle selection"),
    ("Enter", "Confirm selections"),
    ("Escape", "Cancel and exit"),
    ("a", "Select all visible"),
    ("d", "Deselect all"),
    ("f", "Toggle favorite"),
    ("F", "Select all favorites"),
    ("g", "Cycle grouping mode"),
    ("s", "Save preset"),
    ("l", "Load preset"),
    ("/", "Focus filter bar"),
    ("Tab", "Toggle filter / list"),
    ("?", "Show this help"),
]


class HelpScreen(ModalScreen[None]):
    """Modal overlay showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close", priority=True),
        Binding("question_mark", "dismiss_help", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 50;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #help-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .shortcut-row {
        height: 1;
    }

    .shortcut-key {
        width: 16;
        text-style: bold;
        color: $accent;
    }

    .shortcut-desc {
        width: 1fr;
    }

    #help-footer {
        text-align: center;
        margin-top: 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Static("Keyboard Shortcuts", id="help-title")
            for key, desc in _SHORTCUTS:
                yield Static(f"  {key:<16}{desc}")
            yield Static("Press Esc to close", id="help-footer")

    def on_key(self, event: object) -> None:
        self.dismiss(None)

    def action_dismiss_help(self) -> None:
        self.dismiss(None)
