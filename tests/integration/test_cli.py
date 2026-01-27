"""CLI integration tests (T060)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aws_pick.cli.app import app

runner = CliRunner()


def _write_accounts_file(tmp_path: Path) -> Path:
    data = [
        {"account_id": "111111111111", "account_name": "dev-account", "role_name": "Admin"},
        {"account_id": "222222222222", "account_name": "prod-account", "role_name": "ReadOnly"},
    ]
    path = tmp_path / "accounts.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestSelectCommand:
    def test_non_interactive_json_output(self, tmp_path: Path) -> None:
        acct_file = _write_accounts_file(tmp_path)
        result = runner.invoke(
            app,
            ["select", "run", "--input", str(acct_file), "--select", "111111111111:Admin", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["selected"]) == 1
        assert data["selected"][0]["account_id"] == "111111111111"

    def test_non_interactive_multiple_selections(self, tmp_path: Path) -> None:
        acct_file = _write_accounts_file(tmp_path)
        result = runner.invoke(
            app,
            [
                "select",
                "run",
                "--input",
                str(acct_file),
                "--select",
                "111111111111:Admin",
                "--select",
                "222222222222:ReadOnly",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["selected"]) == 2

    def test_invalid_selection_exit_code_3(self, tmp_path: Path) -> None:
        acct_file = _write_accounts_file(tmp_path)
        result = runner.invoke(
            app,
            ["select", "run", "--input", str(acct_file), "--select", "999999999999:NoRole"],
        )
        assert result.exit_code == 3

    def test_missing_input_file(self) -> None:
        result = runner.invoke(
            app,
            ["select", "run", "--input", "/nonexistent/file.json", "--select", "111111111111:Admin"],
        )
        assert result.exit_code == 1

    def test_output_to_file(self, tmp_path: Path) -> None:
        acct_file = _write_accounts_file(tmp_path)
        out_file = tmp_path / "output.json"
        result = runner.invoke(
            app,
            [
                "select",
                "run",
                "--input",
                str(acct_file),
                "--select",
                "111111111111:Admin",
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(data["selected"]) == 1

    def test_human_readable_output(self, tmp_path: Path) -> None:
        acct_file = _write_accounts_file(tmp_path)
        result = runner.invoke(
            app,
            ["select", "run", "--input", str(acct_file), "--select", "111111111111:Admin"],
        )
        assert result.exit_code == 0
        assert "111111111111:Admin" in result.stdout

    def test_invalid_json_file(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{broken", encoding="utf-8")
        result = runner.invoke(
            app,
            ["select", "run", "--input", str(bad_file), "--select", "111111111111:Admin"],
        )
        assert result.exit_code == 1

    def test_stdin_input(self, tmp_path: Path) -> None:
        data = json.dumps(
            [
                {"account_id": "111111111111", "account_name": "dev-account", "role_name": "Admin"},
            ]
        )
        result = runner.invoke(
            app,
            ["select", "run", "--select", "111111111111:Admin", "--json"],
            input=data,
        )
        assert result.exit_code == 0

    def test_accounts_dict_format(self, tmp_path: Path) -> None:
        data = {
            "accounts": [
                {"account_id": "111111111111", "account_name": "dev-account", "role_name": "Admin"},
            ]
        }
        path = tmp_path / "dict_accounts.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = runner.invoke(
            app,
            ["select", "run", "--input", str(path), "--select", "111111111111:Admin", "--json"],
        )
        assert result.exit_code == 0


class TestFavoritesCommand:
    def test_list_empty(self) -> None:
        result = runner.invoke(app, ["favorites", "list"])
        assert result.exit_code == 0

    def test_add(self) -> None:
        result = runner.invoke(app, ["favorites", "add", "123456789012", "Admin"])
        assert result.exit_code == 0
        assert "Added" in result.stdout

    def test_remove(self) -> None:
        result = runner.invoke(app, ["favorites", "remove", "123456789012", "Admin"])
        assert result.exit_code == 0
        assert "Removed" in result.stdout

    def test_clear(self) -> None:
        result = runner.invoke(app, ["favorites", "clear"])
        assert result.exit_code == 0
        assert "cleared" in result.stdout


class TestPresetCommand:
    def test_list_empty(self) -> None:
        result = runner.invoke(app, ["preset", "list"])
        assert result.exit_code == 0

    def test_show_nonexistent(self) -> None:
        result = runner.invoke(app, ["preset", "show", "nonexistent"])
        assert result.exit_code == 1

    def test_delete_nonexistent(self) -> None:
        result = runner.invoke(app, ["preset", "delete", "nonexistent"])
        assert result.exit_code == 1


class TestHistoryCommand:
    def test_list_empty(self) -> None:
        result = runner.invoke(app, ["history", "list"])
        assert result.exit_code == 0

    def test_list_json(self) -> None:
        result = runner.invoke(app, ["history", "list", "--json"])
        assert result.exit_code == 0

    def test_list_with_days(self) -> None:
        result = runner.invoke(app, ["history", "list", "--days", "30"])
        assert result.exit_code == 0

    def test_clear(self) -> None:
        result = runner.invoke(app, ["history", "clear"])
        assert result.exit_code == 0
        assert "cleared" in result.stdout
