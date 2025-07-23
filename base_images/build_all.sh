#!/bin/bash

# Baut alle Base-Images für das GS Crawler System mit Docker Buildx

echo "🔧 Building GS Crawler Base Images with Docker Buildx..."
echo "======================================================"

# Basis-Pfad
BASE_DIR="."
version_number=${1:-"latest"}

# Ziel-Plattformen (Multi-Arch Support)
PLATFORMS="linux/amd64,linux/arm64"

# Builder Name
BUILDER_NAME="gs_crawler_builder"

# Prüfe ob Docker Buildx verfügbar ist
if ! docker buildx version >/dev/null 2>&1; then
    echo "❌ Docker Buildx is not available. Please install Docker Desktop or enable buildx."
    exit 1
fi

# Erstelle oder verwende Buildx Builder
echo "🔧 Setting up Docker Buildx builder..."
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    echo "Creating new buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
else
    echo "Using existing buildx builder: $BUILDER_NAME"
fi

# Aktiviere den Builder
docker buildx use "$BUILDER_NAME"

# Funktion zum Bauen eines Base-Images mit Buildx
build_image() {
    local image_name=$1
    local build_dir=$2
    
    echo "🏗️  Building $image_name for platforms: $PLATFORMS..."
    
    if [ -d "$build_dir" ]; then
        cd "$build_dir"
        
        # Build mit Buildx für Multi-Platform
        if docker buildx build \
            --platform "$PLATFORMS" \
            --tag "stuffdev/$image_name:latest" \
            --tag "stuffdev/$image_name:$version_number" \
            --push \
            --progress=plain \
            .; then
            echo "✅ Successfully built $image_name"
        else
            echo "❌ Failed to build $image_name"
            exit 1
        fi
        cd ".."
    else
        echo "❌ Directory $build_dir not found"
        exit 1
    fi
}

# Baue alle Base-Images
build_image "python_basic_crawler" "$BASE_DIR/python_basic_crawler"
build_image "python_selenium_crawler" "$BASE_DIR/python_selenium_crawler"  
build_image "php_basic_crawler" "$BASE_DIR/php_basic_crawler"
build_image "flask_monitor" "$BASE_DIR/flask_monitor"

echo ""
echo "🎉 All base images built successfully!"
echo ""
echo "📋 Built images for platforms: $PLATFORMS"
echo "🏷️  Version: $version_number"
echo ""
echo "Available images in registry:"
echo "- stuffdev/python_basic_crawler:latest"
echo "- stuffdev/python_basic_crawler:$version_number"
echo "- stuffdev/python_selenium_crawler:latest"
echo "- stuffdev/python_selenium_crawler:$version_number"
echo "- stuffdev/php_basic_crawler:latest"
echo "- stuffdev/php_basic_crawler:$version_number"
echo "- stuffdev/flask_monitor:latest"
echo "- stuffdev/flask_monitor:$version_number"
echo ""
echo "🚀 You can now update your docker-compose.yml to use these base images."
echo "💡 Note: Images are pushed to registry and available for multi-platform deployment."
