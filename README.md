# Todoist Filter Query Language (TFQL)

Multi-editor syntax highlighting and language definition for **Todoist Filter Queries** (TFQL).

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

## Language Specifications

### Supported File Extensions
- `.tfql` (Todoist Filter Query Language)
- `.tdq` (Todoist Queries)
- `.todoist`

### Grammar Token Mapping

| Feature | TFQL Syntax | TextMate Scope | CotEditor Token |
| :--- | :--- | :--- | :--- |
| **Projects** | `#Work`, `##Personal`, `#"Client Alpha"` | `entity.name.type.project` | `types` |
| **Sections** | `/Inbox`, `/Current Sprint`, `/*` | `entity.name.section` | `commands` |
| **Labels** | `@urgent`, `@"follow up"`, `%email` | `variable.other.label` | `variables` |
| **Predicates** | `due:`, `due before:`, `created:`, `assigned to:`, `workspace:`, `search:` | `keyword.control.predicate` | `attributes` |
| **Logical Operators**| `&`, `\|`, `!`, `and`, `or`, `not` | `keyword.operator.logical` | `keywords` |
| **Compound Divider** | `,` | `punctuation.separator.query` | `keywords` |
| **Priorities** | `p1`..`p4`, `priority 1`..`4` | `constant.numeric.priority` | `numbers` |
| **Temporal Tokens** | `today`, `tomorrow`, `yesterday`, `next`, `past`, `mon`..`sun` | `constant.language.temporal` | `values` |
| **Offsets / Dates** | `+7d`, `-14d`, `2026-10-01` | `constant.numeric.date` | `numbers` |
| **Strings** | `"meeting notes"`, `'query'` | `string.quoted` | `strings` |
| **Comments** | `// Comment line`, `/* block */` | `comment.line`, `comment.block` | `comments` |

---

## Project Structure

```
todoist-filter-query-language/
├── grammar/
│   └── tfql.tmLanguage.json          # Master TextMate grammar (Single source of truth)
├── extensions/
│   └── vscode-antigravity/           # Antigravity IDE & VS Code extension package
│       ├── package.json
│       ├── language-configuration.json
│       └── syntaxes/
├── dist/
│   └── coteditor/
│       └── TFQL.cotsyntax/           # Compiled CotEditor bundle
├── tools/
│   ├── build.py                      # Compiler: TextMate grammar -> CotEditor bundle
│   └── install.py                    # Cross-platform installer engine (macOS, Linux, Windows)
├── test/
│   └── example.tfql                  # Test suite
├── install.sh                        # macOS / Linux installer
├── install.ps1                       # Windows PowerShell installer
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
- **macOS:** CotEditor (`~/Library/Application Support/CotEditor/Syntaxes`), Antigravity IDE, VS Code, Cursor.
- **Linux:** Antigravity IDE, VS Code, Cursor (`~/.<editor>/extensions`).
- **Windows:** Antigravity IDE, VS Code, Cursor (`%USERPROFILE%\.<editor>\extensions`).
