"""TFQL Build Compiler.

Compiles the master TextMate grammar (grammar/tfql.tmLanguage.json)
into editor-specific distribution bundles:
- Visual Studio Code / Antigravity IDE extension assets
- CotEditor syntax bundle (dist/coteditor/TFQL.cotsyntax)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


SCOPE_TO_COT_CATEGORY: dict[str, str] = {
    "keyword.control.predicate": "attributes",
    "entity.name.type.project": "types",
    "entity.name.section": "commands",
    "variable.other.label": "variables",
    "keyword.operator.logical": "keywords",
    "punctuation.separator.query": "keywords",
    "constant.numeric.priority": "numbers",
    "constant.numeric.duration": "numbers",
    "constant.numeric.date": "numbers",
    "constant.numeric.time": "numbers",
    "constant.numeric.integer": "numbers",
    "keyword.other.flag": "keywords",
    "constant.language.temporal": "values",
    "constant.language.target": "values",
    "string.quoted": "strings",
    "punctuation.section.parens": "characters",
    "comment.line": "comments",
}


def map_scope_to_category(scope: str) -> str:
    """Map a TextMate hierarchical scope name to a CotEditor highlight category."""
    for prefix, category in SCOPE_TO_COT_CATEGORY.items():
        if scope.startswith(prefix):
            return category
    return "keywords"


def build_coteditor_bundle(grammar: dict[str, Any], dist_dir: Path) -> None:
    """Generate the CotEditor .cotsyntax package bundle from TextMate grammar."""
    bundle_dir = dist_dir / "coteditor" / "TFQL.cotsyntax"
    regex_dir = bundle_dir / "Regex"
    regex_dir.mkdir(parents=True, exist_ok=True)

    # 1. Info.json
    info_payload = {
        "fileMap": {
            "extensions": ["tfql", "tdq", "todoist"]
        },
        "kind": "code",
        "metadata": {
            "author": "Antigravity",
            "description": "Syntax highlighting for Todoist Filter Query Language (TFQL)",
            "lastModified": "2026-09-27",
            "license": "MIT",
            "version": "1.1.0"
        }
    }
    (bundle_dir / "Info.json").write_text(json.dumps(info_payload, indent=2))

    # 2. Edit.json
    edit_payload = {
        "comment": {
            "blocks": [{"begin": "/*", "end": "*/"}],
            "inlines": [{"begin": "//"}]
        },
        "stringDelimiters": [
            {"begin": "\"", "end": "\"", "escapeCharacter": "\\"},
            {"begin": "'", "end": "'", "escapeCharacter": "\\"}
        ]
    }
    (bundle_dir / "Edit.json").write_text(json.dumps(edit_payload, indent=2))

    # 3. Completion.json
    completions: list[dict[str, str]] = [
        {"text": "assigned to:", "type": "attributes"},
        {"text": "assigned by:", "type": "attributes"},
        {"text": "added by:", "type": "attributes"},
        {"text": "due:", "type": "attributes"},
        {"text": "due before:", "type": "attributes"},
        {"text": "due after:", "type": "attributes"},
        {"text": "date:", "type": "attributes"},
        {"text": "date before:", "type": "attributes"},
        {"text": "date after:", "type": "attributes"},
        {"text": "created:", "type": "attributes"},
        {"text": "created before:", "type": "attributes"},
        {"text": "created after:", "type": "attributes"},
        {"text": "deadline:", "type": "attributes"},
        {"text": "deadline before:", "type": "attributes"},
        {"text": "deadline after:", "type": "attributes"},
        {"text": "workspace:", "type": "attributes"},
        {"text": "search:", "type": "attributes"},
        {"text": "today", "type": "values"},
        {"text": "tomorrow", "type": "values"},
        {"text": "yesterday", "type": "values"},
        {"text": "first day", "type": "values"},
        {"text": "overdue", "type": "keywords"},
        {"text": "od", "type": "keywords"},
        {"text": "recurring", "type": "keywords"},
        {"text": "subtask", "type": "keywords"},
        {"text": "uncompletable", "type": "keywords"},
        {"text": "shared", "type": "keywords"},
        {"text": "no date", "type": "keywords"},
        {"text": "no time", "type": "keywords"},
        {"text": "no deadline", "type": "keywords"},
        {"text": "no priority", "type": "keywords"},
        {"text": "no labels", "type": "variables"},
        {"text": "view all", "type": "keywords"},
        {"text": "p1", "type": "numbers"},
        {"text": "p2", "type": "numbers"},
        {"text": "p3", "type": "numbers"},
        {"text": "p4", "type": "numbers"}
    ]
    (bundle_dir / "Completion.json").write_text(json.dumps(completions, indent=2))

    # 4. Outlines.json
    outlines = [
        {
            "description": "Filter query group / section",
            "kind": "heading",
            "pattern": "^\\s*//\\s*(.+)$",
            "template": "$1"
        }
    ]
    (regex_dir / "Outlines.json").write_text(json.dumps(outlines, indent=2))

    # 5. Highlights.json
    highlights: dict[str, list[dict[str, Any]]] = {
        cat: [] for cat in [
            "attributes", "characters", "commands", "comments",
            "keywords", "numbers", "strings", "types", "values", "variables"
        ]
    }

    repo = grammar.get("repository", {})
    for section_name, section_data in repo.items():
        patterns = section_data.get("patterns", [])
        for entry in patterns:
            scope = entry.get("name", "")
            category = map_scope_to_category(scope)
            match_pattern = entry.get("match")
            begin_pattern = entry.get("begin")
            end_pattern = entry.get("end")

            rule: dict[str, Any] = {}
            if match_pattern:
                ignore_case = "(?i)" in match_pattern
                cleaned_pattern = match_pattern.replace("(?i)", "")
                rule = {
                    "begin": cleaned_pattern,
                    "description": scope,
                    "regularExpression": True
                }
                if ignore_case:
                    rule["ignoreCase"] = True
            elif begin_pattern and end_pattern:
                rule = {
                    "begin": begin_pattern,
                    "end": end_pattern,
                    "description": scope,
                    "regularExpression": True
                }

            if rule:
                highlights[category].append(rule)

    (regex_dir / "Highlights.json").write_text(json.dumps(highlights, indent=2))
    print(f"✓ CotEditor bundle built at: {bundle_dir}")


def sync_vscode_grammar(grammar_path: Path, ext_syntaxes_dir: Path) -> None:
    """Sync the canonical grammar into the VS Code / Antigravity extension."""
    ext_syntaxes_dir.mkdir(parents=True, exist_ok=True)
    target = ext_syntaxes_dir / "tfql.tmLanguage.json"
    target.write_text(grammar_path.read_text())
    print(f"✓ VS Code / Antigravity grammar synced to: {target}")


def main() -> None:
    """Entrypoint for compilation."""
    root = Path(__file__).resolve().parent.parent
    grammar_path = root / "grammar" / "tfql.tmLanguage.json"
    dist_dir = root / "dist"
    ext_syntaxes_dir = root / "extensions" / "vscode-antigravity" / "syntaxes"

    print(f"Loading grammar from {grammar_path}...")
    with open(grammar_path, "r", encoding="utf-8") as f:
        grammar = json.load(f)

    build_coteditor_bundle(grammar, dist_dir)
    sync_vscode_grammar(grammar_path, ext_syntaxes_dir)
    print("Build complete.")


if __name__ == "__main__":
    main()
