#!/usr/bin/env python3
# %%%{CotEditorXInput=SelectionOrAllText}%%%
# %%%{CotEditorXOutput=Discard}%%%
# %%%{CotEditorShortcut=^~C}%%%

"""CotEditor Script: Copy Query as Todoist One-Liner.

Converts the selected query (or entire document) into a clean, single-line format
with normalized whitespace, and copies it directly to macOS clipboard (pbcopy).
Shortcut: Control+Option+C
"""

import subprocess
import sys
from pathlib import Path

# Add project root to sys.path to reuse format_text
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from tools.formatter import format_text

def main() -> None:
    content = sys.stdin.read()
    one_liner = format_text(content, style="compact").strip()
    if one_liner:
        subprocess.run(["pbcopy"], input=one_liner.encode("utf-8"), check=True)
        # Post macOS notification
        apple_script = f'display notification "Ready to paste into Todoist" with title "TFQL One-Liner Copied"'
        subprocess.run(["osascript", "-e", apple_script])

if __name__ == "__main__":
    main()
