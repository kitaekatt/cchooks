#!/bin/bash
# Build and install cchooks to all required venvs
# Run after making changes to cchooks source

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CCHOOKS_ROOT="$(dirname "$SCRIPT_DIR")"

# Target venvs that need cchooks
VENVS=(
    "$HOME/.claude/.venv"
    "$HOME/Dev/kitaekatt-plugins/cchooks/.venv"
)

echo "Building cchooks..."
cd "$CCHOOKS_ROOT"
uv build

# Find the latest wheel
WHEEL=$(ls -t dist/*.whl 2>/dev/null | head -1)
if [[ -z "$WHEEL" ]]; then
    echo "Error: No wheel found in dist/"
    exit 1
fi
echo "Built: $WHEEL"

# Install to each venv
for VENV in "${VENVS[@]}"; do
    if [[ -d "$VENV" ]]; then
        SITE_PACKAGES="$VENV/lib/python3.12/site-packages"
        if [[ -d "$SITE_PACKAGES" ]]; then
            echo "Installing to $VENV..."
            uv pip install --force-reinstall "$WHEEL" --target "$SITE_PACKAGES"
        else
            echo "Warning: $SITE_PACKAGES not found, skipping"
        fi
    else
        echo "Warning: $VENV not found, skipping"
    fi
done

echo ""
echo "Done. Installed to ${#VENVS[@]} venv(s)."
echo "→ Restart Claude Code to use updated cchooks"
