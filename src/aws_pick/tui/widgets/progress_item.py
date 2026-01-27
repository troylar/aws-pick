"""Progress item widget showing login status for a single account/role."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class ProgressItem(Widget):
    """Displays a single account/role with its login progress status."""

    DEFAULT_CSS = """
    ProgressItem {
        height: 1;
        padding: 0 1;
    }
    """

    status: reactive[str] = reactive("pending")

    def __init__(
        self,
        account_name: str,
        role_name: str,
        account_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._account_name = account_name
        self._role_name = role_name
        self._account_id = account_id
        self._error: str | None = None

    def set_result(self, success: bool, error: str | None = None) -> None:
        self._error = error
        self.status = "success" if success else "failed"

    def set_processing(self) -> None:
        self.status = "processing"

    def render(self) -> Text:
        label = f"{self._account_name} / {self._role_name}"
        line = Text()
        if self.status == "pending":
            line.append("  ", style="dim")
            line.append(label, style="dim")
        elif self.status == "processing":
            line.append("... ", style="yellow")
            line.append(label, style="yellow")
        elif self.status == "success":
            line.append("v ", style="green")
            line.append(label, style="green")
        else:
            line.append("x ", style="red")
            line.append(label, style="red")
            if self._error:
                line.append(f" ({self._error})", style="dim red")
        return line
