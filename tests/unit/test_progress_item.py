"""Unit tests for ProgressItem widget."""

from __future__ import annotations

from aws_pick.tui.widgets.progress_item import ProgressItem


class TestProgressItem:
    def test_creation(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        assert item.status == "pending"

    def test_set_processing(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_processing()
        assert item.status == "processing"

    def test_set_result_success(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_result(success=True)
        assert item.status == "success"

    def test_set_result_failure(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_result(success=False, error="Auth failed")
        assert item.status == "failed"
        assert item._error == "Auth failed"

    def test_render_pending(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        text = item.render()
        assert "test" in text.plain
        assert "Admin" in text.plain

    def test_render_processing(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_processing()
        text = item.render()
        assert "..." in text.plain

    def test_render_success(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_result(success=True)
        text = item.render()
        assert "v" in text.plain

    def test_render_failed(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_result(success=False, error="Network error")
        text = item.render()
        assert "x" in text.plain
        assert "Network error" in text.plain

    def test_render_failed_no_error(self) -> None:
        item = ProgressItem(account_name="test", role_name="Admin", account_id="123456789012")
        item.set_result(success=False)
        text = item.render()
        assert "x" in text.plain
