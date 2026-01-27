# Library API Contract: AWS Credential Selector

**Feature**: 001-aws-credential-selector
**Date**: 2026-01-26

This document defines the public Python API for `aws_pick` when used as an importable library.

## Public API Surface

### `select_accounts` (primary entry point)

```python
def select_accounts(
    accounts: list[dict],
    *,
    interactive: bool = True,
    selections: list[str] | None = None,
    on_login: Callable[[dict], LoginResult] | None = None,
    config_dir: str | Path | None = None,
) -> SelectionResult:
    """
    Launch the credential selector.

    Args:
        accounts: List of account/role dicts. Each dict must contain:
            - account_id (str): 12-digit AWS account ID
            - account_name (str): Human-readable account name
            - role_name (str): IAM role name
            - environment (str, optional): Explicit environment tag
        interactive: If True (default), launch the TUI. If False, use
            `selections` parameter for non-interactive mode.
        selections: List of "account_id:role_name" strings for non-interactive
            selection. Required when interactive=False.
        on_login: Optional callback invoked for each selected account/role
            pair upon confirmation. Receives a dict with account_id,
            account_name, and role_name. Must return a LoginResult.
        config_dir: Override the default config directory for favorites,
            presets, and history. Defaults to platform-appropriate user
            config directory.

    Returns:
        SelectionResult containing the selected items and optional
        login results.

    Raises:
        ValueError: If accounts list is empty or contains invalid entries.
        ValueError: If interactive=False and selections is None.
    """
```

**Input schema** (each dict in `accounts`):

```python
{
    "account_id": "123456789012",     # required, 12-digit string
    "account_name": "my-app-prod",    # required, non-empty string
    "role_name": "AdminAccess",       # required, non-empty string
    "environment": "production",      # optional, explicit environment tag
}
```

**Output schema** (`SelectionResult`):

```python
@dataclass
class SelectionResult:
    selected: list[dict]              # list of selected account/role dicts
    cancelled: bool                   # True if user cancelled (Ctrl+C/Escape)
    login_results: BatchLoginResult | None  # present if on_login was provided
```

---

### `LoginResult` (callback return type)

```python
@dataclass
class LoginResult:
    success: bool
    error: str | None = None
```

---

### `BatchLoginResult` (aggregate login results)

```python
@dataclass
class BatchLoginResult:
    results: list[ItemLoginResult]
    total: int
    succeeded: int
    failed: int

@dataclass
class ItemLoginResult:
    account_id: str
    account_name: str
    role_name: str
    success: bool
    error: str | None = None
```

---

### `manage_favorites` (favorites management)

```python
def manage_favorites(
    *,
    config_dir: str | Path | None = None,
) -> FavoritesManager:
    """
    Return a FavoritesManager for programmatic favorites access.
    """

class FavoritesManager:
    def list(self) -> list[dict]: ...
    def add(self, account_id: str, role_name: str) -> None: ...
    def remove(self, account_id: str, role_name: str) -> None: ...
    def clear(self) -> None: ...
```

---

### `manage_presets` (preset management)

```python
def manage_presets(
    *,
    config_dir: str | Path | None = None,
) -> PresetsManager:
    """
    Return a PresetsManager for programmatic preset access.
    """

class PresetsManager:
    def list(self) -> list[str]: ...
    def get(self, name: str) -> list[dict]: ...
    def save(self, name: str, items: list[dict]) -> None: ...
    def delete(self, name: str) -> None: ...
```

---

## Usage Examples

### Minimal (TUI selector, return selections)

```python
from aws_pick import select_accounts

accounts = [
    {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "AdminAccess"},
    {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "ReadOnly"},
    {"account_id": "987654321098", "account_name": "my-app-dev", "role_name": "AdminAccess"},
]

result = select_accounts(accounts)
for item in result.selected:
    print(f"{item['account_name']} / {item['role_name']}")
```

### With login handler

```python
from aws_pick import select_accounts, LoginResult

def assume_role(account_role: dict) -> LoginResult:
    try:
        # Your STS AssumeRole logic here
        sts_client.assume_role(
            RoleArn=f"arn:aws:iam::{account_role['account_id']}:role/{account_role['role_name']}",
            RoleSessionName="session",
        )
        return LoginResult(success=True)
    except Exception as e:
        return LoginResult(success=False, error=str(e))

result = select_accounts(accounts, on_login=assume_role)
print(f"Logged into {result.login_results.succeeded}/{result.login_results.total} accounts")
```

### Non-interactive mode

```python
from aws_pick import select_accounts

result = select_accounts(
    accounts,
    interactive=False,
    selections=["123456789012:AdminAccess", "987654321098:ReadOnly"],
)
```
