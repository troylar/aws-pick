# Quickstart: AWS Credential Selector

**Feature**: 001-aws-credential-selector

## Installation

```bash
pip install aws-pick
```

## As a CLI Tool

### Interactive TUI

```bash
# From a file
aws-pick select --input accounts.json

# From stdin (pipe from your existing tool)
your-auth-tool list-accounts | aws-pick select
```

The TUI launches with:
- Arrow keys to navigate, Space to select/deselect
- Type to filter by account name, ID, or role
- `f` to toggle favorites, `F` to select all favorites
- `g` to cycle grouping (by account → by role → flat)
- `?` for full keyboard shortcut help
- Enter to confirm, Escape to cancel

### Non-Interactive

```bash
aws-pick select --input accounts.json \
  --select 123456789012:AdminAccess \
  --select 987654321098:ReadOnly \
  --json
```

## As a Library

### Basic Selection

```python
from aws_pick import select_accounts

accounts = [
    {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "AdminAccess"},
    {"account_id": "987654321098", "account_name": "my-app-dev", "role_name": "AdminAccess"},
]

result = select_accounts(accounts)
for item in result.selected:
    print(f"{item['account_name']} / {item['role_name']}")
```

### With Login Handler

```python
from aws_pick import select_accounts, LoginResult

def my_login(account_role: dict) -> LoginResult:
    # Your credential generation logic here
    return LoginResult(success=True)

result = select_accounts(accounts, on_login=my_login)
print(f"{result.login_results.succeeded}/{result.login_results.total} succeeded")
```

### Non-Interactive (Scripting)

```python
result = select_accounts(
    accounts,
    interactive=False,
    selections=["123456789012:AdminAccess"],
)
```

## Input Format

The account list is a JSON array (or Python list of dicts):

```json
[
  {
    "account_id": "123456789012",
    "account_name": "my-app-prod",
    "role_name": "AdminAccess",
    "environment": "production"
  }
]
```

Required fields: `account_id`, `account_name`, `role_name`.
Optional fields: `environment` (for color-coded environment indicators).

## Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| Up/Down | Navigate list |
| Space | Toggle selection |
| Enter | Confirm selections |
| Escape | Cancel (return empty) |
| / or type | Filter/search |
| a | Select all visible |
| d | Deselect all visible |
| f | Toggle favorite on current item |
| F | Select all favorites |
| g | Cycle grouping mode |
| s | Save current selection as preset |
| l | Load a preset |
| ? | Show help overlay |
