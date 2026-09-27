#!/usr/bin/env python3
# %%%{CotEditorXInput=AllText}%%%
# %%%{CotEditorXOutput=ReplaceAllText}%%%
# %%%{CotEditorShortcut=^~F}%%%

"""CotEditor Script Menu Filter for Todoist Filter Query Language (TFQL).

Formats the active TFQL document on demand or via shortcut Control+Option+F:
- Hierarchical multi-line tree formatting for nested parentheses (4 spaces indent, leading operators)
- Normalized spacing around operators (&, |) and unary (!)
- Preserves escaped characters and string literals
"""

import re
import sys
from typing import Any

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
    line = atom.strip()
    if not line:
        return ""

    pred_regex = re.compile(
        r"(?i)\b(due(\s+(before|after|on))?|date(\s+(before|after|on))?|created(\s+(before|after|on))?|"
        r"added(\s+(before|after|on|by))?|deadline(\s+(before|after|on))?|completed(\s+(before|after|on))?|"
        r"assigned(\s+(to|by))?|workspace|search)\s*:\s*",
    )
    line = pred_regex.sub(lambda m: f"{' '.join(m.group(1).lower().split())}: ", line)
    line = re.sub(r"(?i)\b(p[1-4])\b", lambda m: m.group(1).lower(), line)
    line = re.sub(r"(?i)\bpriority\s*([1-4])\b", r"priority \1", line)
    line = re.sub(
        r"(?i)\bno\s+(date|time|due\s+date|deadline|priority|labels?)\b",
        lambda m: f"no {' '.join(m.group(1).lower().split())}",
        line
    )

    for kw in KEYWORDS_LOWERCASE:
        line = re.sub(rf"(?i)\b{re.escape(kw)}\b", kw, line)

    line = re.sub(r"!\s+", "!", line)
    line = re.sub(r"[ \t]{2,}", " ", line)
    return line.strip()


def parse_expr_tokens(s: str) -> list[tuple[str, str]]:
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
            j = i + 1
            while j < n and s[j].isspace():
                j += 1
            if j < n and s[j] == "(":
                tokens.append(("NOT_GROUP", "!"))
                i = j
                continue

        if s[i] == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue
        if s[i] == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

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
    if isinstance(item, tuple) and item[0] in ("(", "!("):
        return 1 + max((count_depth(x) for x in item[1]), default=0)
    return 0


def render_inline(elements: list[Any]) -> str:
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


def format_single_clause(clause: str, indent_size: int = 4) -> list[str]:
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

    if max_d >= 2 or (max_d >= 1 and len(inline_repr) > 60):
        return pretty_print_tree(tree, 0, indent_str)
    else:
        return [inline_repr]


def split_top_level_commas(line: str) -> list[str]:
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


def format_text(text: str, indent_size: int = 4) -> str:
    lines = text.splitlines()
    output_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            output_lines.append(stripped)
            continue
        clauses = split_top_level_commas(stripped)
        if len(clauses) > 1:
            for i, clause in enumerate(clauses):
                clause_lines = format_single_clause(clause, indent_size=indent_size)
                if i < len(clauses) - 1:
                    clause_lines[-1] = f"{clause_lines[-1]},"
                output_lines.extend(clause_lines)
        else:
            output_lines.extend(format_single_clause(stripped, indent_size=indent_size))
    return "\n".join(output_lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    content = sys.stdin.read()
    sys.stdout.write(format_text(content))


if __name__ == "__main__":
    main()
