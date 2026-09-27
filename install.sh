#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Building latest distributions..."
python3 "$SCRIPT_DIR/tools/build.py"

# 1. Install CotEditor bundle
COT_SRC="$SCRIPT_DIR/dist/coteditor/TFQL.cotsyntax"
COT_STANDALONE="$HOME/Library/Application Support/CotEditor/Syntaxes"
COT_SANDBOX="$HOME/Library/Containers/com.coteditor.CotEditor/Data/Library/Application Support/CotEditor/Syntaxes"

echo "==> Installing to CotEditor..."
mkdir -p "$COT_STANDALONE"
cp -R "$COT_SRC" "$COT_STANDALONE/"
echo "  ✓ Installed to $COT_STANDALONE/TFQL.cotsyntax"

if [ -d "$HOME/Library/Containers/com.coteditor.CotEditor" ]; then
    mkdir -p "$COT_SANDBOX"
    cp -R "$COT_SRC" "$COT_SANDBOX/"
    echo "  ✓ Installed to $COT_SANDBOX/TFQL.cotsyntax"
fi

# 2. Install to Antigravity IDE and VS Code extensions
EXT_SRC="$SCRIPT_DIR/extensions/vscode-antigravity"
EXT_NAME="todoist-filter-query-language"

install_extension_target() {
    local target_dir="$1"
    if [ -d "$target_dir" ]; then
        local dest="$target_dir/$EXT_NAME"
        rm -rf "$dest"
        cp -R "$EXT_SRC" "$dest"
        echo "  ✓ Installed extension to $dest"
    fi
}

echo "==> Installing to Editor Extensions..."
install_extension_target "$HOME/.antigravity/extensions"
install_extension_target "$HOME/.vscode/extensions"
install_extension_target "$HOME/.cursor/extensions"

echo ""
echo "Installation complete!"
echo "• CotEditor: Ready. Supports .tfql, .tdq, .todoist files."
echo "• Antigravity IDE / VS Code: Extension active upon reload/restart."
