#!/bin/bash
# =============================================================================
# Test a single crawler locally without Docker
#
# Usage:
#   ./scripts/test-scraper-local.sh              # List available crawlers
#   ./scripts/test-scraper-local.sh 002_gz       # Test specific crawler
#   ./scripts/test-scraper-local.sh --config     # Test only config-driven
#   ./scripts/test-scraper-local.sh --custom     # Test only custom crawlers
#
# This script uses crawlers.yaml as the source of truth.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required"
    exit 1
fi

# Check for PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install --break-system-packages pyyaml 2>/dev/null || pip3 install pyyaml
fi

# Run the Python test script
exec python3 "$SCRIPT_DIR/test-crawler.py" "$@"
