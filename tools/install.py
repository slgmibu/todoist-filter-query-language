"""Cross-platform installer for Todoist Filter Query Language (TFQL).

Detects operating system (macOS, Linux, Windows) and installs grammar definitions
and formatting tools into all discovered editor extension and syntax directories:
- Antigravity IDE (Grammar & Auto-formatter)
- Visual Studio Code (Grammar & Auto-formatter)
- Cursor
- CotEditor (macOS only: Syntax Bundle & Script Menu Formatter)
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_target_directories() -> list[tuple[str, Path]]:
    """Resolve all potential editor syntax/extension directories based on host OS."""
    system = platform.system()
    home = Path.home()
    targets: list[tuple[str, Path]] = []

    # 1. Antigravity IDE & VS Code variants (Cross-platform)
    editor_dirs: list[tuple[str, Path]] = [
        ("Antigravity IDE", home / ".antigravity" / "extensions"),
        ("Antigravity IDE (Alt)", home / ".antigravity-ide" / "extensions"),
        ("VS Code", home / ".vscode" / "extensions"),
        ("Cursor", home / ".cursor" / "extensions"),
    ]

    for name, path in editor_dirs:
        if path.parent.exists():
            targets.append((name, path))

    # 2. CotEditor (macOS specific)
    if system == "Darwin":
        targets.extend([
            (
                "CotEditor (Standard)",
                home / "Library" / "Application Support" / "CotEditor" / "Syntaxes"
            ),
            (
                "CotEditor (Sandbox)",
                home / "Library" / "Containers" / "com.coteditor.CotEditor" / "Data" / "Library" / "Application Support" / "CotEditor" / "Syntaxes"
            ),
        ])

    return targets


def install() -> None:
    """Compile grammar and install to all discovered editor environments."""
    root = Path(__file__).resolve().parent.parent
    dist_dir = root / "dist"
    ext_dir = root / "extensions" / "vscode-antigravity"
    ext_name = "todoist-filter-query-language"

    print(f"Detected OS: {platform.system()} ({platform.release()})")
    print("==> Building latest distributions...")

    # Run compiler
    build_script = root / "tools" / "build.py"
    subprocess.run([sys.executable, str(build_script)], check=True)

    targets = get_target_directories()
    installed_count = 0

    print("\n==> Deploying to detected editors:")
    for name, target_path in targets:
        try:
            if "CotEditor" in name:
                cot_bundle = dist_dir / "coteditor" / "TFQL.cotsyntax"
                cot_script = dist_dir / "coteditor" / "Format TFQL.py"
                if cot_bundle.exists() and (target_path.parent.exists() or "Standard" in name):
                    target_path.mkdir(parents=True, exist_ok=True)
                    dest = target_path / "TFQL.cotsyntax"
                    shutil.copytree(cot_bundle, dest, dirs_exist_ok=True)
                    print(f"  ✓ [{name}] Installed syntax: {dest}")
                    installed_count += 1

                    # Install ScriptMenu formatter
                    script_menu_dir = target_path.parent / "ScriptMenu"
                    if script_menu_dir.parent.exists() or "Standard" in name:
                        script_menu_dir.mkdir(parents=True, exist_ok=True)
                        dest_script = script_menu_dir / "Format TFQL.py"
                        shutil.copy2(cot_script, dest_script)
                        dest_script.chmod(0o755)
                        print(f"  ✓ [{name}] Installed formatter script: {dest_script}")
            else:
                target_path.mkdir(parents=True, exist_ok=True)
                dest = target_path / ext_name
                shutil.copytree(ext_dir, dest, dirs_exist_ok=True)
                print(f"  ✓ [{name}] Installed extension: {dest}")
                installed_count += 1
        except Exception as err:
            print(f"  ✗ [{name}] Skipped: {err}")

    print(f"\nDone! Installed to {installed_count} editor environment(s).")
    print("• Antigravity IDE / VS Code: Format Document (Shift+Option+F) active.")
    print("• CotEditor: Syntax bundle & Script menu formatter (Control+Option+F) active.")


if __name__ == "__main__":
    install()
