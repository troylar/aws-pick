"""Search/filter input widget for the account list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input


class FilterBar(Input):
    """Search bar that emits FilterChanged messages on each keystroke."""

    BINDINGS = [
        Binding("escape", "blur_filter", "Back to list", show=False),
    ]

    @dataclass
    class FilterChanged(Message):
        """Posted when filter text changes."""

        text: str

    @dataclass
    class FilterBlurred(Message):
        """Posted when the filter bar loses focus via escape."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(placeholder="Type to filter...", id="filter-bar", **kwargs)

    def on_input_changed(self, event: Input.Changed) -> None:
        self.post_message(self.FilterChanged(text=event.value))

    def action_blur_filter(self) -> None:
        self.post_message(self.FilterBlurred())
