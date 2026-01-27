# Tasks: AWS Credential Selector

**Input**: Design documents from `/specs/001-aws-credential-selector/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included per project guidelines (80% minimum test coverage, pytest).

**Organization**: Tasks grouped by user story, ordered by priority (P1 → P2 → P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, packaging, and directory structure

- [x] T001 Create project directory structure per plan.md: `src/aws_pick/` with subdirectories `cli/`, `cli/commands/`, `core/`, `models/`, `storage/`, `tui/`, `tui/screens/`, `tui/widgets/`, `tui/styles/`, and `tests/` with `unit/`, `integration/`, `contract/`
- [x] T002 Create `pyproject.toml` with build system (hatchling), project metadata, Python >=3.10, dependencies (textual, typer, rich, platformdirs), dev dependencies (pytest, pytest-asyncio, pytest-cov, textual-dev, mypy, black, ruff), console_scripts entry point, and tool configs (mypy strict, black line-length 120, ruff rules)
- [x] T003 [P] Create all `__init__.py` files for packages: `src/aws_pick/__init__.py`, `cli/__init__.py`, `cli/commands/__init__.py`, `core/__init__.py`, `models/__init__.py`, `storage/__init__.py`, `tui/__init__.py`, `tui/screens/__init__.py`, `tui/widgets/__init__.py`
- [x] T004 [P] Create custom exceptions in `src/aws_pick/exceptions.py`: `InvalidAccountError`, `InvalidSelectionError`, `ConfigCorruptedError`, `PresetNotFoundError`
- [x] T005 [P] Create `.gitignore` additions for Python build artifacts, `.venv/`, `dist/`, `*.egg-info/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.coverage`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data models and storage layer that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create account models in `src/aws_pick/models/account.py`: `AwsAccount` (account_id: str, account_name: str, environment: str | None), `AwsRole` (role_name: str), `AccountRole` (account: AwsAccount, role: AwsRole) as frozen dataclasses with validation (12-digit account_id, non-empty names), `from_dict`/`to_dict` methods, and deduplication helper
- [x] T007 [P] Create selection models in `src/aws_pick/models/selection.py`: `SelectionResult` (selected: list[dict], cancelled: bool, login_results: BatchLoginResult | None), `LoginResult` (success: bool, error: str | None), `ItemLoginResult` (account_id, account_name, role_name, success, error), `BatchLoginResult` (results, total, succeeded, failed) as dataclasses
- [x] T008 [P] Create config models in `src/aws_pick/models/config.py`: `Favorite` (account_id: str, role_name: str), `Preset` (name: str, items: list[Favorite], created_at: str), `HistoryEntry` (account_id: str, role_name: str, last_used: str), `EnvironmentPattern` (pattern: str, environment: str, color: str) with `from_dict`/`to_dict` methods
- [x] T009 Implement JSON store in `src/aws_pick/storage/json_store.py`: `JsonStore` class with `read(path) -> dict`, `write(path, data)` using atomic writes (write to `.tmp`, `os.replace()`), corruption handling (catch `JSONDecodeError`, back up to `.corrupt.bak`, return defaults), `ensure_dir()` for creating parent directories, and `platformdirs.user_config_dir("aws-pick")` for default config path
- [x] T010 [P] Create shared test fixtures in `tests/conftest.py`: `mock_accounts` fixture (20 accounts, 3 roles each, mix of prod/dev/staging names), `tmp_config_dir` fixture (tmp_path based), `small_account_list` fixture (3 accounts), `large_account_list` fixture (100 accounts)
- [x] T011 [P] Write unit tests for models in `tests/unit/test_models.py`: test dataclass creation, validation (invalid account_id length, empty names), from_dict/to_dict round-trip, deduplication, frozen immutability
- [x] T012 [P] Write unit tests for JSON store in `tests/unit/test_json_store.py`: test read/write round-trip, atomic write behavior, corruption handling (backup + defaults), missing file returns defaults, directory creation

**Checkpoint**: Foundation ready - models validated, storage tested, user story implementation can begin

---

## Phase 3: User Story 1 - Select Multiple AWS Accounts/Roles via TUI (Priority: P1) MVP

**Goal**: Users can launch a TUI displaying accounts/roles grouped by account, select multiple items via keyboard, and confirm to return selections

**Independent Test**: Provide mock accounts, launch TUI, make selections, verify returned data matches expectations

### Implementation for User Story 1

- [x] T013 [US1] Create Textual CSS stylesheet in `src/aws_pick/tui/styles/app.tcss`: base layout (header, body, footer), color scheme (dark theme), selection highlight styles, group header styles, checkbox/selected indicator styles, scrollable container
- [x] T014 [US1] Create account_list widget in `src/aws_pick/tui/widgets/account_list.py`: custom Textual widget extending `Widget`, displays AccountRole items grouped by account name as collapsible sections, each item has a checkbox indicator, supports keyboard navigation (up/down arrows), space bar toggles selection, tracks selected items as a `set[tuple[str, str]]` (account_id, role_name), provides `selected_items` property, select-all (`a` key) and deselect-all (`d` key) for visible items
- [x] T015 [US1] Create status_bar widget in `src/aws_pick/tui/widgets/status_bar.py`: displays "N selected" count, key hints ("Enter: confirm | Esc: cancel | Space: toggle"), updates reactively when selections change
- [x] T016 [US1] Create selector screen in `src/aws_pick/tui/screens/selector.py`: Textual `Screen` composing account_list and status_bar widgets, receives list of `AccountRole` objects, handles Enter key (dismiss with selections), handles Escape key (dismiss with empty/cancelled), passes selection state between widgets
- [x] T017 [US1] Create TUI app in `src/aws_pick/tui/app.py`: Textual `App` subclass `CredentialSelectorApp`, accepts `list[AccountRole]` on init, pushes selector screen on mount, exposes `result: SelectionResult` property set on screen dismiss, `run()` returns after screen completes
- [x] T018 [US1] Implement core selector in `src/aws_pick/core/selector.py`: `select_accounts(accounts: list[dict], *, interactive=True, selections=None, on_login=None, config_dir=None) -> SelectionResult`, validates input dicts (required fields, 12-digit account_id), deduplicates by (account_id, role_name), converts dicts to AccountRole models, when `interactive=True` launches TUI app and returns result, handles empty account list (returns immediately with message)
- [x] T019 [US1] Wire cancellation handling: Ctrl+C signal handler in TUI app returns `SelectionResult(selected=[], cancelled=True)`, Escape key on selector screen does the same, no crash or traceback on cancellation
- [x] T020 [US1] Write unit tests for core selector in `tests/unit/test_selector.py`: test input validation (missing fields, invalid account_id), deduplication, empty list handling
- [x] T021 [US1] Write TUI pilot integration tests in `tests/integration/test_tui.py`: test app launches with mock data, test keyboard navigation (arrow keys move focus), test space bar toggles selection, test Enter returns selections, test Escape returns cancelled, test select-all/deselect-all shortcuts

**Checkpoint**: MVP functional -- TUI launches, displays grouped accounts, supports multi-select, returns results

---

## Phase 4: User Story 2 - Search and Filter Accounts/Roles (Priority: P1)

**Goal**: Users can type to filter the account/role list in real-time, matching against account name, account ID, and role name simultaneously

**Independent Test**: Provide 100 accounts, type "prod" in filter bar, verify only matching items shown with prior selections preserved

### Implementation for User Story 2

- [x] T022 [US2] Create filter_bar widget in `src/aws_pick/tui/widgets/filter_bar.py`: Textual `Input` widget styled as a search bar, emits `FilterChanged` message on each keystroke with current filter text, shows placeholder "Type to filter..." and clear button
- [x] T023 [US2] Implement filtering logic in `src/aws_pick/tui/widgets/account_list.py`: add `apply_filter(text: str)` method, case-insensitive substring match against account_name, account_id, and role_name simultaneously, when a role matches show it and its parent account group, when an account matches show all its roles, preserve selected items set when filter changes (items remain selected even if hidden)
- [x] T024 [US2] Integrate filter_bar into selector screen in `src/aws_pick/tui/screens/selector.py`: compose filter_bar at top, wire `FilterChanged` message to `account_list.apply_filter()`, handle filter clear (show all items)
- [x] T025 [US2] Write unit tests for filter logic in `tests/unit/test_selector.py`: test case-insensitive matching, test matching on each field (name, ID, role), test selection preservation across filter apply/clear, test empty filter shows all, test no-match shows empty list

**Checkpoint**: Search/filter operational -- users can find accounts quickly in large lists

---

## Phase 5: User Story 7 - Keyboard Shortcut Help Overlay (Priority: P1)

**Goal**: Users can press `?` to see all available keyboard shortcuts in a dismissable overlay

**Independent Test**: Launch TUI, press `?`, verify overlay lists all shortcuts, press any key to dismiss

### Implementation for User Story 7

- [x] T026 [US7] Create help screen in `src/aws_pick/tui/screens/help.py`: Textual `ModalScreen` displaying a styled table of all keyboard shortcuts (Up/Down: navigate, Space: toggle, Enter: confirm, Esc: cancel, a/d: select/deselect all, /: filter, ?: help), dismisses on any key press
- [x] T027 [US7] Add help hint to status_bar in `src/aws_pick/tui/widgets/status_bar.py`: append "? help" to the persistent hint text in the footer
- [x] T028 [US7] Wire `?` key binding in `src/aws_pick/tui/screens/selector.py`: push help screen as modal on `?` key, ensure filter state and selections are unaffected when overlay is shown/dismissed

**Checkpoint**: All P1 stories complete -- core TUI is fully functional with selection, filtering, and help

---

## Phase 6: User Story 3 - Configurable Grouping (Priority: P2)

**Goal**: Users can cycle between group-by-account, group-by-role, and flat list views while preserving selections

**Independent Test**: Provide accounts with overlapping role names, toggle grouping modes, verify reorganization with selections preserved

### Implementation for User Story 3

- [x] T029 [US3] Implement grouping modes in `src/aws_pick/tui/widgets/account_list.py`: add `GroupingMode` enum (`BY_ACCOUNT`, `BY_ROLE`, `FLAT`), refactor rendering to use current mode, `BY_ACCOUNT`: group headers are account names (existing behavior), `BY_ROLE`: group headers are role names with account items underneath, `FLAT`: alphabetically sorted flat list with "account / role" display
- [x] T030 [US3] Add grouping toggle to selector screen in `src/aws_pick/tui/screens/selector.py`: wire `g` key binding to cycle `GroupingMode` (account → role → flat → account), re-render account_list with new mode, preserve all selections across mode change, update status_bar to show current grouping mode
- [x] T031 [US3] Ensure filter + grouping interaction in `src/aws_pick/tui/widgets/account_list.py`: when both active, apply filter first then group filtered results, preserve selections across both filter and grouping changes simultaneously
- [x] T032 [US3] Update help screen in `src/aws_pick/tui/screens/help.py`: add `g: cycle grouping` to shortcut list
- [x] T033 [US3] Write unit tests in `tests/unit/test_selector.py`: test grouping by role (accounts with same role grouped together), test flat mode (alphabetical), test selection preservation across mode changes, test filter + grouping combined

**Checkpoint**: Grouping operational -- users can organize accounts by account, role, or flat view

---

## Phase 7: User Story 4 - Mark Favorites (Priority: P2)

**Goal**: Users can mark account/role pairs as favorites, which persist between sessions and appear in a dedicated top section

**Independent Test**: Mark items as favorites, relaunch TUI, verify favorites appear at top, test select-all-favorites shortcut

### Implementation for User Story 4

- [x] T034 [US4] Implement FavoritesManager in `src/aws_pick/core/favorites.py`: class with `list() -> list[Favorite]`, `add(account_id, role_name)`, `remove(account_id, role_name)`, `clear()`, `is_favorite(account_id, role_name) -> bool`, uses `JsonStore` to read/write `config.json` favorites section, handles missing/corrupt file gracefully
- [x] T035 [US4] Add favorites section to account_list widget in `src/aws_pick/tui/widgets/account_list.py`: render "Favorites" group at top when favorites exist, mark favorite items with star/pin visual indicator, handle stale favorites (account/role not in current input) as dimmed/inactive items
- [x] T036 [US4] Wire favorite key bindings in `src/aws_pick/tui/screens/selector.py`: `f` key toggles favorite on focused item (calls FavoritesManager.add/remove, re-renders), `F` key selects all favorites that exist in current input list
- [x] T037 [US4] Ensure favorites work with filter and grouping in `src/aws_pick/tui/widgets/account_list.py`: favorites section appears at top regardless of grouping mode, filtered favorites still appear in favorites section when matching filter
- [x] T038 [US4] Update help screen in `src/aws_pick/tui/screens/help.py`: add `f: toggle favorite` and `F: select all favorites` to shortcut list
- [x] T039 [US4] Write unit tests in `tests/unit/test_favorites.py`: test CRUD operations, test persistence (write then read), test is_favorite, test corrupt file handling, test stale favorite detection

**Checkpoint**: Favorites operational -- users can mark, persist, and quick-select favorite accounts

---

## Phase 8: User Story 6 - Library Integration (Priority: P2)

**Goal**: The package is importable as a library with a clean public API, supporting both interactive and non-interactive modes, with optional login handler

**Independent Test**: Import the library in a script, call select_accounts with mock data and interactive=False, verify returned SelectionResult

### Implementation for User Story 6

- [x] T040 [US6] Create public API exports in `src/aws_pick/__init__.py`: export `select_accounts`, `SelectionResult`, `LoginResult`, `BatchLoginResult`, `ItemLoginResult`, `manage_favorites`, `manage_presets`, set `__all__` and `__version__`
- [x] T041 [US6] Create `src/aws_pick/__main__.py`: import and call `main()` from `cli.app` for `python -m aws_pick` support
- [x] T042 [US6] Implement non-interactive selection path in `src/aws_pick/core/selector.py`: when `interactive=False`, parse `selections` list of "account_id:role_name" strings, match against input accounts, return `SelectionResult` with matched items, raise `InvalidSelectionError` for unmatched selections
- [x] T043 [US6] Implement login handler callback support in `src/aws_pick/core/selector.py`: when `on_login` is provided and `interactive=False`, invoke callback for each selected item, collect `LoginResult` from each, build `BatchLoginResult`, attach to `SelectionResult.login_results`
- [x] T044 [US6] Create `manage_favorites()` factory function in `src/aws_pick/core/favorites.py`: returns `FavoritesManager` with optional `config_dir` override
- [x] T045 [US6] Create `manage_presets()` factory function stub in `src/aws_pick/core/presets.py`: returns `PresetsManager` with optional `config_dir` override (full implementation in US8)
- [x] T046 [US6] Write library integration tests in `tests/integration/test_library_api.py`: test `select_accounts(interactive=False, selections=[...])`, test login handler callback invocation and result collection, test `manage_favorites()` CRUD, test invalid input raises ValueError, test public API exports match contract

**Checkpoint**: Library fully importable and functional for programmatic use

---

## Phase 9: User Story 9 - Visual Environment Indicators (Priority: P2)

**Goal**: Accounts display color-coded environment tags (prod=red, dev=green, staging=yellow) based on name patterns or explicit input tags

**Independent Test**: Provide accounts with "prod", "dev", "staging" in names, verify correct color indicators, test explicit tag override

### Implementation for User Story 9

- [x] T047 [US9] Implement environment classifier in `src/aws_pick/core/environment.py`: `classify(account: AwsAccount) -> EnvironmentPattern | None`, default patterns (prod/production → red, dev/develop/development → green, stg/staging/stage → yellow), explicit `environment` field on input takes precedence, case-insensitive substring matching, configurable patterns from config.json `environment_patterns` section
- [x] T048 [US9] Add environment indicators to account_list widget in `src/aws_pick/tui/widgets/account_list.py`: prepend color-coded tag (e.g., `[PROD]` in red, `[DEV]` in green, `[STG]` in yellow) to account items, neutral/no tag for unclassified accounts
- [x] T049 [US9] Add production confirmation warning in `src/aws_pick/tui/screens/selector.py`: on Enter, if any selected items have production classification, show confirmation modal "N production accounts selected. Continue? [Y/n]", only proceed if confirmed
- [x] T050 [US9] Write unit tests in `tests/unit/test_environment.py`: test default pattern matching (prod, dev, staging variants), test explicit tag precedence, test case-insensitive matching, test unclassified accounts, test custom patterns from config

**Checkpoint**: Environment indicators visible -- production accounts clearly identifiable at a glance

---

## Phase 10: User Story 10 - Live Progress Feedback During Batch Login (Priority: P2)

**Goal**: When login handler processes selections, TUI shows real-time per-item progress (spinner → checkmark/X) with summary on completion

**Independent Test**: Configure mock login handler with delays, confirm selections, verify live progress updates and final summary

### Implementation for User Story 10

- [x] T051 [US10] Implement batch login orchestration in `src/aws_pick/core/login.py`: `async process_batch(items: list[AccountRole], handler: Callable, on_progress: Callable)` processes items sequentially (or with configurable concurrency), invokes handler for each, calls on_progress callback with `ItemLoginResult` after each, handles Ctrl+C (complete in-flight, skip remaining), returns `BatchLoginResult`
- [x] T052 [US10] Create progress_item widget in `src/aws_pick/tui/widgets/progress_item.py`: displays account/role with status indicator (spinner while processing, checkmark on success, X on failure with error text), uses Textual's `LoadingIndicator` or Rich spinner
- [x] T053 [US10] Create progress screen in `src/aws_pick/tui/screens/progress.py`: Textual `Screen` with scrollable list of progress_item widgets (one per selected item), updates in real-time as items complete, shows summary footer (N/M complete, X failed), dismiss on completion with summary
- [x] T054 [US10] Integrate progress into selector flow in `src/aws_pick/tui/app.py`: when `on_login` is provided and user confirms selections, push progress screen instead of dismissing, pass handler and selections to progress screen, collect and return `BatchLoginResult`
- [x] T055 [US10] Write unit tests in `tests/unit/test_login.py`: test batch processing completes all items, test partial failure (some succeed, some fail), test cancellation mid-batch (in-flight completes, remaining skipped), test result aggregation (total/succeeded/failed counts)

**Checkpoint**: Batch login progress visible -- users see real-time status for each account

---

## Phase 11: User Story 5 - CLI Non-Interactive Mode (Priority: P3)

**Goal**: Users can run the tool as a CLI with `--select` arguments for scripted/automated use, receiving JSON output

**Independent Test**: Run CLI with `--select` args and `--json`, verify JSON output matches expected format and exit codes

### Implementation for User Story 5

- [x] T056 [US5] Create Typer app in `src/aws_pick/cli/app.py`: root `Typer()` app with `select`, `preset`, `favorites`, `history` command groups, `main()` function as entry point
- [x] T057 [US5] Implement select command in `src/aws_pick/cli/commands/select.py`: `--input`/`-i` option (file path or stdin), `--select`/`-s` option (multiple, "account_id:role_name"), `--preset`/`-p` option, `--favorites` flag, `--json` flag, `--output`/`-o` option, reads input JSON, calls `select_accounts()` with appropriate args, outputs JSON or launches TUI based on args, exit codes (0=success, 1=error, 2=cancelled, 3=invalid selection)
- [x] T058 [US5] Implement favorites CLI commands in `src/aws_pick/cli/commands/favorites.py`: `list`, `add ACCOUNT_ID ROLE_NAME`, `remove ACCOUNT_ID ROLE_NAME`, `clear` subcommands using FavoritesManager
- [x] T059 [US5] Implement stdin input parsing in `src/aws_pick/cli/commands/select.py`: detect piped input (`sys.stdin.isatty()`), read and parse JSON from stdin, handle parse errors with clear error message
- [x] T060 [US5] Write CLI integration tests in `tests/integration/test_cli.py`: test `select --input file.json --select id:role --json` returns correct JSON, test invalid selection exits with code 3, test stdin input parsing, test favorites CLI CRUD commands, test missing input file error

**Checkpoint**: CLI fully functional for scripted use and automation

---

## Phase 12: User Story 8 - Named Presets / Saved Selections (Priority: P3)

**Goal**: Users can save current selections as named presets, load them later, and manage presets via TUI and CLI

**Independent Test**: Save selection as preset "my-preset", clear selections, load "my-preset", verify items re-selected

### Implementation for User Story 8

- [x] T061 [US8] Implement PresetsManager in `src/aws_pick/core/presets.py`: `list() -> list[str]`, `get(name) -> Preset`, `save(name, items: list[Favorite])`, `delete(name)`, uses JsonStore config.json presets section, records created_at timestamp
- [x] T062 [US8] Create preset_save screen in `src/aws_pick/tui/screens/preset_save.py`: Textual `ModalScreen` with text input for preset name, save/cancel buttons, validates non-empty name, warns on overwrite of existing preset
- [x] T063 [US8] Create preset_load screen in `src/aws_pick/tui/screens/preset_load.py`: Textual `ModalScreen` listing available presets with item counts, select a preset to load, shows delete option, reports skipped items if preset references missing accounts
- [x] T064 [US8] Wire preset key bindings in `src/aws_pick/tui/screens/selector.py`: `s` key opens preset_save screen (passes current selections), `l` key opens preset_load screen (returns items to select), handle stale items on load (select valid, report skipped)
- [x] T065 [US8] Implement preset CLI commands in `src/aws_pick/cli/commands/preset.py`: `list`, `show NAME`, `delete NAME` subcommands using PresetsManager
- [x] T066 [US8] Update help screen in `src/aws_pick/tui/screens/help.py`: add `s: save preset` and `l: load preset` to shortcut list
- [x] T067 [US8] Write unit tests in `tests/unit/test_presets.py`: test CRUD operations, test persistence, test stale item handling on load, test overwrite warning, test preset with all stale items

**Checkpoint**: Presets operational -- users can save and recall named selections across sessions

---

## Phase 13: User Story 11 - Session History / Last-Used Indicator (Priority: P3)

**Goal**: TUI displays "last used" timestamp next to previously selected accounts, with history auto-pruned after 90 days

**Independent Test**: Select accounts, relaunch TUI, verify "2h ago" style indicators appear, verify 90-day pruning

### Implementation for User Story 11

- [x] T068 [US11] Implement HistoryManager in `src/aws_pick/core/history.py`: `record(items: list[AccountRole])` writes timestamps for each item, `get_last_used(account_id, role_name) -> str | None` returns ISO timestamp, `prune(retention_days=90)` removes old entries, uses JsonStore history.json, `prune()` called on init
- [x] T069 [US11] Add last-used indicators to account_list widget in `src/aws_pick/tui/widgets/account_list.py`: for items with history, append dimmed relative time text (e.g., "2h ago", "3d ago"), use `datetime` to compute relative time from ISO timestamp, no indicator for items without history
- [x] T070 [US11] Record selections on confirm in `src/aws_pick/tui/app.py`: after user confirms and selections are returned, call `HistoryManager.record()` with selected items
- [x] T071 [US11] Implement history CLI commands in `src/aws_pick/cli/commands/history.py`: `list` (shows recent entries, `--days N`, `--json`), `clear` subcommands using HistoryManager
- [x] T072 [US11] Write unit tests in `tests/unit/test_history.py`: test record and retrieval, test pruning (entries older than retention period removed), test relative time formatting, test stale history for missing accounts ignored, test concurrent sessions (no data loss)

**Checkpoint**: History operational -- users see when they last used each account

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Quality, consistency, and validation across all user stories

- [x] T073 Run full test suite and verify minimum 80% code coverage via `pytest --cov=aws_pick --cov-report=term-missing`
- [x] T074 [P] Run mypy strict type checking via `mypy src/` and fix all errors
- [x] T075 [P] Run Black + Ruff formatting/linting via `black src/ tests/` and `ruff check src/ tests/ --fix`
- [x] T076 Write API contract tests in `tests/contract/test_api_contract.py`: verify public API surface matches `contracts/library-api.md` (exported names, function signatures, dataclass fields)
- [x] T077 Validate quickstart.md scenarios end-to-end: run each example from quickstart.md (CLI with file input, non-interactive mode, library import) and verify expected behavior
- [x] T078 Cross-platform smoke test: verify `pip install -e .` and basic TUI launch on macOS (dev machine), document Windows/Linux test steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies -- start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion -- BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 -- MVP core TUI
- **US2 (Phase 4)**: Depends on Phase 3 (extends account_list widget)
- **US7 (Phase 5)**: Depends on Phase 3 (adds overlay to selector screen)
- **US3 (Phase 6)**: Depends on Phase 3 (extends account_list widget)
- **US4 (Phase 7)**: Depends on Phase 2 + Phase 3 (needs storage + TUI)
- **US6 (Phase 8)**: Depends on Phase 3 (wraps TUI in library API)
- **US9 (Phase 9)**: Depends on Phase 3 (extends account_list widget)
- **US10 (Phase 10)**: Depends on Phase 3 + US6 (needs TUI + login handler)
- **US5 (Phase 11)**: Depends on Phase 8/US6 (CLI wraps library API)
- **US8 (Phase 12)**: Depends on Phase 7/US4 (extends persistence pattern)
- **US11 (Phase 13)**: Depends on Phase 2 + Phase 3 (needs storage + TUI)
- **Polish (Phase 14)**: Depends on all desired phases being complete

### User Story Dependencies

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundational)
       ├─→ Phase 3 (US1: TUI Multi-Select) ← MVP
       │    ├─→ Phase 4 (US2: Search/Filter)
       │    ├─→ Phase 5 (US7: Help Overlay)
       │    ├─→ Phase 6 (US3: Grouping)
       │    ├─→ Phase 7 (US4: Favorites)
       │    ├─→ Phase 9 (US9: Environment Indicators)
       │    ├─→ Phase 13 (US11: History)
       │    └─→ Phase 8 (US6: Library API)
       │         ├─→ Phase 10 (US10: Batch Login Progress)
       │         └─→ Phase 11 (US5: CLI Mode)
       └─→ Phase 12 (US8: Presets) ← depends on US4 pattern
```

### Parallel Opportunities

After Phase 3 (US1) completes, these can run in parallel:
- US2 (filter) + US7 (help) + US3 (grouping) + US4 (favorites) + US9 (environment) + US11 (history)

After Phase 8 (US6) completes:
- US10 (progress) + US5 (CLI)

### Within Each Phase

- Models before services
- Core logic before TUI widgets
- Widgets before screens
- Screens before app integration
- Tests can be written alongside implementation

---

## Parallel Example: Post-MVP (After Phase 3)

```
# These can all run in parallel (different files, no conflicts):
Agent 1: "US2 - filter_bar widget in tui/widgets/filter_bar.py"
Agent 2: "US7 - help screen in tui/screens/help.py"
Agent 3: "US3 - grouping modes in tui/widgets/account_list.py"
Agent 4: "US4 - FavoritesManager in core/favorites.py"
Agent 5: "US9 - environment classifier in core/environment.py"
Agent 6: "US11 - HistoryManager in core/history.py"
```

Note: US3 and US4 both modify `account_list.py` so they should be sequenced, not parallelized.

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (TUI Multi-Select)
4. **STOP and VALIDATE**: Launch TUI with mock data, select items, verify return
5. Demo-ready MVP

### Incremental Delivery (Recommended)

1. Setup + Foundational → Foundation ready
2. US1 → Test independently → **MVP!**
3. US2 + US7 → Test independently → Core TUI complete (all P1 stories)
4. US3 + US4 + US6 + US9 → P2 stories → Full-featured TUI
5. US10 → Batch login with progress
6. US5 + US8 + US11 → P3 stories → CLI + power features
7. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US3 and US2 both modify account_list.py -- sequence them (US1 first, then US2 adds filter, then US3 adds grouping)
- US4 and US11 both add visual elements to account_list.py -- sequence after US3
- Total tasks: 78
