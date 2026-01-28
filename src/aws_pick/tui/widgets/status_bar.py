"""Footer status bar showing selection count and keyboard hints."""

from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class StatusBar(Widget):
    """Displays selection count and key hints at the bottom of the panel."""

    selected_count: reactive[int] = reactive(0)
    grouping_label: reactive[str] = reactive("account")

    def render(self) -> Text:
        count = self.selected_count
        line = Text()
        line.append(f" {count} ", style="bold reverse cyan")
        line.append(" selected", style="bold")
        line.append("    ", style="dim")
        for key, action, last in [
            ("Space", "toggle", False),
            ("Enter", "confirm", False),
            ("Tab", "filter", False),
            ("?", "help", True),
        ]:
            line.append(key, style="bold cyan")
            line.append(f" {action}", style="dim")
            if not last:
                line.append("  ", style="dim")
        return line
