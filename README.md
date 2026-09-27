# Todoist Filter Query Language (TFQL)

Multi-editor syntax highlighting and language definition for **Todoist Filter Queries** (TFQL).

Cross-platform support for:
- **Antigravity IDE**
- **Visual Studio Code / Cursor**
- **CotEditor**
- **Sublime Text / TextMate**

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
│   └── build.py                      # Compiler: TextMate grammar -> CotEditor bundle
├── test/
│   └── example.tfql                  # Test suite
└── install.sh                        # Universal local installer
```

---

## Installation

Run the universal installer:
```bash
./install.sh
```

This compiles the latest grammar and deploys to:
1. CotEditor (`~/Library/Application Support/CotEditor/Syntaxes/TFQL.cotsyntax`)
2. Antigravity IDE (`~/.antigravity/extensions/todoist-filter-query-language`)
3. VS Code (`~/.vscode/extensions/todoist-filter-query-language`)
