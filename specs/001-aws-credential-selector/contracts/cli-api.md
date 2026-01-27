# CLI API Contract: AWS Credential Selector

**Feature**: 001-aws-credential-selector
**Date**: 2026-01-26

This document defines the command-line interface for `aws-pick`.

## Commands

### `aws-pick select`

Launch the interactive TUI selector or perform non-interactive selection.

```
aws-pick select [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input` / `-i` | PATH | stdin | Path to JSON file containing account/role list. If omitted, reads from stdin. |
| `--select` / `-s` | TEXT (multiple) | none | Non-interactive selection(s) in `account_id:role_name` format. Bypasses TUI. |
| `--preset` / `-p` | TEXT | none | Load a saved preset by name, select its items, and return. Bypasses TUI. |
| `--favorites` | flag | false | Select all favorites and return. Bypasses TUI. |
| `--json` | flag | false | Output results as JSON (default for non-interactive). |
| `--output` / `-o` | PATH | stdout | Write results to file instead of stdout. |

**Input format** (JSON array):

```json
[
  {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "AdminAccess"},
  {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "ReadOnly"},
  {"account_id": "987654321098", "account_name": "my-app-dev", "role_name": "AdminAccess", "environment": "development"}
]
```

**Output format** (JSON, when `--json` or non-interactive):

```json
{
  "selected": [
    {"account_id": "123456789012", "account_name": "my-app-prod", "role_name": "AdminAccess"},
    {"account_id": "987654321098", "account_name": "my-app-dev", "role_name": "AdminAccess"}
  ],
  "count": 2,
  "cancelled": false
}
```

**Exit codes**:

| Code | Meaning |
|------|---------|
| 0 | Success (selections returned) |
| 1 | Error (invalid input, file not found, etc.) |
| 2 | User cancelled (Ctrl+C / Escape, empty selection) |
| 3 | Invalid selection (non-interactive mode, account/role not found) |

**Examples**:

```bash
# Interactive TUI with input from file
aws-pick select --input accounts.json

# Interactive TUI with input from pipe
cat accounts.json | aws-pick select

# Non-interactive selection
aws-pick select --input accounts.json \
  --select 123456789012:AdminAccess \
  --select 987654321098:ReadOnly \
  --json

# Load preset
aws-pick select --input accounts.json --preset daily-dev --json

# Select all favorites
aws-pick select --input accounts.json --favorites --json
```

---

### `aws-pick preset`

Manage saved presets.

```
aws-pick preset [SUBCOMMAND]
```

**Subcommands**:

| Subcommand | Description |
|------------|-------------|
| `list` | List all saved presets with item counts |
| `show NAME` | Show the contents of a preset |
| `delete NAME` | Delete a preset |

**Examples**:

```bash
aws-pick preset list
aws-pick preset show daily-dev
aws-pick preset delete daily-dev
```

Note: Presets are created interactively via the TUI (save current selection) or programmatically via the library API. The CLI `preset` command is for management only.

---

### `aws-pick favorites`

Manage favorites.

```
aws-pick favorites [SUBCOMMAND]
```

**Subcommands**:

| Subcommand | Description |
|------------|-------------|
| `list` | List all favorites |
| `add ACCOUNT_ID ROLE_NAME` | Add a favorite |
| `remove ACCOUNT_ID ROLE_NAME` | Remove a favorite |
| `clear` | Remove all favorites |

**Examples**:

```bash
aws-pick favorites list
aws-pick favorites add 123456789012 AdminAccess
aws-pick favorites remove 123456789012 AdminAccess
aws-pick favorites clear
```

---

### `aws-pick history`

View and manage selection history.

```
aws-pick history [SUBCOMMAND]
```

**Subcommands**:

| Subcommand | Description |
|------------|-------------|
| `list` | Show recently selected accounts (last 30 days by default) |
| `clear` | Clear all history |

**Options for `list`**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days` | INT | 30 | Show history from last N days |
| `--json` | flag | false | Output as JSON |

**Examples**:

```bash
aws-pick history list
aws-pick history list --days 7 --json
aws-pick history clear
```
