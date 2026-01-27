"""Preset CLI commands."""

from __future__ import annotations

from typing import Annotated

import typer

from aws_pick.core.presets import PresetsManager
from aws_pick.exceptions import PresetNotFoundError

preset_app = typer.Typer(help="Manage named presets.", no_args_is_help=True)


@preset_app.command("list")
def list_presets() -> None:
    """List all presets."""
    mgr = PresetsManager()
    names = mgr.list_names()
    if not names:
        typer.echo("No presets saved.")
        return
    for name in names:
        preset = mgr.get(name)
        typer.echo(f"{name} ({len(preset.items)} items, created {preset.created_at})")


@preset_app.command("show")
def show_preset(
    name: Annotated[str, typer.Argument(help="Preset name.")],
) -> None:
    """Show items in a preset."""
    mgr = PresetsManager()
    try:
        preset = mgr.get(name)
    except PresetNotFoundError:
        typer.echo(f"Preset '{name}' not found.", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Preset: {preset.name} (created {preset.created_at})")
    for item in preset.items:
        typer.echo(f"  {item.account_id}:{item.role_name}")


@preset_app.command("delete")
def delete_preset(
    name: Annotated[str, typer.Argument(help="Preset name.")],
) -> None:
    """Delete a preset."""
    mgr = PresetsManager()
    try:
        mgr.delete(name)
        typer.echo(f"Preset '{name}' deleted.")
    except PresetNotFoundError:
        typer.echo(f"Preset '{name}' not found.", err=True)
        raise typer.Exit(code=1)
