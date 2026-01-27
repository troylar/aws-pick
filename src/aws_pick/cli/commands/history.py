"""History CLI commands."""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer

from aws_pick.core.history import HistoryManager, format_relative_time

history_app = typer.Typer(help="Manage usage history.", no_args_is_help=True)


@history_app.command("list")
def list_history(
    days: Annotated[
        Optional[int],
        typer.Option("--days", "-d", help="Show entries from the last N days."),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON."),
    ] = False,
) -> None:
    """List recent usage history."""
    retention = days if days else 90
    mgr = HistoryManager(retention_days=retention)
    entries = mgr.list_entries()
    if not entries:
        typer.echo("No history entries.")
        return
    if output_json:
        data = [{"account_id": e.account_id, "role_name": e.role_name, "last_used": e.last_used} for e in entries]
        typer.echo(json.dumps(data, indent=2))
    else:
        for entry in entries:
            relative = format_relative_time(entry.last_used)
            typer.echo(f"{entry.account_id}:{entry.role_name} (used {relative})")


@history_app.command("clear")
def clear_history() -> None:
    """Clear all usage history."""
    mgr = HistoryManager()
    mgr.clear()
    typer.echo("History cleared.")
