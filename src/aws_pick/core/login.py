"""Batch login orchestration with progress callbacks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from aws_pick.models.account import AccountRole
from aws_pick.models.selection import (
    BatchLoginResult,
    ItemLoginResult,
    LoginResult,
)


async def process_batch(
    items: list[AccountRole],
    handler: Callable[[dict[str, Any]], LoginResult],
    on_progress: Callable[[ItemLoginResult], None] | None = None,
) -> BatchLoginResult:
    """Process login for each selected item sequentially.

    Args:
        items: List of selected AccountRole items.
        handler: Sync callback that processes a single item dict and returns LoginResult.
        on_progress: Optional callback invoked after each item completes.

    Returns:
        BatchLoginResult with all item results.
    """
    results: list[ItemLoginResult] = []
    for item in items:
        item_dict = item.to_dict()
        try:
            lr = await asyncio.to_thread(handler, item_dict)
            result = ItemLoginResult(
                account_id=item.account.account_id,
                account_name=item.account.account_name,
                role_name=item.role.role_name,
                success=lr.success,
                error=lr.error,
            )
        except asyncio.CancelledError:
            result = ItemLoginResult(
                account_id=item.account.account_id,
                account_name=item.account.account_name,
                role_name=item.role.role_name,
                success=False,
                error="Cancelled",
            )
            results.append(result)
            if on_progress:
                on_progress(result)
            break
        except Exception as exc:
            result = ItemLoginResult(
                account_id=item.account.account_id,
                account_name=item.account.account_name,
                role_name=item.role.role_name,
                success=False,
                error=str(exc),
            )
        results.append(result)
        if on_progress:
            on_progress(result)
    return BatchLoginResult(results=results)
