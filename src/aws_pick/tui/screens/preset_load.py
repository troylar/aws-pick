"""Preset load modal screen."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from aws_pick.core.presets import PresetsManager
from aws_pick.models.config import Favorite


class PresetLoadScreen(ModalScreen[list[Favorite] | None]):
    """Modal dialog for loading a named preset."""

    BINDINGS = [
        Binding("escape", "cancel_load", "Cancel"),
        Binding("enter", "select_preset", "Load", priority=True),
    ]

    DEFAULT_CSS = """
    PresetLoadScreen {
        align: center middle;
    }

    #load-container {
        width: 50;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #load-title {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #load-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, presets_manager: PresetsManager, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._mgr = presets_manager
        self._preset_names: list[str] = []

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="load-container"):
                yield Static("Load Preset", id="load-title")
                yield OptionList(id="preset-list")
                yield Static("Enter to load, Esc to cancel", id="load-hint")

    def on_mount(self) -> None:
        option_list = self.query_one("#preset-list", OptionList)
        self._preset_names = self._mgr.list_names()
        if not self._preset_names:
            option_list.add_option(Option(Text("No presets saved", style="dim"), disabled=True))
        else:
            for name in self._preset_names:
                preset = self._mgr.get(name)
                label = Text(f"{name} ({len(preset.items)} items)")
                option_list.add_option(Option(label, id=name))
        option_list.focus()

    def action_select_preset(self) -> None:
        option_list = self.query_one("#preset-list", OptionList)
        if option_list.highlighted is None or not self._preset_names:
            return
        option = option_list.get_option_at_index(option_list.highlighted)
        if option.id is None:
            return
        preset = self._mgr.get(option.id)
        self.dismiss(list(preset.items))

    def action_cancel_load(self) -> None:
        self.dismiss(None)
