#!/bin/bash
# Test a single scraper configuration locally without Docker
# Usage: ./scripts/test-scraper-local.sh <config_name>
# Example: ./scripts/test-scraper-local.sh 002_gz

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CONFIG_NAME="${1:-}"

if [ -z "$CONFIG_NAME" ]; then
    echo "Usage: $0 <config_name>"
    echo "Available configs:"
    ls -1 "$PROJECT_ROOT/crawler_configs/"*.yaml 2>/dev/null | xargs -n1 basename | sed 's/.yaml$//'
    exit 1
fi

CONFIG_PATH="$PROJECT_ROOT/crawler_configs/${CONFIG_NAME}.yaml"

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Config not found: $CONFIG_PATH"
    echo "Available configs:"
    ls -1 "$PROJECT_ROOT/crawler_configs/"*.yaml 2>/dev/null | xargs -n1 basename | sed 's/.yaml$//'
    exit 1
fi

# Create virtual environment if needed
VENV_PATH="$PROJECT_ROOT/base_images/generic_scraper/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install -r "$PROJECT_ROOT/base_images/generic_scraper/requirements.txt"
fi

# Create output directory
OUTPUT_DIR="$PROJECT_ROOT/test_output"
mkdir -p "$OUTPUT_DIR"

# Run the scraper
echo "Testing scraper: $CONFIG_NAME"
echo "Config: $CONFIG_PATH"
echo "Output: $OUTPUT_DIR"
echo "----------------------------------------"

cd "$PROJECT_ROOT/base_images/generic_scraper"
OUTPUT_DIR="$OUTPUT_DIR" "$VENV_PATH/bin/python" scraper.py "$CONFIG_PATH"

echo "----------------------------------------"
echo "Output files:"
ls -la "$OUTPUT_DIR"/*.json 2>/dev/null || echo "No output files generated"
