"""Unit tests for batch login orchestration (T055)."""

from __future__ import annotations

import pytest

from aws_pick.core.login import process_batch
from aws_pick.models.account import AccountRole, AwsAccount, AwsRole
from aws_pick.models.selection import ItemLoginResult, LoginResult


def _make_items(n: int = 3) -> list[AccountRole]:
    return [
        AccountRole(
            account=AwsAccount(account_id=f"{i:012d}", account_name=f"account-{i}"),
            role=AwsRole(role_name="Admin"),
        )
        for i in range(1, n + 1)
    ]


class TestProcessBatch:
    @pytest.mark.asyncio
    async def test_all_succeed(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=True)

        result = await process_batch(_make_items(), handler)
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_all_fail(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=False, error="Auth denied")

        result = await process_batch(_make_items(), handler)
        assert result.total == 3
        assert result.succeeded == 0
        assert result.failed == 3

    @pytest.mark.asyncio
    async def test_mixed_results(self) -> None:
        call_count = 0

        def handler(item: dict) -> LoginResult:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return LoginResult(success=False, error="Failed")
            return LoginResult(success=True)

        result = await process_batch(_make_items(), handler)
        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_handler_exception(self) -> None:
        def handler(item: dict) -> LoginResult:
            raise RuntimeError("Connection error")

        result = await process_batch(_make_items(1), handler)
        assert result.total == 1
        assert result.failed == 1
        assert "Connection error" in (result.results[0].error or "")

    @pytest.mark.asyncio
    async def test_progress_callback_invoked(self) -> None:
        progress_items: list[ItemLoginResult] = []

        def handler(item: dict) -> LoginResult:
            return LoginResult(success=True)

        def on_progress(result: ItemLoginResult) -> None:
            progress_items.append(result)

        await process_batch(_make_items(), handler, on_progress=on_progress)
        assert len(progress_items) == 3
        assert all(p.success for p in progress_items)

    @pytest.mark.asyncio
    async def test_empty_items(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=True)

        result = await process_batch([], handler)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_result_contains_account_info(self) -> None:
        def handler(item: dict) -> LoginResult:
            return LoginResult(success=True)

        items = _make_items(1)
        result = await process_batch(items, handler)
        assert result.results[0].account_id == "000000000001"
        assert result.results[0].account_name == "account-1"
        assert result.results[0].role_name == "Admin"
