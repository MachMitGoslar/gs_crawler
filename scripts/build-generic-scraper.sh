#!/bin/bash
# Build the generic scraper base image locally
# Usage: ./scripts/build-generic-scraper.sh [tag]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TAG="${1:-latest}"
IMAGE_NAME="gs_crawler/generic_scraper:$TAG"

echo "Building generic scraper image..."
echo "Image: $IMAGE_NAME"
echo "----------------------------------------"

cd "$PROJECT_ROOT/base_images/generic_scraper"

# Build with BuildKit for cache mounts
DOCKER_BUILDKIT=1 docker build \
    --tag "$IMAGE_NAME" \
    --progress=plain \
    .

echo "----------------------------------------"
echo "Built: $IMAGE_NAME"
echo ""
echo "To test, run:"
echo "  docker run --rm -v \$PWD/crawler_configs:/app/configs -v \$PWD/test_output:/app/output $IMAGE_NAME"
