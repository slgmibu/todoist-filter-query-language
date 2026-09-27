#!/usr/bin/env python3
# %%%{CotEditorXInput=AllText}%%%
# %%%{CotEditorXOutput=ReplaceAllText}%%%
# %%%{CotEditorShortcut=^~F}%%%

"""CotEditor Script Menu Filter for Todoist Filter Query Language (TFQL).

Formats the active TFQL document on demand or via shortcut Control+Option+F.
"""

import re
import sys

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


def format_single_clause(clause: str) -> str:
    line = clause.strip()
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

    line = re.sub(r"(?<!\\)\s*([&|])\s*", r" \1 ", line)
    line = re.sub(r"!\s+", "!", line)
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)
    line = re.sub(r"([^\s!(])\(", r"\1 (", line)
    line = re.sub(r"\)([^\s),])", r") \1", line)
    line = re.sub(r"[ \t]{2,}", " ", line)
    return line.strip()


def split_top_level_commas(line: str) -> list[str]:
    clauses: list[str] = []
    current: list[str] = []
    paren_depth = 0
    in_quote = None
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


def format_text(text: str) -> str:
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
                formatted = format_single_clause(clause)
                output_lines.append(f"{formatted}," if i < len(clauses) - 1 else formatted)
        else:
            output_lines.append(format_single_clause(stripped))
    return "\n".join(output_lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    content = sys.stdin.read()
    sys.stdout.write(format_text(content))


if __name__ == "__main__":
    main()
