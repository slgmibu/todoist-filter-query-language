#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use Python-based cross-platform installer if python3 is available
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/tools/install.py"
else
    echo "Python 3 is required to run the installer."
    exit 1
fi
