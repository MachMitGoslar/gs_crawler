#!/bin/bash
# Test all crawler configurations locally without Docker
# Usage: ./scripts/test-all-configs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Testing all crawler configurations..."
echo "========================================"

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

cd "$PROJECT_ROOT/base_images/generic_scraper"

# Track results
PASSED=0
FAILED=0
FAILED_CONFIGS=""

# Test all configs
for config_dir in "$PROJECT_ROOT/crawler_configs/simple" "$PROJECT_ROOT/crawler_configs/tschuessschule"; do
    if [ -d "$config_dir" ]; then
        for config in "$config_dir"/*.yaml; do
            if [ -f "$config" ]; then
                config_name=$(basename "$config" .yaml)
                echo ""
                echo "Testing: $config_name"
                echo "----------------------------------------"

                if OUTPUT_DIR="$OUTPUT_DIR" "$VENV_PATH/bin/python" scraper.py "$config" 2>&1; then
                    echo "PASSED: $config_name"
                    ((PASSED++))
                else
                    echo "FAILED: $config_name"
                    ((FAILED++))
                    FAILED_CONFIGS="$FAILED_CONFIGS $config_name"
                fi
            fi
        done
    fi
done

echo ""
echo "========================================"
echo "Test Results"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo "Failed configs:$FAILED_CONFIGS"
    exit 1
fi

echo ""
echo "Output files:"
ls -la "$OUTPUT_DIR"/*.json 2>/dev/null | head -20
