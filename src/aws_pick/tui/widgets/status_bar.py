"""Footer status bar showing selection count, grouping mode, and keyboard hints."""

from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class StatusBar(Widget):
    """Displays selection count, grouping mode, and key hints at the bottom of the screen."""

    selected_count: reactive[int] = reactive(0)
    grouping_label: reactive[str] = reactive("account")

    def render(self) -> Text:
        count = self.selected_count
        line = Text()
        line.append(f"{count} selected", style="bold")
        line.append("  ·  g: cycle grouping", style="dim")
        return line
