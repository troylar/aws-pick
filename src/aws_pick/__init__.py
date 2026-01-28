"""aws-pick - Interactive TUI and Python library for selecting AWS account/role credentials."""

__version__ = "0.1.3"

from aws_pick.core.favorites import manage_favorites
from aws_pick.core.presets import manage_presets
from aws_pick.core.selector import select_accounts
from aws_pick.models.selection import (
    BatchLoginResult,
    ItemLoginResult,
    LoginResult,
    SelectionResult,
)

__all__ = [
    "select_accounts",
    "manage_favorites",
    "manage_presets",
    "SelectionResult",
    "LoginResult",
    "BatchLoginResult",
    "ItemLoginResult",
]
