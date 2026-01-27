# aws-pick

[![PyPI version](https://img.shields.io/pypi/v/aws-pick.svg)](https://pypi.org/project/aws-pick/)
[![Python versions](https://img.shields.io/pypi/pyversions/aws-pick.svg)](https://pypi.org/project/aws-pick/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build status](https://img.shields.io/github/actions/workflow/status/troylar/aws-pick/ci.yml?branch=main)](https://github.com/troylar/aws-pick/actions)
[![Coverage](https://img.shields.io/codecov/c/github/troylar/aws-pick)](https://codecov.io/gh/troylar/aws-pick)
[![Downloads](https://img.shields.io/pypi/dm/aws-pick.svg)](https://pypi.org/project/aws-pick/)

**Interactive TUI and Python library for selecting AWS account/role credentials.**

Managing dozens of AWS accounts and IAM roles means constantly hunting through config files or retyping ARNs. `aws-pick` gives you a fast, keyboard-driven terminal UI to search, select, and act on account/role pairs -- and it embeds directly into your own Python tools as a library.

## Installation

```bash
pip install aws-pick
```

Requires Python 3.10+.

## Key Features

- **Interactive TUI** -- Full-screen terminal selector built on [Textual](https://textual.textualize.io/) with keyboard navigation, real-time filtering, and multi-select
- **Embeddable library** -- One function call (`select_accounts()`) drops the TUI into any Python script and returns structured results
- **Favorites and presets** -- Star frequently used roles; save and reload named selection sets
- **Environment awareness** -- Accounts are auto-classified as production/staging/development with color-coded tags and a confirmation gate before acting on production resources
- **Flexible grouping** -- View accounts grouped by account name, by role name, or as a flat list -- cycle with a single keystroke
- **Selection history** -- Tracks recently used account/role pairs with relative timestamps
- **Non-interactive mode** -- Pass explicit `account_id:role_name` selections for CI/CD pipelines and scripts
- **Login callbacks** -- Hook in your own authentication logic (SSO, STS AssumeRole, etc.) and get structured success/failure results

## Quick Start

```python
from aws_pick import select_accounts

result = select_accounts([
    {"account_id": "111111111111", "account_name": "prod", "role_name": "Admin"},
    {"account_id": "222222222222", "account_name": "dev", "role_name": "Developer"},
    {"account_id": "222222222222", "account_name": "dev", "role_name": "ReadOnly"},
])

if not result.cancelled:
    for item in result.selected:
        print(f"{item['account_name']} -> {item['role_name']}")
```

This launches the TUI, lets the user pick one or more account/role pairs, and returns the selections as a list of dicts.

## Usage Examples

### Basic: Embed in a CLI tool

```python
from aws_pick import select_accounts

accounts = load_accounts_from_your_source()  # list of dicts

result = select_accounts(accounts, title="Deploy Target")

if result.cancelled:
    print("Aborted.")
else:
    for item in result.selected:
        deploy_to(item["account_id"], item["role_name"])
```

### With login callbacks

Provide an `on_login` callback to authenticate immediately after selection. The TUI shows a progress screen as each login executes.

```python
from aws_pick import select_accounts, LoginResult

def assume_role(item: dict) -> LoginResult:
    try:
        session = boto3.Session()
        sts = session.client("sts")
        sts.assume_role(
            RoleArn=f"arn:aws:iam::{item['account_id']}:role/{item['role_name']}",
            RoleSessionName="aws-pick",
        )
        return LoginResult(success=True)
    except Exception as e:
        return LoginResult(success=False, error=str(e))

result = select_accounts(accounts, on_login=assume_role)

if result.login_results:
    print(f"{result.login_results.succeeded}/{result.login_results.total} succeeded")
```

### Non-interactive mode for scripts

Skip the TUI entirely by passing explicit selections. Useful for CI/CD, cron jobs, or wrapping in shell scripts.

```python
from aws_pick import select_accounts

result = select_accounts(
    accounts,
    interactive=False,
    selections=["111111111111:Admin", "222222222222:Developer"],
)
```

### Managing favorites and presets programmatically

```python
from aws_pick import manage_favorites, manage_presets

# Favorites
favs = manage_favorites()
favs.add("111111111111", "Admin")
favs.add("222222222222", "Developer")
print(favs.list())   # [Favorite(...), ...]
favs.remove("111111111111", "Admin")

# Presets (named selection sets)
presets = manage_presets()
presets.save("deploy-prod", [
    Favorite(account_id="111111111111", role_name="Admin"),
    Favorite(account_id="333333333333", role_name="DeployRole"),
])
print(presets.list_names())  # ["deploy-prod"]
preset = presets.get("deploy-prod")
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Up` / `Down` | Navigate items |
| `Space` | Toggle selection |
| `Enter` | Confirm selections |
| `Escape` | Cancel and exit |
| `/` | Focus filter bar |
| `Tab` | Toggle filter / list focus |
| `a` / `d` | Select all / Deselect all |
| `f` | Toggle favorite |
| `F` | Select all favorites |
| `g` | Cycle grouping mode |
| `s` / `l` | Save / Load preset |
| `?` | Show help overlay |

## API Reference

### `select_accounts(accounts, *, interactive=True, selections=None, on_login=None, config_dir=None, title="Select Accounts")`

Main entry point. Launches the TUI (or runs non-interactively) and returns a `SelectionResult`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `accounts` | `list[dict]` | List of dicts with `account_id`, `account_name`, `role_name`, and optional `environment` |
| `interactive` | `bool` | `True` for TUI, `False` for scripted selection |
| `selections` | `list[str]` | `"account_id:role_name"` strings (required when `interactive=False`) |
| `on_login` | `Callable` | Callback receiving a selected dict, returns `LoginResult` |
| `config_dir` | `str \| Path` | Override config directory for favorites/presets/history |
| `title` | `str` | Panel header title in the TUI |

### `SelectionResult`

| Field | Type | Description |
|-------|------|-------------|
| `selected` | `list[dict]` | Selected account/role dicts |
| `cancelled` | `bool` | `True` if the user pressed Escape |
| `login_results` | `BatchLoginResult \| None` | Login outcomes when `on_login` is provided |

### `LoginResult`

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether login succeeded |
| `error` | `str \| None` | Error message on failure |

### `manage_favorites(*, config_dir=None)` / `manage_presets(*, config_dir=None)`

Factory functions returning `FavoritesManager` and `PresetsManager` for programmatic CRUD on persisted favorites and named presets.

## CLI

`aws-pick` also ships a CLI powered by [Typer](https://typer.tiangolo.com/):

```bash
aws-pick select          # Launch the TUI selector
aws-pick favorites list  # List saved favorites
aws-pick preset list     # List saved presets
aws-pick history show    # Show selection history
```

## Development

```bash
git clone https://github.com/troylar/aws-pick.git
cd aws-pick
pip install -e ".[dev]"
```

### Running tests

```bash
pytest                     # All 225+ tests
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration + TUI pilot tests
pytest --cov=aws_pick      # With coverage
```

### Code quality

```bash
ruff check .               # Lint
ruff check . --fix         # Auto-fix
black .                    # Format
mypy src/ --strict         # Type checking
```

### Code style

- **Black** with 120-char line length
- **Ruff** (rules: E, F, I, N, W)
- **mypy** strict mode
- Type hints on all functions

## Contributing

1. Open an issue describing the change
2. Fork and create a branch: `issue-###-short-description`
3. Write tests (minimum 80% coverage)
4. Ensure `pytest`, `ruff check`, and `mypy --strict` pass
5. Open a PR referencing the issue (`Closes #123`)

Commit format: `type(scope): description (#issue)`

## Roadmap

- [ ] AWS SSO / IAM Identity Center integration
- [ ] Profile generation (`~/.aws/config` writer)
- [ ] Plugin system for custom login providers
- [ ] Configurable environment patterns
- [ ] Export selections to shell environment variables

## License

[MIT](LICENSE)
