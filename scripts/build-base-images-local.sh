#!/bin/bash
# =============================================================================
# Build all base images locally (no registry push required)
# Usage: ./scripts/build-base-images-local.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 Building GS Crawler Base Images Locally..."
echo "=============================================="
echo ""

cd "$PROJECT_ROOT/base_images"

# Build each base image with local tag (matching what Dockerfiles expect)
build_local() {
    local name=$1
    local dir=$2

    if [ -d "$dir" ]; then
        echo "🏗️  Building $name..."
        docker build -t "ghcr.io/machmitgoslar/gs_crawler_$name:latest" "$dir"
        echo "✅ Built: ghcr.io/machmitgoslar/gs_crawler_$name:latest"
        echo ""
    else
        echo "⚠️  Directory not found: $dir (skipping)"
    fi
}

# Build all base images
build_local "python_basic_crawler" "python_basic_crawler"
build_local "python_selenium_crawler" "python_selenium_crawler"
build_local "php_basic_crawler" "php_basic_crawler"
build_local "flask_monitor" "flask_monitor"
build_local "generic_scraper" "generic_scraper"

echo "=============================================="
echo "🎉 All base images built successfully!"
echo ""
echo "Available local images:"
docker images | grep "ghcr.io/machmitgoslar/gs_crawler_" | head -10
echo ""
echo "Next steps:"
echo "  1. Run: docker compose -f compose.dev.yaml up -d"
echo "  2. Or:  ./scripts/dev.sh up"
