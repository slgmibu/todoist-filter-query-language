"""Unit tests for Todoist Filter Query Language (TFQL) Formatter."""

import pytest
from tools.formatter import format_text, to_one_liner, parse_expr_tokens, parse_tree


def test_idempotency_expanded_format() -> None:
    """Formatting an already formatted multi-line query must produce identical output."""
    raw = (
        "#Inbox | (((today & no time) | due before: +1 hours | overdue) & "
        "!(#Laundry & !/Backlog) & !#Snoozed & !(#Work & p4 & !/Daily+))"
    )
    first_pass = format_text(raw, style="expanded")
    second_pass = format_text(first_pass, style="expanded")
    third_pass = format_text(second_pass, style="expanded")

    assert first_pass == second_pass
    assert second_pass == third_pass


def test_idempotency_compact_format() -> None:
    """Formatting into compact style must be idempotent."""
    raw = (
        "#Inbox\n"
        "| (\n"
        "    (\n"
        "        (today & no time)\n"
        "        | due before: +1 hours\n"
        "        | overdue\n"
        "    )\n"
        "    & !(#Laundry & !/Backlog)\n"
        "    & !#Snoozed\n"
        "    & !(#Work & p4 & !/Daily+)\n"
        ")"
    )
    first_pass = format_text(raw, style="compact")
    second_pass = format_text(first_pass, style="compact")

    expected = (
        "#Inbox | (((today & no time) | due before: +1 hours | overdue) & "
        "!(#Laundry & !/Backlog) & !#Snoozed & !(#Work & p4 & !/Daily+))"
    )
    assert first_pass.strip() == expected
    assert second_pass.strip() == expected


def test_parentheses_integrity_no_shifting() -> None:
    """Ensure multi-line formatting does NOT produce spurious empty parens like | () or ().\n"""
    formatted_block = (
        "#Inbox\n"
        "| (\n"
        "    (\n"
        "        (today & no time)\n"
        "        | due before: +1 hours\n"
        "        | overdue\n"
        "    )\n"
        "    & !(#Laundry & !/Backlog)\n"
        "    & !#Snoozed\n"
        "    & !(#Work & p4 & !/Daily+)\n"
        ")\n"
    )
    reformatted = format_text(formatted_block, style="expanded")
    assert "| ()" not in reformatted
    assert "()\n" not in reformatted
    assert reformatted.strip() == formatted_block.strip()


def test_to_one_liner_whitespace() -> None:
    """Verify one-liner normalizes all operators and parentheses without missing spaces."""
    expanded = (
        "#Inbox\n"
        "| (\n"
        "    (today | overdue)\n"
        "    & !(#Laundry & !/Backlog)\n"
        "    & !#Snoozed\n"
        "    & !(#Work & p4 & !/Daily+)\n"
        ")"
    )
    one_liner = to_one_liner(expanded)
    expected = (
        "#Inbox | ((today | overdue) & !(#Laundry & !/Backlog) & "
        "!#Snoozed & !(#Work & p4 & !/Daily+))"
    )
    assert one_liner == expected
    # Ensure no collapsed "#Inbox|"
    assert "#Inbox|" not in one_liner
    assert "#Inbox |" in one_liner


def test_unindented_leading_operators_continuation() -> None:
    """Continuation lines starting with & or | must aggregate properly even at column 0."""
    query = (
        "#Snoozed\n"
        "| (today & due after: +1 hours & !no time)"
    )
    formatted = format_text(query, style="compact").strip()
    assert formatted == "#Snoozed | (today & due after: +1 hours & !no time)"

    multi_continuation = (
        "14 days\n"
        "& !/daily+\n"
        "& !(#Laundry & !/Buffering)\n"
        "& !today\n"
        "& !#Work"
    )
    formatted_multi = format_text(multi_continuation, style="compact").strip()
    assert formatted_multi == "14 days & !/daily+ & !(#Laundry & !/Buffering) & !today & !#Work"


def test_compound_multi_view_filters() -> None:
    """Top-level commas in multi-views split in expanded mode and join with comma in compact mode."""
    query = "today & overdue, p1 & no date, ##Work & /Urgent"
    expanded = format_text(query, style="expanded")
    expected_expanded = (
        "today & overdue,\n"
        "p1 & no date,\n"
        "##Work & /Urgent"
    )
    assert expanded.strip() == expected_expanded

    compact = format_text(expanded, style="compact")
    assert compact.strip() == "today & overdue, p1 & no date, ##Work & /Urgent"


def test_string_literals_and_escapes() -> None:
    """Quoted strings and escaped characters must not be split as operators."""
    query = 'search: "Tom & Jerry" & #One \\ & Two'
    formatted = format_text(query, style="expanded").strip()
    assert formatted == 'search: "Tom & Jerry" & #One \\ & Two'


def test_comments_and_blank_lines_preserved() -> None:
    """Comments and blank lines must remain intact during formatting."""
    doc = (
        "// Daily Dashboard\n"
        "#Inbox\n"
        "| (\n"
        "    (today | overdue)\n"
        "    & #Work\n"
        ")\n"
        "\n"
        "// Secondary View\n"
        "#Snoozed\n"
    )
    formatted = format_text(doc, style="expanded")
    assert "// Daily Dashboard" in formatted
    assert "// Secondary View" in formatted
    assert "\n\n" in formatted


def test_node_cross_engine_parity() -> None:
    """Verify JavaScript extension engine produces bitwise identical output to Python."""
    import subprocess
    py_out = subprocess.check_output(["python3", "tools/formatter.py", "test/example.tfql"]).decode("utf-8")
    node_out = subprocess.check_output([
        "node", "-e",
        "const fs = require('fs'); "
        "const { formatDocumentText } = require('./extensions/vscode-antigravity/extension.js'); "
        "process.stdout.write(formatDocumentText(fs.readFileSync('test/example.tfql', 'utf8'), 'expanded', 4));"
    ]).decode("utf-8")
    assert py_out == node_out

    py_compact = subprocess.check_output(["python3", "tools/formatter.py", "--style", "compact", "test/example.tfql"]).decode("utf-8")
    node_compact = subprocess.check_output([
        "node", "-e",
        "const fs = require('fs'); "
        "const { formatDocumentText } = require('./extensions/vscode-antigravity/extension.js'); "
        "process.stdout.write(formatDocumentText(fs.readFileSync('test/example.tfql', 'utf8'), 'compact', 4));"
    ]).decode("utf-8")
    assert py_compact == node_compact
