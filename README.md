# Todoist Filter Query Language (TFQL)

Multi-editor syntax highlighting and language definition for **Todoist Filter Queries** (TFQL).

Cross-platform support for:
- **Antigravity IDE** (macOS, Linux, Windows)
- **Visual Studio Code / Cursor** (macOS, Linux, Windows)
- **CotEditor** (macOS)
- **Sublime Text / TextMate** (macOS, Linux, Windows)

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
| **Labels** | `@urgent`, `@"follow up"`, `no label` | `variable.other.label` | `variables` |
| **Predicates** | `due:`, `due before:`, `created:`, `assigned to:`, `search:` | `keyword.control.predicate` | `attributes` |
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
