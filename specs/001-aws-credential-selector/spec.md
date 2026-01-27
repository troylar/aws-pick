# Feature Specification: AWS Credential Selector

**Feature Branch**: `001-aws-credential-selector`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "A CLI and TUI based Python library for managing AWS local credentials. Users authenticate via Ping with Active Directory, and an API returns a list of AWS accounts and roles they have access to. They can then generate temporary access keys/secrets for AWS to put into their config file. Currently a script, needs to be an elegant CLI/TUI tool that lets users select multiple accounts/roles at once, displays a gorgeous modern TUI, runs on Windows and Linux, takes an input of a list of accounts/roles, and upon selection returns the selected accounts and roles. Should be usable as a library plugged into existing tools."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Multiple AWS Accounts/Roles via TUI (Priority: P1)

A user has authenticated via their organization's Ping/AD system and has a list of AWS accounts and roles available to them. They launch the credential selector TUI, which displays all available accounts and roles in an interactive, searchable multi-select interface. The user selects the accounts/roles they need, confirms their selection, and the tool either returns the selected items or triggers login/credential generation for all selected accounts simultaneously (if a login handler is configured).

**Why this priority**: This is the core value proposition -- replacing manual, one-at-a-time credential selection with an elegant multi-select interface that supports batch operations. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by providing a mock list of accounts/roles, launching the TUI, making selections, and verifying the correct selections are returned as structured data (or that the login handler is invoked for each selection).

**Acceptance Scenarios**:

1. **Given** a list of 20 accounts with 3 roles each, **When** the user launches the TUI, **Then** all accounts and roles are displayed in a navigable, organized list grouped by account.
2. **Given** the TUI is displayed, **When** the user selects 5 account/role combinations using keyboard navigation and space bar, **Then** a visual indicator (checkbox/highlight) shows which items are selected.
3. **Given** the user has made their selections, **When** they confirm (press Enter) with no login handler configured, **Then** the tool returns a structured list of the selected account/role pairs to the calling program.
4. **Given** the user has made their selections and a login handler is configured, **When** they confirm (press Enter), **Then** the tool invokes the login handler for each selected account/role pair and reports success/failure status for each.
5. **Given** the TUI is displayed, **When** the user presses a "select all" shortcut, **Then** all visible accounts/roles are selected.
6. **Given** the TUI is displayed, **When** the user presses a "deselect all" shortcut, **Then** all selections are cleared.

---

### User Story 2 - Search and Filter Accounts/Roles (Priority: P1)

A user has access to a large number of AWS accounts (50+) and needs to quickly find specific accounts or roles. They type a search query in the TUI filter bar to narrow the displayed list. The search matches against account name, account ID, and role name simultaneously, providing instant results as the user types.

**Why this priority**: For users with many accounts, search/filter is essential for practical usability. Without it, the multi-select TUI becomes unusable at scale.

**Independent Test**: Can be tested by providing a large list of accounts, typing filter text, and verifying only matching accounts/roles are displayed while preserving any prior selections.

**Acceptance Scenarios**:

1. **Given** a list of 100 accounts, **When** the user types "prod" in the filter bar, **Then** only accounts/roles containing "prod" in their account name, account ID, or role name are shown.
2. **Given** the user has selected 3 items and then applies a filter, **When** the filter hides some selected items, **Then** the previously selected items remain selected (not deselected by filtering).
3. **Given** the user has filtered the list, **When** they clear the filter, **Then** all accounts/roles reappear with existing selections preserved.
4. **Given** the user types "admin" in the filter bar, **When** only role names contain "admin", **Then** those roles and their parent accounts are shown.
5. **Given** the user types a 12-digit account ID, **When** the filter is applied, **Then** the matching account and all its roles are shown.

---

### User Story 3 - Configurable Grouping (Priority: P2)

A user wants to change how accounts and roles are organized in the TUI. By default, items are grouped by account (each account is a collapsible group containing its roles). The user can switch the grouping to organize by role name instead (grouping all accounts that share the same role name together), or view a flat ungrouped list. This is useful when looking for a specific role across many accounts.

**Why this priority**: Grouping flexibility is important for users who manage cross-account roles (e.g., "AdminAccess" across 30 accounts). It makes the TUI practical for different workflows beyond the default account-centric view.

**Independent Test**: Can be tested by providing accounts with overlapping role names, toggling grouping modes, and verifying items are reorganized correctly while preserving selections.

**Acceptance Scenarios**:

1. **Given** the TUI is displayed with the default "group by account" view, **When** the user presses a grouping toggle shortcut, **Then** the view switches to "group by role" and items are reorganized with role names as group headers.
2. **Given** the view is "group by role", **When** the user toggles again, **Then** the view switches to a flat ungrouped list sorted alphabetically.
3. **Given** the user has selected 5 items in "group by account" view, **When** they switch to "group by role" view, **Then** all 5 selections are preserved.
4. **Given** 10 accounts each have an "AdminAccess" role, **When** viewing in "group by role" mode, **Then** all 10 accounts appear under a single "AdminAccess" group header.

---

### User Story 4 - Mark Favorites (Priority: P2)

A user frequently selects the same set of accounts/roles. They can mark specific account/role combinations as favorites, which are persisted between sessions. Favorites appear at the top of the list (or in a dedicated favorites section) for quick access. The user can also select all favorites at once with a shortcut.

**Why this priority**: Favorites eliminate repetitive navigation for the most common selections. For users who log into the same 5-10 accounts daily, this dramatically reduces time spent in the selector.

**Independent Test**: Can be tested by marking items as favorites, closing and reopening the TUI, and verifying favorites persist and appear prominently. Also test the "select all favorites" shortcut.

**Acceptance Scenarios**:

1. **Given** the TUI is displayed, **When** the user presses a "toggle favorite" shortcut on an account/role, **Then** a visual indicator (star/pin) marks it as a favorite.
2. **Given** favorites have been set in a previous session, **When** the user launches the TUI again, **Then** favorites appear in a dedicated "Favorites" section at the top of the list.
3. **Given** the user has 5 favorites, **When** they press a "select all favorites" shortcut, **Then** all 5 favorite account/role pairs are selected.
4. **Given** an item is marked as a favorite, **When** the user presses the "toggle favorite" shortcut again, **Then** the favorite is removed and the item returns to its normal position.
5. **Given** favorites exist and a filter is active, **When** favorites match the filter, **Then** they still appear in the favorites section at the top of the filtered results.

---

### User Story 5 - CLI Non-Interactive Mode (Priority: P3)

A user wants to integrate the credential selector into a script or automation pipeline. Instead of launching the TUI, they pass account/role selections as command-line arguments and receive the selected items as structured output (JSON) without any interactive prompts.

**Why this priority**: Non-interactive mode enables automation and scripting, which is important for power users, but the primary use case is the interactive TUI.

**Independent Test**: Can be tested by invoking the tool with CLI arguments specifying account IDs and role names, and verifying the output matches the expected JSON structure.

**Acceptance Scenarios**:

1. **Given** a list of available accounts/roles provided as input, **When** the user runs the CLI with `--select account-id:role-name account-id2:role-name2`, **Then** the tool returns those selections as JSON without launching the TUI.
2. **Given** the user specifies an account/role that is not in the available list, **When** the command runs, **Then** the tool reports an error indicating the invalid selection.
3. **Given** the user provides no selection arguments and no TUI flag, **When** the command runs, **Then** the tool defaults to launching the TUI.

---

### User Story 6 - Library Integration (Priority: P2)

A developer wants to embed the credential selector into their existing Python-based credential management tool. They import the library, pass a list of account/role objects, and either launch the TUI programmatically or use the selection logic non-interactively. The library optionally accepts a login handler callback that is invoked for each selected account/role pair upon confirmation.

**Why this priority**: Library usage is a stated requirement and enables the tool to be plugged into existing infrastructure tooling, making it more widely useful.

**Independent Test**: Can be tested by importing the library in a Python script, passing a list of account/role dicts, calling the selector function, and verifying it returns the expected selections.

**Acceptance Scenarios**:

1. **Given** a Python script imports the library, **When** the developer calls the selector function with a list of account/role dicts, **Then** the TUI launches and returns the selected items as a Python list of dicts.
2. **Given** the library is called with a `interactive=False` flag and explicit selections, **When** the function executes, **Then** it returns the matching items without launching any TUI.
3. **Given** the library is called with an empty list of accounts, **When** the function executes, **Then** it returns an empty list and displays a message indicating no accounts are available.
4. **Given** the library is called with a login handler callback, **When** the user confirms selections in the TUI, **Then** the handler is invoked for each selected account/role pair and results (success/failure per item) are returned.

---

### User Story 7 - Keyboard Shortcut Help Overlay (Priority: P1)

A first-time user launches the TUI and is unsure which keyboard shortcuts are available. They press `?` to display a help overlay that lists all available shortcuts (select, deselect all, toggle favorite, switch grouping, select favorites, filter, confirm, cancel). The overlay dismisses when the user presses any key or `?` again.

**Why this priority**: The TUI has many keyboard-driven features. Without discoverability, users will miss key functionality and the 95% first-time success rate (SC-003) is unachievable.

**Independent Test**: Can be tested by launching the TUI and pressing `?`, verifying all shortcuts are listed, and pressing a key to dismiss the overlay.

**Acceptance Scenarios**:

1. **Given** the TUI is displayed, **When** the user presses `?`, **Then** a help overlay appears listing all available keyboard shortcuts with descriptions.
2. **Given** the help overlay is displayed, **When** the user presses any key, **Then** the overlay dismisses and the TUI returns to its normal state.
3. **Given** the TUI is displayed, **When** the user has not pressed `?`, **Then** a subtle hint (e.g., "Press ? for help") is visible in the status bar or footer.

---

### User Story 8 - Named Presets / Saved Selections (Priority: P3)

A user has distinct sets of accounts they use for different workflows (e.g., "daily dev accounts," "prod incident response," "audit accounts"). They can save their current selection as a named preset, and later recall a preset to instantly select those accounts/roles. Presets are persisted between sessions alongside favorites.

**Why this priority**: Presets go beyond favorites by supporting multiple named groups. This is a power-user feature that significantly speeds up repeated workflows but is not required for basic usage.

**Independent Test**: Can be tested by selecting items, saving as a named preset, clearing selections, recalling the preset, and verifying the correct items are re-selected.

**Acceptance Scenarios**:

1. **Given** the user has selected 8 account/role pairs, **When** they invoke a "save preset" action and enter a name (e.g., "dev-accounts"), **Then** the preset is saved and persisted.
2. **Given** a preset named "dev-accounts" exists, **When** the user invokes a "load preset" action and selects "dev-accounts", **Then** all 8 account/role pairs from the preset are selected.
3. **Given** a preset references account/role pairs that no longer exist in the input list, **When** the preset is loaded, **Then** only the still-valid pairs are selected and a message indicates which items were skipped.
4. **Given** multiple presets exist, **When** the user invokes "load preset", **Then** a list of available presets is shown with their names and item counts.
5. **Given** a preset exists, **When** the user invokes a "delete preset" action, **Then** the preset is removed from storage.

---

### User Story 9 - Visual Environment Indicators (Priority: P2)

A user wants to quickly distinguish production accounts from development and staging accounts to avoid accidental credential generation for sensitive environments. The TUI displays color-coded indicators or tags next to accounts based on environment classification. The classification can be driven by pattern matching on account names (e.g., names containing "prod" are red) or by explicit tags provided in the input data.

**Why this priority**: Accidental production access is a real risk in organizations with many accounts. Visual differentiation provides a safety net and improves scanning speed.

**Independent Test**: Can be tested by providing accounts with names containing "prod", "dev", and "staging", and verifying the correct color indicators appear. Also test with explicitly tagged input data.

**Acceptance Scenarios**:

1. **Given** an account named "my-app-prod" is in the list, **When** the TUI renders it, **Then** it displays with a red/warning color indicator or a "PROD" tag.
2. **Given** an account named "my-app-dev" is in the list, **When** the TUI renders it, **Then** it displays with a green/safe color indicator or a "DEV" tag.
3. **Given** input data includes an explicit `environment` tag (e.g., "production"), **When** the TUI renders it, **Then** the explicit tag takes precedence over pattern matching.
4. **Given** an account name does not match any known pattern and has no explicit tag, **When** the TUI renders it, **Then** it displays with a neutral/default indicator.
5. **Given** the user is about to confirm selections that include production-tagged accounts, **When** they press Enter, **Then** a confirmation prompt warns them that N production accounts are included.

---

### User Story 10 - Live Progress Feedback During Batch Login (Priority: P2)

When a login handler is configured and the user confirms selections, the TUI displays real-time progress as each account/role pair is processed. Each item shows a spinner while in progress, a checkmark on success, or an error indicator on failure. A summary is displayed when all items are processed.

**Why this priority**: Without progress feedback, users processing 10+ accounts have no visibility into what's happening and whether the tool is stuck. This is essential UX for the batch login feature.

**Independent Test**: Can be tested by configuring a mock login handler with artificial delays, confirming selections, and verifying the progress indicators update in real-time.

**Acceptance Scenarios**:

1. **Given** the user confirms 10 selections with a login handler configured, **When** processing begins, **Then** each item shows a spinner/in-progress indicator.
2. **Given** an item's login handler completes successfully, **When** the status updates, **Then** the spinner is replaced with a checkmark and the item is marked as done.
3. **Given** an item's login handler fails, **When** the status updates, **Then** the spinner is replaced with an error indicator and a brief error message is shown.
4. **Given** all items have been processed, **When** the summary is displayed, **Then** it shows total count, successful count, and failed count with details for failures.
5. **Given** processing is in progress, **When** the user presses Ctrl+C, **Then** in-flight operations complete but no new ones are started, and a partial summary is shown.

---

### User Story 11 - Session History / Last-Used Indicator (Priority: P3)

A user wants to see which accounts they recently selected to avoid re-logging into accounts they already have active credentials for. The TUI displays a "last used" timestamp or relative time (e.g., "2h ago") next to account/role pairs that were selected in recent sessions. History is persisted locally.

**Why this priority**: This prevents redundant credential generation and helps users track which accounts are likely still active. Useful but not essential for core functionality.

**Independent Test**: Can be tested by selecting accounts, closing the TUI, reopening it, and verifying "last used" indicators appear on previously selected items.

**Acceptance Scenarios**:

1. **Given** the user selected "account-A / AdminRole" in a previous session 2 hours ago, **When** the TUI launches again, **Then** "account-A / AdminRole" displays a "2h ago" indicator.
2. **Given** the user has never selected an account/role pair, **When** the TUI displays it, **Then** no last-used indicator is shown.
3. **Given** history exists for items that are no longer in the input list, **When** the TUI launches, **Then** the stale history entries are silently ignored (not displayed).
4. **Given** the user selects items and confirms, **When** the session completes, **Then** the current timestamp is recorded for each selected item.

---

### Edge Cases

- What happens when the account/role list is empty? The TUI displays a clear "No accounts available" message and exits gracefully.
- What happens when the terminal does not support the TUI (e.g., piped output, non-interactive shell)? The tool detects the non-interactive environment and falls back to CLI mode or exits with a helpful error message.
- What happens when the terminal window is very small? The TUI adapts to small terminal sizes, showing scrollable content with a minimum usable size of 80x24.
- How does the tool handle duplicate account/role entries in the input? Duplicates are deduplicated by account ID + role name combination.
- What happens when the user cancels (Ctrl+C / Escape)? The tool exits cleanly, returning an empty selection to the caller (not an error).
- What happens when the favorites file is corrupted or inaccessible? The tool logs a warning and proceeds without favorites, treating the session as if no favorites exist.
- What happens when a favorited account/role no longer appears in the input list? The favorite is displayed as inactive/dimmed and cannot be selected, or is hidden with a note that N favorites are no longer available.
- What happens when the login handler fails for some but not all selections? The tool reports per-item success/failure status, does not abort remaining items, and returns the full results summary.
- What happens when grouping is changed while a filter is active? The filtered results are re-grouped under the new grouping mode, preserving both the filter and selections.
- What happens when the help overlay is shown while a filter is active? The filter remains active and the overlay appears on top; dismissing the overlay returns to the filtered view.
- What happens when a preset contains 50 items but only 30 are in the current input list? The 30 valid items are selected and a message indicates "20 items from this preset are no longer available."
- What happens when environment pattern matching conflicts with an explicit tag? The explicit tag always takes precedence.
- What happens when the history/last-used data file grows very large? History is capped at a configurable maximum (default: 90 days), and entries older than the cap are pruned on startup.
- What happens when batch login is interrupted (Ctrl+C) mid-processing? In-flight operations complete, no new ones start, and a partial summary is returned showing completed/skipped items.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a list of AWS accounts and roles as input, where each entry contains at minimum an account ID, account name, and role name.
- **FR-002**: System MUST display an interactive TUI that renders account/role options in a visually organized, grouped layout (default: grouped by account).
- **FR-003**: Users MUST be able to select and deselect individual account/role combinations using keyboard navigation (arrow keys + space bar).
- **FR-004**: Users MUST be able to select all or deselect all visible items with a keyboard shortcut.
- **FR-005**: System MUST support real-time text filtering/search to narrow the displayed list by account name, account ID, or role name simultaneously.
- **FR-006**: System MUST preserve selections when filters are applied, cleared, or grouping is changed.
- **FR-007**: System MUST return selected items as a structured data format (list of dicts in library mode, JSON in CLI mode) upon confirmation.
- **FR-008**: System MUST support a non-interactive CLI mode where selections are passed as arguments.
- **FR-009**: System MUST be importable as a Python library with a public API for programmatic use.
- **FR-010**: System MUST run on Windows, Linux, and macOS without platform-specific workarounds required by the user.
- **FR-011**: System MUST handle user cancellation (Ctrl+C, Escape) gracefully, returning an empty selection without crashing.
- **FR-012**: System MUST display the count of currently selected items in the TUI.
- **FR-013**: System MUST deduplicate input entries by account ID + role name combination.
- **FR-014**: System MUST support switching between grouping modes: by account (default), by role name, and flat/ungrouped. Grouping is toggled via a keyboard shortcut.
- **FR-015**: Users MUST be able to mark account/role combinations as favorites via a keyboard shortcut.
- **FR-016**: System MUST persist favorites between sessions in a local configuration file.
- **FR-017**: System MUST display favorites in a dedicated section at the top of the list, visually distinguished from non-favorites.
- **FR-018**: Users MUST be able to select all favorites at once with a dedicated keyboard shortcut.
- **FR-019**: System MUST optionally accept a login handler callback (in library mode) that is invoked for each selected account/role pair upon confirmation.
- **FR-020**: When a login handler is provided, the system MUST process all selections (not abort on individual failures) and report per-item success/failure status.
- **FR-021**: System MUST display a keyboard shortcut help overlay when the user presses `?`, listing all available shortcuts with descriptions.
- **FR-022**: System MUST show a persistent hint (e.g., "? for help") in the TUI footer/status bar to aid discoverability.
- **FR-023**: Users MUST be able to save the current selection as a named preset.
- **FR-024**: Users MUST be able to load a previously saved preset, which selects all matching account/role pairs from the preset.
- **FR-025**: Users MUST be able to delete a saved preset.
- **FR-026**: System MUST persist presets between sessions in the same local configuration as favorites.
- **FR-027**: When loading a preset, if some items no longer exist in the input list, the system MUST select only valid items and inform the user of skipped items.
- **FR-028**: System MUST display visual environment indicators (color-coding or tags) on accounts based on environment classification.
- **FR-029**: Environment classification MUST support both automatic pattern matching on account names and explicit tags provided in the input data. Explicit tags take precedence.
- **FR-030**: System MUST display a confirmation warning when the user is about to confirm selections that include production-tagged accounts.
- **FR-031**: When a login handler is processing selections, the system MUST display real-time per-item progress indicators (in-progress, success, failure) in the TUI.
- **FR-032**: When batch login completes, the system MUST display a summary showing total, successful, and failed counts with failure details.
- **FR-033**: System MUST record the timestamp of each selection and display a "last used" indicator next to previously selected account/role pairs.
- **FR-034**: Session history MUST be persisted locally and automatically pruned after a configurable retention period (default: 90 days).

### Key Entities

- **Account**: Represents an AWS account. Attributes: account ID (string, 12-digit), account name/alias (display string). An account can have multiple associated roles.
- **Role**: Represents an IAM role within an account. Attributes: role name (string). A role belongs to one account in the context of the selector.
- **Selection**: A pairing of one Account and one Role chosen by the user. The output of the tool is a collection of Selections.
- **Favorite**: A persisted Account + Role pairing that the user has marked for quick access. Stored locally and loaded on each TUI launch.
- **LoginResult**: The outcome of invoking the login handler for a single Selection. Attributes: the Selection, success/failure status, and an optional error message.
- **Preset**: A named, persisted collection of Account + Role pairings that can be recalled to quickly select a predefined set. Attributes: name (string), list of Account + Role pairings, creation date.
- **HistoryEntry**: A record of when an Account + Role pairing was last selected. Attributes: account ID, role name, timestamp. Used to display "last used" indicators.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select credentials for 5 accounts from a list of 50+ in under 30 seconds using the TUI (compared to the current script-based approach).
- **SC-002**: Returning users with favorites configured can select and confirm their daily accounts in under 5 seconds.
- **SC-003**: 95% of users can successfully complete their first credential selection without documentation, relying on the TUI's visual cues and keyboard hints.
- **SC-004**: The tool runs identically on Windows, Linux, and macOS with no platform-specific configuration required by the user.
- **SC-005**: Library integration requires no more than 5 lines of code to display the selector and receive results (10 lines with a login handler).
- **SC-006**: The TUI remains responsive (renders in under 200ms) with account lists of up to 500 entries.
- **SC-007**: Users can find a specific account/role from a list of 200+ entries in under 10 seconds using the search/filter.
- **SC-008**: Users can identify all production accounts at a glance without reading individual account names.
- **SC-009**: Users can save and recall a preset of 10 accounts in under 10 seconds.
- **SC-010**: During batch login of 10+ accounts, users can see real-time progress for each item without waiting for the entire batch to complete.

## Assumptions

- The calling tool/script handles authentication (Ping/AD) by default. This tool is responsible for the selection UI and optionally orchestrating login via a caller-provided handler.
- The input format is a list of account/role objects. The specific schema will be a list of dicts with `account_id`, `account_name`, and `role_name` fields at minimum.
- Users have a terminal that supports basic ANSI escape codes (true for all modern terminals on Windows 10+, Linux, and macOS).
- The tool persists favorites, presets, and session history locally (no credentials or secrets are ever stored). All persisted data is stored in a platform-appropriate user config directory.
- The login handler callback, when provided, is responsible for the actual credential generation logic. The tool only invokes it and reports results.
- Default environment pattern matching uses common conventions: "prod" = production (red), "dev" = development (green), "staging"/"stg" = staging (yellow). These defaults can be overridden via configuration or explicit input tags.
- The input data schema optionally supports an `environment` field for explicit environment tagging. If not provided, pattern matching on `account_name` is used.
