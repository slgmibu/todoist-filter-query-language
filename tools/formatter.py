r"""TFQL Code Formatter.

Enforces an opinionated, clean coding style for Todoist Filter Query Language (TFQL):
- Normalized spacing around binary operators (&, |) and unary (!)
- Preserves escaped characters (e.g. #One \& Two)
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
    """Format an individual filter query clause."""
    line = clause.strip()
    if not line:
        return ""

    # 1. Normalize predicates (e.g. "due  :   today" -> "due: today")
    pred_regex = re.compile(
        r"(?i)\b(due(\s+(before|after|on))?|date(\s+(before|after|on))?|created(\s+(before|after|on))?|"
        r"added(\s+(before|after|on|by))?|deadline(\s+(before|after|on))?|completed(\s+(before|after|on))?|"
        r"assigned(\s+(to|by))?|workspace|search)\s*:\s*",
    )
    line = pred_regex.sub(lambda m: f"{' '.join(m.group(1).lower().split())}: ", line)

    # 2. Normalize priority tokens (e.g. "P1" -> "p1", "priority  1" -> "priority 1")
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

    # 5. Normalize operators: unary ! (no space after), binary & and | (1 space around, ignore escaped \&)
    line = re.sub(r"(?<!\\)\s*([&|])\s*", r" \1 ", line)
    line = re.sub(r"!\s+", "!", line)

    # 6. Normalize parentheses padding: "( query )" -> "(query)"
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)

    # Ensure space before opening parenthesis if preceded by word/symbol other than ! or (
    line = re.sub(r"([^\s!(])\(", r"\1 (", line)
    # Ensure space after closing parenthesis if followed by word/symbol other than ) or ,
    line = re.sub(r"\)([^\s),])", r") \1", line)

    # Collapse any incidental multiple spaces
    line = re.sub(r"[ \t]{2,}", " ", line)

    return line.strip()


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


def format_text(text: str) -> str:
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
                formatted = format_single_clause(clause)
                if i < len(clauses) - 1:
                    output_lines.append(f"{formatted},")
                else:
                    output_lines.append(formatted)
        else:
            output_lines.append(format_single_clause(stripped))

    return "\n".join(output_lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Opinionated code formatter for Todoist Filter Query Language (TFQL)")
    parser.add_argument("files", nargs="*", help="Files to format (reads stdin if omitted or '-')")
    parser.add_argument("-w", "--write", action="store_true", help="Write formatted output directly to files in-place")
    parser.add_argument("-c", "--check", action="store_true", help="Check formatting without modifying files (exits 1 if unformatted)")
    args = parser.parse_args()

    if not args.files or args.files == ["-"]:
        input_text = sys.stdin.read()
        formatted = format_text(input_text)
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
        formatted = format_text(original)

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
