"""Preset save modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class PresetSaveScreen(ModalScreen[str | None]):
    """Modal dialog for saving current selections as a named preset."""

    BINDINGS = [
        Binding("escape", "cancel_save", "Cancel"),
    ]

    DEFAULT_CSS = """
    PresetSaveScreen {
        align: center middle;
    }

    #save-container {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #save-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #save-input {
        margin-bottom: 1;
    }

    #save-hint {
        text-align: center;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="save-container"):
                yield Static("Save Preset", id="save-title")
                yield Input(placeholder="Enter preset name...", id="save-input")
                yield Static("Press Enter to save, Esc to cancel", id="save-hint")

    def on_mount(self) -> None:
        self.query_one("#save-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if name:
            self.dismiss(name)

    def action_cancel_save(self) -> None:
        self.dismiss(None)
