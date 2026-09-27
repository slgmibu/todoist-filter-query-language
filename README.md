# Todoist Filter Query Language (TFQL)

Multi-editor syntax highlighting and code formatting for **Todoist Filter Queries** (TFQL).

Cross-platform support for:
- **Antigravity IDE** (macOS, Linux, Windows)
- **Visual Studio Code / Cursor** (macOS, Linux, Windows)
- **CotEditor** (macOS)
- **Sublime Text / TextMate** (macOS, Linux, Windows)

---

## Color & Semantic Meaning

While exact color shades depend on your active editor theme (e.g., *Dark+*, *Monokai*, *GitHub Dark*, or CotEditor *Pulse*), TFQL systematically maps every element of a query to standard semantic grammar categories.

### Semantic Color Guide

| Category | Typical Dark Theme Color | Syntax Examples | What It Means in Todoist |
| :--- | :--- | :--- | :--- |
| **Projects & Hierarchies** | **Teal / Cyan / Bright Green** | `#Work`, `##Personal`, `#"Client Alpha"`, `#Welcome 👋` | Project and sub-project scope filters (`#` = project only, `##` = project + all sub-projects). |
| **Sections** | **Blue / Indigo** | `/Inbox`, `/Current Sprint`, `/*`, `/Sprint 🚀` | Section containers within projects. `/*` matches any section; `!/*` matches unsectioned tasks. |
| **Labels** | **Light Blue / Sky Blue** | `@urgent`, `@"follow up"`, `%email`, `%home*` | Task labels and tags (supports both `@` and `%` prefixes, plus wildcards). |
| **Predicates & Keys** | **Purple / Magenta / Lavender** | `due:`, `due before:`, `created:`, `assigned to:`, `workspace:`, `search:` | Query operators defining which task attribute to evaluate. |
| **Logical Operators** | **Pink / Red / Rose** | `&`, `\|`, `!`, `and`, `or`, `not` | Boolean algebra connecting conditions (`&` = AND, `\|` = OR, `!` = NOT). |
| **List Separator** | **Muted White / Grey** | `,` | Separates compound queries into distinct sections/lists within a single view. |
| **Priorities & Numbers** | **Light Green / Olive** | `p1`, `p2`, `p3`, `p4`, `priority 1`..`4`, `+7d`, `14 days`, `2026-10-01` | Priority levels, numeric durations, offsets, and calendar dates. |
| **Temporal Constants** | **Blue / Violet / Cyan** | `today`, `tomorrow`, `yesterday`, `mon`..`sun`, `jan`..`dec`, `first day` | Relative date words, weekdays, calendar months, and time units. |
| **Assignee Constants** | **Blue / Violet** | `me`, `others` | Built-in target identities used with `assigned to:` or `added by:`. |
| **Status Flags** | **Purple / Violet** | `shared`, `assigned`, `subtask`, `uncompletable`, `recurring`, `overdue`, `od`, `view all` | Built-in boolean status filters and task properties. |
| **Negative Flags** | **Purple / Orange** | `no date`, `no time`, `no due date`, `no deadline`, `no priority`, `no labels` | Explicit exclusions for missing attributes. |
| **Search Strings** | **Orange / Amber / Red-Brown** | `"quarterly review"`, `'deployment notes'` | Exact search phrases evaluated within task names and descriptions. |
| **Comments & Headers** | **Muted Grey / Forest Green** | `// Daily Dashboard`, `/* notes */` | Explanatory titles; single-line comments populate the editor's document outline. |

---

### Example Query Breakdown

```tfql
// Daily priority dashboard
(today | overdue) & #Work & /Sprint 🚀 & @urgent & p1,
 └────┬─────────┘   └─┬──┘   └───┬────┘   └──┬───┘  └┬┘ └┬┘
   Temporal        Project    Section      Label    Pri  Multi-view
   Constants       (types)   (commands) (variables)         Divider
```

---

## Code Formatting & Style Guide

TFQL includes an auto-formatter that cleans up whitespace, line breaks, casing, and compound views.

### Style Rules Enforced:
1. **Hierarchical 4-Space Tree Formatting (Leading Operators):** Complex nested parentheses are expanded into clear multi-line trees with 4 spaces per nesting level and leading operators (`&`, `|`). This prevents accidental vertical alignment of parentheses from different nesting levels:
   ```tfql
   // Complex nested query:
   #Inbox
   | (
       (
           (today & no time)
           | due before: +1 hours
           | overdue
       )
       & !(#Laundry & !/Backlog)
       & !#Snoozed
       & !(#Work & p4 & !/Daily+)
   )
   ```
2. **Multi-View Query Splitting:** Comma-separated multi-view filters are split across lines so each list is readable at a glance:
   ```tfql
   // Before:
   today & overdue, p1 & no date, ##Work & /Urgent

   // Formatted:
   today & overdue,
   p1 & no date,
   ##Work & /Urgent
   ```
2. **Normalized Operator Spacing:** Exactly one space around binary operators (`&`, `|`), and zero spaces after unary NOT (`!`):
   ```tfql
   (today | overdue) & #Work & !assigned
   ```
3. **Clean Parentheses:** No inner padding inside groupings (`(query)` instead of `( query )`).
4. **Predicate Colons:** Zero spaces before the colon, exactly one space after (`due: today`, `workspace: Doist`).
5. **Casing Normalization:** Standardizes keywords and priorities to lowercase (`p1`..`p4`, `today`, `overdue`, `recurring`).

---

### How to Format & Copy for Todoist

#### 1. In Antigravity IDE / VS Code / Cursor
- **Format Document (Expanded Tree):** Press **`Shift + Option + F`** (macOS) or **`Shift + Alt + F`** (Windows / Linux).
- **Copy as One-Liner for Todoist:** Press **`Cmd + Option + C`** (macOS) / **`Ctrl + Alt + C`** (Windows/Linux) or **Right-Click > "TFQL: Copy Query as One-Liner for Todoist"**.
  - Normalizes the active query into a single compact line with strict whitespace rules ready to paste directly into the Todoist filter UI.
- **Convert to One-Liners (In-Place):** Run **`TFQL: Convert Document to One-Liners (Compact)`** via `Cmd + Shift + P`.
- **Auto-format on save:** Add to `settings.json`:
  ```json
  "[tfql]": {
    "editor.formatOnSave": true
  }
  ```

#### 2. In CotEditor
- **Format Document (Expanded Tree):** Press **`Control + Option + F`** (or select **Script > Format TFQL**).
- **Copy as Todoist One-Liner:** Press **`Control + Option + C`** (or select **Script > Copy as Todoist One-Liner**).
  - Automatically pipes the clean one-liner to macOS clipboard (`pbcopy`) and posts a system notification.

#### 3. CLI (Terminal / Python)
```bash
# Format files in-place (expanded tree)
python3 tools/formatter.py -w query.tfql

# Convert to single-line compact format for Todoist
python3 tools/formatter.py --one-line query.tfql

# Convert to one-liner and copy directly to macOS clipboard
python3 tools/formatter.py --one-line --copy query.tfql

# Format from stdin (pipes / filters)
cat query.tfql | python3 tools/formatter.py

# Check formatting in CI (exits with 1 if unformatted)
python3 tools/formatter.py --check query.tfql
```

---

## Language Specifications

### Supported File Extensions
- `.tfql` (Todoist Filter Query Language)
- `.tdq` (Todoist Queries)
- `.todoist`

---

## Project Structure

```
todoist-filter-query-language/
├── grammar/
│   └── tfql.tmLanguage.json          # Canonical TextMate grammar (Single source of truth)
├── extensions/
│   └── vscode-antigravity/           # Antigravity IDE & VS Code extension package
│       ├── extension.js              # Formatting provider & clipboard one-liner commands
│       ├── package.json              # Extension manifest & command/keybinding definitions
│       ├── language-configuration.json # Brackets, comments, and auto-pairing rules
│       └── syntaxes/                 # Synced extension grammar
├── dist/
│   ├── todoist-filter-query-language-1.4.0.vsix # Packaged installable VSIX bundle
│   └── coteditor/
│       ├── TFQL.cotsyntax/           # Compiled CotEditor syntax definition package
│       ├── Format TFQL.py            # CotEditor multi-line tree formatter (^~F)
│       └── Copy as Todoist One-Liner.py # CotEditor clipboard one-liner exporter (^~C)
├── tools/
│   ├── build.py                      # Compiler: TextMate grammar -> CotEditor bundle & VSIX
│   ├── formatter.py                  # Core AST formatter engine, multi-line aggregator & CLI
│   └── install.py                    # Cross-platform installer (Antigravity IDE, VS Code, CotEditor)
├── tests/
│   └── test_formatter.py             # Pytest automated test suite (AST idempotency, Node parity)
├── test/
│   └── example.tfql                  # Specification test file (all official Todoist filter examples)
├── install.sh                        # macOS / Linux installer script
├── install.ps1                       # Windows PowerShell installer script
└── README.md
```

---

## Installation

The installer automatically detects your operating system and deploys to all installed editors.

### macOS & Linux
```bash
./install.sh
# or: python3 tools/install.py
```

### Windows (PowerShell)
```powershell
.\install.ps1
# or: python tools\install.py
```

### What gets deployed:
- **macOS:** CotEditor syntax bundle + Script Menu formatter (`~/Library/Application Support/CotEditor`), Antigravity IDE, VS Code, Cursor.
- **Linux:** Antigravity IDE, VS Code, Cursor (`~/.<editor>/extensions`).
- **Windows:** Antigravity IDE, VS Code, Cursor (`%USERPROFILE%\.<editor>\extensions`).
