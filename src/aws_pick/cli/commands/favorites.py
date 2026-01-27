"""Favorites CLI commands."""

from __future__ import annotations

from typing import Annotated

import typer

from aws_pick.core.favorites import FavoritesManager

favorites_app = typer.Typer(help="Manage favorite account/role pairs.", no_args_is_help=True)


@favorites_app.command("list")
def list_favorites() -> None:
    """List all favorites."""
    mgr = FavoritesManager()
    favs = mgr.list()
    if not favs:
        typer.echo("No favorites saved.")
        return
    for fav in favs:
        typer.echo(f"{fav.account_id}:{fav.role_name}")


@favorites_app.command("add")
def add_favorite(
    account_id: Annotated[str, typer.Argument(help="AWS account ID (12 digits).")],
    role_name: Annotated[str, typer.Argument(help="Role name.")],
) -> None:
    """Add a favorite."""
    mgr = FavoritesManager()
    mgr.add(account_id, role_name)
    typer.echo(f"Added {account_id}:{role_name} to favorites.")


@favorites_app.command("remove")
def remove_favorite(
    account_id: Annotated[str, typer.Argument(help="AWS account ID (12 digits).")],
    role_name: Annotated[str, typer.Argument(help="Role name.")],
) -> None:
    """Remove a favorite."""
    mgr = FavoritesManager()
    mgr.remove(account_id, role_name)
    typer.echo(f"Removed {account_id}:{role_name} from favorites.")


@favorites_app.command("clear")
def clear_favorites() -> None:
    """Clear all favorites."""
    mgr = FavoritesManager()
    mgr.clear()
    typer.echo("All favorites cleared.")
