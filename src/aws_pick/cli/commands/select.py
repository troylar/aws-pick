"""Select command for choosing AWS accounts/roles."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from aws_pick.core.selector import select_accounts
from aws_pick.exceptions import InvalidAccountError, InvalidSelectionError

select_app = typer.Typer(help="Select AWS accounts/roles.", no_args_is_help=True)


@select_app.command("run")
def run(
    input_file: Annotated[
        Optional[Path],
        typer.Option("--input", "-i", help="JSON file with account/role data."),
    ] = None,
    select: Annotated[
        Optional[list[str]],
        typer.Option("--select", "-s", help="Non-interactive: account_id:role_name pairs."),
    ] = None,
    preset_name: Annotated[
        Optional[str],
        typer.Option("--preset", "-p", help="Load a named preset."),
    ] = None,
    favorites: Annotated[
        bool,
        typer.Option("--favorites", help="Select all favorites."),
    ] = False,
    output_json: Annotated[
        bool,
        typer.Option("--json", help="Output results as JSON."),
    ] = False,
    output_file: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Write results to file."),
    ] = None,
) -> None:
    """Select AWS accounts/roles interactively or non-interactively."""
    accounts = _load_accounts(input_file)
    if accounts is None:
        raise typer.Exit(code=1)

    interactive = select is None and not favorites and preset_name is None
    selections = list(select) if select else None

    if favorites:
        from aws_pick.core.favorites import FavoritesManager

        mgr = FavoritesManager()
        fav_list = mgr.list()
        selections = [f"{f.account_id}:{f.role_name}" for f in fav_list]
        interactive = False

    if preset_name:
        from aws_pick.core.presets import PresetsManager

        mgr_p = PresetsManager()
        try:
            preset = mgr_p.get(preset_name)
            selections = [f"{item.account_id}:{item.role_name}" for item in preset.items]
            interactive = False
        except Exception as e:
            typer.echo(f"Error loading preset: {e}", err=True)
            raise typer.Exit(code=1)

    try:
        result = select_accounts(accounts, interactive=interactive, selections=selections)
    except InvalidAccountError as e:
        typer.echo(f"Invalid account data: {e}", err=True)
        raise typer.Exit(code=1)
    except InvalidSelectionError as e:
        typer.echo(f"Invalid selection: {e}", err=True)
        raise typer.Exit(code=3)

    if result.cancelled:
        raise typer.Exit(code=2)

    output = json.dumps({"selected": result.selected, "cancelled": result.cancelled}, indent=2)
    if output_file:
        output_file.write_text(output, encoding="utf-8")
    elif output_json:
        typer.echo(output)
    else:
        for item in result.selected:
            typer.echo(f"{item['account_id']}:{item['role_name']} ({item['account_name']})")


def _load_accounts(input_file: Path | None) -> list[dict[str, str]] | None:
    """Load accounts from file or stdin."""
    if input_file is not None:
        if not input_file.exists():
            typer.echo(f"Input file not found: {input_file}", err=True)
            return None
        try:
            data = json.loads(input_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else data.get("accounts", [])
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON in input file: {e}", err=True)
            return None

    if not sys.stdin.isatty():
        try:
            data = json.load(sys.stdin)
            return data if isinstance(data, list) else data.get("accounts", [])
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON from stdin: {e}", err=True)
            return None

    typer.echo("No input provided. Use --input or pipe JSON to stdin.", err=True)
    return None
