# Implementation Plan: AWS Credential Selector

**Branch**: `001-aws-credential-selector` | **Date**: 2026-01-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-aws-credential-selector/spec.md`

## Summary

Build a Python library and CLI/TUI tool for selecting AWS account/role credentials from a provided list. The TUI uses Textual for a modern, cross-platform multi-select interface with search/filter, configurable grouping, favorites, named presets, environment indicators, and optional batch login with live progress. The library is importable for programmatic use with an optional login handler callback. The CLI provides both interactive (TUI) and non-interactive (JSON) modes.

## Technical Context

**Language/Version**: Python 3.10+ (type hints, pattern matching, `tomllib` fallback handled)
**Primary Dependencies**: Textual (TUI framework), Typer (CLI framework), Rich (terminal formatting, included via Textual), platformdirs (config directory resolution)
**Storage**: JSON files via `platformdirs` (config.json for favorites/presets, history.json for session history)
**Testing**: pytest + pytest-asyncio (Textual apps are async) + Textual's pilot testing framework
**Target Platform**: Windows 10+, Linux, macOS (cross-platform terminal)
**Project Type**: Single project (Python library + CLI)
**Performance Goals**: TUI renders in <200ms with 500 account entries; real-time filter response
**Constraints**: No credential storage; stateless except favorites/presets/history; minimal dependencies
**Scale/Scope**: Account lists up to 500 entries; single-user local tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is an unratified template with no project-specific principles defined. No gates to enforce. The CLAUDE.md project guidelines apply:

| Guideline | Status | Notes |
|-----------|--------|-------|
| Python 3.10+ | Pass | Minimum version set to 3.10 |
| pytest for testing | Pass | Using pytest + pytest-asyncio |
| mypy strict mode | Pass | `disallow_untyped_defs=true` in pyproject.toml |
| Black + Ruff formatting | Pass | Configured in pyproject.toml |
| 80% minimum test coverage | Pass | Will enforce via pytest-cov |
| GitHub issue required | Pass | Will create issue before implementation |

**Post-Phase 1 re-check**: All design decisions align with guidelines. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-aws-credential-selector/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── library-api.md   # Python library public API
│   └── cli-api.md       # CLI commands and options
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── aws_pick/
    ├── __init__.py              # Public API exports (select_accounts, LoginResult, etc.)
    ├── __main__.py              # python -m aws_pick support
    ├── cli/
    │   ├── __init__.py
    │   ├── app.py               # Typer app definition, main() entry point
    │   └── commands/
    │       ├── __init__.py
    │       ├── select.py        # select command (TUI launch + non-interactive)
    │       ├── preset.py        # preset list/show/delete commands
    │       ├── favorites.py     # favorites list/add/remove/clear commands
    │       └── history.py       # history list/clear commands
    ├── core/
    │   ├── __init__.py
    │   ├── selector.py          # Core selection logic (select_accounts function)
    │   ├── favorites.py         # FavoritesManager (CRUD + persistence)
    │   ├── presets.py           # PresetsManager (CRUD + persistence)
    │   ├── history.py           # HistoryManager (record, query, prune)
    │   ├── environment.py       # Environment classification (pattern matching + tags)
    │   └── login.py             # Batch login handler orchestration
    ├── models/
    │   ├── __init__.py
    │   ├── account.py           # AwsAccount, AwsRole, AccountRole dataclasses
    │   ├── selection.py         # SelectionResult, LoginResult, BatchLoginResult
    │   └── config.py            # Favorite, Preset, HistoryEntry dataclasses
    ├── storage/
    │   ├── __init__.py
    │   └── json_store.py        # JSON file read/write with atomic writes + corruption handling
    ├── tui/
    │   ├── __init__.py
    │   ├── app.py               # Textual App subclass (main TUI application)
    │   ├── screens/
    │   │   ├── __init__.py
    │   │   ├── selector.py      # Main selector screen (list + filter + status bar)
    │   │   ├── help.py          # Help overlay screen (keyboard shortcuts)
    │   │   ├── preset_save.py   # Save-preset dialog
    │   │   ├── preset_load.py   # Load-preset dialog
    │   │   └── progress.py      # Batch login progress screen
    │   ├── widgets/
    │   │   ├── __init__.py
    │   │   ├── account_list.py  # Grouped multi-select list widget
    │   │   ├── filter_bar.py    # Search/filter input widget
    │   │   ├── status_bar.py    # Selection count + hints footer
    │   │   └── progress_item.py # Per-item login progress indicator
    │   └── styles/
    │       └── app.tcss         # Textual CSS stylesheet
    └── exceptions.py            # Custom exceptions

tests/
├── conftest.py                  # Shared fixtures (mock accounts, tmp config dirs)
├── unit/
│   ├── test_models.py           # Dataclass validation, serialization
│   ├── test_selector.py         # Core selection logic
│   ├── test_favorites.py        # FavoritesManager
│   ├── test_presets.py          # PresetsManager
│   ├── test_history.py          # HistoryManager (including pruning)
│   ├── test_environment.py      # Environment classification
│   ├── test_login.py            # Batch login orchestration
│   └── test_json_store.py       # Atomic writes, corruption handling
├── integration/
│   ├── test_tui.py              # Textual pilot tests (TUI interaction)
│   ├── test_cli.py              # Typer CliRunner tests
│   └── test_library_api.py      # End-to-end library usage
└── contract/
    └── test_api_contract.py     # Verify public API matches contract docs
```

**Structure Decision**: Single project with `src/` layout. The `cli/` layer depends on `core/`, never the reverse. The `tui/` layer depends on `core/` and `models/`. The `core/` layer depends only on `models/` and `storage/`. This ensures `from aws_pick import select_accounts` works without pulling in Textual or Typer when only the non-interactive library API is used.

**Dependency direction**:
```
cli/ ──→ core/ ──→ models/
  │        │         ↑
  │        ↓         │
  │     storage/ ────┘
  ↓
tui/ ──→ core/
```

## Complexity Tracking

No constitution violations to justify (constitution is unratified template).

| Decision | Rationale |
|----------|-----------|
| Textual for TUI | Only framework that provides all required widgets natively with Windows support |
| Separate storage/ layer | Isolates JSON file I/O and atomic write logic from business logic |
| tui/ as separate package from cli/ | TUI is a Textual app with its own screens/widgets; CLI is a Typer wrapper. Mixing them would create tight coupling. |
