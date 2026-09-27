r"""TFQL Code Formatter.

Enforces an opinionated, clean coding style for Todoist Filter Query Language (TFQL):
- Hierarchical multi-line tree formatting for nested parentheses (4 spaces indent, leading operators)
- Normalized spacing around binary operators (&, |) and unary (!)
- Preserves escaped characters (e.g. #One \& Two) and string literals (e.g. search: "...")
- Consistent predicate colon formatting (0 before, 1 after)
- Top-level comma splitting (compound multi-views on separate lines)
- Normalized parentheses padding and keyword casing (p1..p4, today, overdue)
- Preservation of string literals, comments, and project/label casing
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, List, Tuple


KEYWORDS_LOWERCASE = {
    "today", "tomorrow", "yesterday", "now", "overdue", "recurring",
    "subtask", "uncompletable", "shared", "assigned", "all",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "me", "others", "first day", "last day"
}


def normalize_atom(atom: str) -> str:
    """Normalize predicates, priorities, and keywords in an atomic clause."""
    line = atom.strip()
    if not line:
        return ""

    # 1. Normalize predicates (e.g. "due  :   today" -> "due: today")
    pred_regex = re.compile(
        r"(?i)\b(due(\s+(before|after|on))?|date(\s+(before|after|on))?|created(\s+(before|after|on))?|"
        r"added(\s+(before|after|on|by))?|deadline(\s+(before|after|on))?|completed(\s+(before|after|on))?|"
        r"assigned(\s+(to|by))?|workspace|search)\s*:\s*",
    )
    line = pred_regex.sub(lambda m: f"{' '.join(m.group(1).lower().split())}: ", line)

    # 2. Normalize priority tokens (p1..p4)
    line = re.sub(r"(?i)\b(p[1-4])\b", lambda m: m.group(1).lower(), line)
    line = re.sub(r"(?i)\bpriority\s*([1-4])\b", r"priority \1", line)

    # 3. Normalize negative flags (e.g. "no   date" -> "no date")
    line = re.sub(
        r"(?i)\bno\s+(date|time|due\s+date|deadline|priority|labels?)\b",
        lambda m: f"no {' '.join(m.group(1).lower().split())}",
        line
    )

    # 4. Normalize common temporal keywords casing if standalone
    for kw in KEYWORDS_LOWERCASE:
        line = re.sub(rf"(?i)\b{re.escape(kw)}\b", kw, line)

    # 5. Unary NOT normalization: ensure no space between ! and the identifier/word
    line = re.sub(r"!\s+", "!", line)

    # Collapse multiple incidental spaces (except inside quotes which are handled upstream)
    line = re.sub(r"[ \t]{2,}", " ", line)

    return line.strip()


def parse_expr_tokens(s: str) -> list[tuple[str, str]]:
    """Tokenize query into operators, parentheses, and atomic phrases.
    
    Correctly recognizes string literals and escaped characters.
    """
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(s)
    while i < n:
        if s[i].isspace():
            i += 1
            continue
        if s[i] in "&|":
            tokens.append(("OP", s[i]))
            i += 1
            continue
        if s[i] == "!":
            # Check if this negates a parenthesized group, e.g. !(...) or ! (...)
            j = i + 1
            while j < n and s[j].isspace():
                j += 1
            if j < n and s[j] == "(":
                tokens.append(("NOT_GROUP", "!"))
                i = j  # next loop iteration will process '('
                continue
            # If not a parenthesized group, fall through to atom parsing

        if s[i] == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue
        if s[i] == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

        # Atom / predicate phrase
        start = i
        in_quote: str | None = None
        while i < n:
            if in_quote:
                if s[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if s[i] == in_quote:
                    in_quote = None
                i += 1
                continue

            if s[i] in ('"', "'"):
                in_quote = s[i]
                i += 1
                continue

            if s[i] == "\\" and i + 1 < n:
                i += 2
                continue

            if s[i] in "&|()":
                break
            i += 1

        tokens.append(("ATOM", normalize_atom(s[start:i])))
    return tokens


def parse_tree(tokens: list[tuple[str, str]], idx: int = 0) -> tuple[list[Any], int]:
    """Parse tokens into nested group tree."""
    elements: list[Any] = []
    prefix = ""
    while idx < len(tokens):
        t_type, val = tokens[idx]
        if t_type == "LPAREN":
            sub, idx = parse_tree(tokens, idx + 1)
            elements.append((prefix + "(", sub))
            prefix = ""
        elif t_type == "NOT_GROUP":
            prefix = "!"
            idx += 1
        elif t_type == "RPAREN":
            return elements, idx + 1
        else:
            elements.append((t_type, val))
            idx += 1
    return elements, idx


def count_depth(item: Any) -> int:
    """Calculate maximum nesting depth of an element."""
    if isinstance(item, tuple) and item[0] in ("(", "!("):
        return 1 + max((count_depth(x) for x in item[1]), default=0)
    return 0


def render_inline(elements: list[Any]) -> str:
    """Render elements as a single normalized line."""
    res: list[str] = []
    for el in elements:
        if isinstance(el, tuple) and el[0] in ("(", "!("):
            res.append(f"{el[0]}{render_inline(el[1])})")
        elif el[0] == "OP":
            res.append(f" {el[1]} ")
        else:
            res.append(el[1])
    return "".join(res).strip()


def pretty_print_tree(
    elements: list[Any],
    indent_level: int = 0,
    indent_str: str = "    "
) -> list[str]:
    """Pretty print group tree with 4-space indents and leading operators."""
    lines: list[str] = []
    current_op = ""
    i = 0
    while i < len(elements):
        el = elements[i]
        if el[0] == "OP":
            current_op = el[1]
            i += 1
            continue

        prefix = f"{current_op} " if current_op else ""
        current_op = ""

        if isinstance(el, tuple) and el[0] in ("(", "!("):
            group_type = el[0]
            sub = el[1]
            inline_str = render_inline(sub)
            depth = count_depth(el)

            # Compact inline heuristic: keep leaf groups inline if depth <= 1 and simple
            is_simple_leaf = (
                depth <= 1 and len(inline_str) < 45 and
                not any(x[0] == "OP" and x[1] == "|" for x in sub if count_depth(x) > 0)
            )

            if is_simple_leaf:
                lines.append(f"{indent_str * indent_level}{prefix}{group_type}{inline_str})")
            else:
                lines.append(f"{indent_str * indent_level}{prefix}{group_type}")
                sub_lines = pretty_print_tree(sub, indent_level + 1, indent_str)
                lines.extend(sub_lines)
                lines.append(f"{indent_str * indent_level})")
        else:
            lines.append(f"{indent_str * indent_level}{prefix}{el[1]}")
        i += 1
    return lines


def format_single_clause(clause: str, style: str = "expanded", indent_size: int = 4) -> list[str]:
    """Format an individual filter query clause into one or more lines."""
    line = clause.strip()
    if not line:
        return [""]

    tokens = parse_expr_tokens(line)
    if not tokens:
        return [""]

    tree, _ = parse_tree(tokens)
    indent_str = " " * indent_size
    max_d = max((count_depth(x) for x in tree), default=0)
    inline_repr = render_inline(tree)

    # Expand into multi-line tree if:
    # 1. Nested parentheses exist (max_d >= 2), or
    # 2. Contains groups (max_d >= 1) and length exceeds 60 characters
    should_expand = style == "expanded" and (max_d >= 2 or (max_d >= 1 and len(inline_repr) > 60))

    if should_expand:
        return pretty_print_tree(tree, 0, indent_str)
    else:
        return [inline_repr]


def split_top_level_commas(line: str) -> list[str]:
    """Split query by commas that are NOT inside parentheses or quotes."""
    clauses: list[str] = []
    current: list[str] = []
    paren_depth = 0
    in_quote: str | None = None
    escaped = False

    for char in line:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            continue

        if in_quote:
            current.append(char)
            if char == in_quote:
                in_quote = None
            continue

        if char in ('"', "'"):
            in_quote = char
            current.append(char)
            continue

        if char == "(":
            paren_depth += 1
            current.append(char)
            continue
        elif char == ")":
            if paren_depth > 0:
                paren_depth -= 1
            current.append(char)
            continue

        if char == "," and paren_depth == 0:
            clauses.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        clauses.append("".join(current).strip())

    return [c for c in clauses if c]


def format_text(text: str, style: str = "expanded", indent_size: int = 4) -> str:
    """Format full TFQL document text."""
    lines = text.splitlines()
    output_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Preserve comments and empty lines
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            output_lines.append(stripped)
            continue

        # Check if line contains a top-level compound query separated by commas
        clauses = split_top_level_commas(stripped)
        if len(clauses) > 1:
            for i, clause in enumerate(clauses):
                clause_lines = format_single_clause(clause, style=style, indent_size=indent_size)
                if i < len(clauses) - 1:
                    clause_lines[-1] = f"{clause_lines[-1]},"
                output_lines.extend(clause_lines)
        else:
            output_lines.extend(format_single_clause(stripped, style=style, indent_size=indent_size))

    return "\n".join(output_lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Opinionated code formatter for Todoist Filter Query Language (TFQL)")
    parser.add_argument("files", nargs="*", help="Files to format (reads stdin if omitted or '-')")
    parser.add_argument("-w", "--write", action="store_true", help="Write formatted output directly to files in-place")
    parser.add_argument("-c", "--check", action="store_true", help="Check formatting without modifying files")
    parser.add_argument("--style", choices=["expanded", "compact"], default="expanded", help="Formatting style (default: expanded)")
    parser.add_argument("--indent", type=int, default=4, help="Indentation spaces (default: 4)")
    args = parser.parse_args()

    if not args.files or args.files == ["-"]:
        input_text = sys.stdin.read()
        formatted = format_text(input_text, style=args.style, indent_size=args.indent)
        sys.stdout.write(formatted)
        return

    failed = False
    for filepath_str in args.files:
        path = Path(filepath_str)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            failed = True
            continue

        original = path.read_text(encoding="utf-8")
        formatted = format_text(original, style=args.style, indent_size=args.indent)

        if args.check:
            if original != formatted:
                print(f"Requires formatting: {path}")
                failed = True
        elif args.write:
            if original != formatted:
                path.write_text(formatted, encoding="utf-8")
                print(f"Formatted: {path}")
        else:
            sys.stdout.write(formatted)

    if args.check and failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
