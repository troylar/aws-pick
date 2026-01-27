# Research: AWS Credential Selector

**Feature**: 001-aws-credential-selector
**Date**: 2026-01-26

## Decision 1: TUI Framework

**Decision**: Textual (by Textualize)

**Rationale**: Textual is the only Python TUI framework that natively provides all required widgets: `SelectionList` for multi-select, `Input` for search/filter, `Tree`/`Collapsible` for grouped sections, Rich markup for color-coding, `LoadingIndicator`/`ProgressBar` for progress indicators, and `Screen` system for help overlays. It has first-class Windows support (Windows Terminal, CMD, PowerShell), the highest visual quality of any terminal framework, and active corporate-backed development (Textualize company).

**Alternatives considered**:

| Option | Reason rejected |
|--------|----------------|
| Rich + InquirerPy | InquirerPy maintenance has stalled (last meaningful release 2022-2023). No support for grouped/collapsible sections or help overlays. |
| prompt_toolkit | Powerful low-level toolkit but requires building all widgets from scratch (no built-in checkboxes, trees, or selection lists). |
| urwid | No native Windows support. Legacy project with minimal maintenance. Dated visual aesthetics. |
| blessed/blessings | Effectively unmaintained. No widget system. Poor Windows support. |

---

## Decision 2: CLI Framework

**Decision**: Typer (built on Click)

**Rationale**: Typer's type-hint-based design naturally separates CLI argument parsing from core business logic. Functions remain plain Python and are directly importable as a library. Full mypy compatibility. Inherits Click's mature error handling and shell completion. Created by the FastAPI author with active maintenance.

**Alternatives considered**:

| Option | Reason rejected |
|--------|----------------|
| Click | Works but decorator-heavy style doesn't naturally encourage separation of concerns. Less type-safe. More verbose for no benefit since Typer wraps it. |
| argparse | Too verbose, no type safety, poor developer experience. Only advantage is zero dependencies. |
| Google Fire | "Magic" approach produces poor user-facing error messages and surprising behavior. Stalled development. |

---

## Decision 3: Configuration Persistence

**Decision**: `platformdirs` + JSON files

**Rationale**: JSON is stdlib (`json` module), maps perfectly to the data model (lists of dicts for favorites, named collections for presets, timestamped records for history), and is human-readable. `platformdirs` is the current standard for cross-platform config directory resolution (successor to `appdirs`). Zero additional serialization dependencies.

**File structure**:
```
<platform-config-dir>/aws-pick/
    config.json      # favorites + presets
    history.json     # session history (separate for independent pruning)
```

Separating config from history reduces corruption risk during frequent history writes.

**Corruption handling**: Atomic writes via temp-file-and-rename (`os.replace()`). On `JSONDecodeError`, back up corrupt file to `<name>.corrupt.bak`, log warning, start with defaults.

**Alternatives considered**:

| Option | Reason rejected |
|--------|----------------|
| TOML | No stdlib writer (need `tomli-w`). Awkward for list-heavy data. `tomllib` only in 3.11+. |
| YAML | Indentation-sensitivity risks silent corruption on hand-edits. External dependency. Type coercion surprises. |
| SQLite | Not human-readable. Overkill for data volume (<1000 records). Requires schema management. |
| INI/configparser | Cannot represent lists or nested structures without encoding hacks. |

---

## Decision 4: Package Structure

**Decision**: `src/` layout with strict `cli/ → core/` dependency boundary

**Rationale**: The `src/` layout is the PyPA-recommended standard that prevents accidental local imports during testing. The one-way dependency rule (`cli/` imports `core/`, never the reverse) ensures the library is importable without CLI dependencies.

**Build system**: `pyproject.toml` with Hatchling (modern PyPA-recommended build backend). No `setup.py` or `setup.cfg`.

**Entry points**: Console script via `[project.scripts]` + `__main__.py` for `python -m` support.

---

## Decision 5: Environment Classification

**Decision**: Built-in pattern matching with configurable overrides + explicit input tags

**Rationale**: Most organizations follow naming conventions (account names containing "prod", "dev", "staging"). Default pattern matching covers 80% of cases. The input data optionally includes an `environment` field for explicit classification. A local config file can override/extend the default patterns.

**Default patterns**:
- Production: `prod`, `production` → red indicator
- Development: `dev`, `develop`, `development` → green indicator
- Staging: `stg`, `staging`, `stage` → yellow indicator
- Unclassified: neutral/default indicator

---

## Decision 6: Data Models

**Decision**: Python dataclasses with `from_dict`/`to_dict` methods

**Rationale**: Dataclasses are stdlib (no Pydantic dependency), provide type hints, are immutable-friendly (`frozen=True`), and work naturally with JSON serialization. The data models are simple enough that Pydantic's validation features are unnecessary overhead.
