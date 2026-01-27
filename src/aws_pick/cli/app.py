"""Typer CLI application for aws-pick."""

from __future__ import annotations

import typer

from aws_pick.cli.commands.favorites import favorites_app
from aws_pick.cli.commands.history import history_app
from aws_pick.cli.commands.preset import preset_app
from aws_pick.cli.commands.select import select_app

app = typer.Typer(
    name="aws-pick",
    help="CLI and TUI tool for selecting AWS account/role credentials.",
    no_args_is_help=True,
)

app.add_typer(select_app, name="select")
app.add_typer(favorites_app, name="favorites")
app.add_typer(preset_app, name="preset")
app.add_typer(history_app, name="history")


def main() -> None:
    app()
