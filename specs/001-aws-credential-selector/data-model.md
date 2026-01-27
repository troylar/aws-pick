# Data Model: AWS Credential Selector

**Feature**: 001-aws-credential-selector
**Date**: 2026-01-26
**Source**: Feature spec entities + research decisions

## Entities

### AwsAccount

Represents an AWS account available for credential selection.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_id | string | yes | 12-digit AWS account ID |
| account_name | string | yes | Human-readable account name/alias |
| environment | string | no | Explicit environment classification (e.g., "production", "development", "staging"). If absent, derived from pattern matching on account_name. |

**Validation rules**:
- `account_id` must be exactly 12 digits
- `account_name` must be non-empty
- `environment`, if provided, takes precedence over pattern-matched classification

---

### AwsRole

Represents an IAM role within an account.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role_name | string | yes | IAM role name |

**Validation rules**:
- `role_name` must be non-empty

---

### AccountRole

The primary selectable item -- a pairing of an account and a role. This is the unit of selection in the TUI.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account | AwsAccount | yes | The AWS account |
| role | AwsRole | yes | The IAM role within the account |

**Validation rules**:
- Uniqueness: deduplicated by (account_id, role_name) tuple
- Input lists are deduplicated on load

**Relationships**:
- An AwsAccount can have many AccountRoles (one per role)
- An AwsRole name can appear across many AwsAccounts (e.g., "AdminAccess" in 30 accounts)

---

### Selection

The output of the selector -- a collection of AccountRole items chosen by the user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | list[AccountRole] | yes | The selected account/role pairs |

**State transitions**:
- Empty → items added via TUI interaction → confirmed (returned to caller)
- At any point, user cancellation resets to empty

---

### LoginResult

The outcome of invoking the login handler for a single AccountRole.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_role | AccountRole | yes | The account/role that was processed |
| success | boolean | yes | Whether the login handler succeeded |
| error | string | no | Error message if success is false |

---

### BatchLoginResult

The aggregate outcome of processing all selections through the login handler.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| results | list[LoginResult] | yes | Per-item results |
| total | integer | yes | Total items processed |
| succeeded | integer | yes | Count of successful items |
| failed | integer | yes | Count of failed items |

---

### Favorite

A persisted AccountRole pairing marked for quick access.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_id | string | yes | 12-digit AWS account ID |
| role_name | string | yes | IAM role name |

**Persistence**: Stored in `config.json` as a list of `{account_id, role_name}` objects.

**Behavior**:
- Loaded on TUI launch, displayed in dedicated "Favorites" section
- If a favorite's account/role is not in the current input list, it is shown as inactive/dimmed

---

### Preset

A named, saved collection of AccountRole pairings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | User-defined preset name |
| items | list[{account_id, role_name}] | yes | The account/role pairs in this preset |
| created_at | string (ISO 8601) | yes | When the preset was created |

**Persistence**: Stored in `config.json` as a dict keyed by preset name.

**Behavior**:
- Loading a preset selects all matching items from the current input list
- Items in the preset not found in the input list are reported as skipped

---

### HistoryEntry

A record of when an AccountRole was last selected.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| account_id | string | yes | 12-digit AWS account ID |
| role_name | string | yes | IAM role name |
| last_used | string (ISO 8601) | yes | When this pair was last selected |

**Persistence**: Stored in `history.json` as a list.

**Behavior**:
- Updated after each confirmed selection
- Entries older than 90 days (configurable) are pruned on startup
- Displayed as relative time (e.g., "2h ago") in the TUI

---

### EnvironmentPattern

Configuration for automatic environment classification based on account name patterns.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pattern | string | yes | Substring or regex to match against account_name |
| environment | string | yes | Classification label (e.g., "production", "development") |
| color | string | yes | Display color (e.g., "red", "green", "yellow") |

**Defaults**:
- `prod`, `production` → "production" (red)
- `dev`, `develop`, `development` → "development" (green)
- `stg`, `staging`, `stage` → "staging" (yellow)

---

## Persistence Schema

### config.json

```json
{
  "favorites": [
    {"account_id": "123456789012", "role_name": "AdminAccess"}
  ],
  "presets": {
    "daily-dev": {
      "items": [
        {"account_id": "123456789012", "role_name": "AdminAccess"},
        {"account_id": "987654321098", "role_name": "ReadOnly"}
      ],
      "created_at": "2026-01-26T10:30:00Z"
    }
  },
  "environment_patterns": [
    {"pattern": "prod", "environment": "production", "color": "red"},
    {"pattern": "dev", "environment": "development", "color": "green"},
    {"pattern": "stg", "environment": "staging", "color": "yellow"}
  ]
}
```

### history.json

```json
{
  "entries": [
    {
      "account_id": "123456789012",
      "role_name": "AdminAccess",
      "last_used": "2026-01-26T10:30:00Z"
    }
  ],
  "retention_days": 90
}
```
