#!/bin/bash
# =============================================================================
# Generate all files from crawlers.yaml registry
#
# Usage: ./scripts/generate-all.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== GS Crawler - Generate All Files ==="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed"
    exit 1
fi

# Check for PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install pyyaml
fi

echo "1. Generating Docker Compose files..."
python3 scripts/generate-compose.py

echo ""
echo "2. Generating README.md tables..."
python3 scripts/generate-readme.py

echo ""
echo "=== All files generated! ==="
echo ""
echo "Generated files:"
echo "  - compose.yaml (production)"
echo "  - compose.dev.yaml (development)"
echo "  - README.md (crawler tables)"
echo ""
echo "To verify changes: git diff"
