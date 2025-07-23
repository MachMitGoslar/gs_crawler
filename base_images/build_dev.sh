#!/bin/bash

# Lokales Build-Script für Entwicklungszwecke (ohne Registry Push)

echo "🔧 Building GS Crawler Base Images Locally..."
echo "============================================"

# Basis-Pfad
BASE_DIR="."

# Lokaler Modus (ohne Push)
LOCAL_MODE=${1:-"true"}
PLATFORMS="linux/amd64"  # Nur lokale Plattform für schnellere Builds

# Funktion zum Bauen eines Base-Images lokal
build_image_local() {
    local image_name=$1
    local build_dir=$2
    
    echo "🏗️  Building $image_name locally..."
    
    if [ -d "$build_dir" ]; then
        cd "$build_dir"
        
        if [ "$LOCAL_MODE" == "true" ]; then
            # Lokaler Build ohne Push
            if docker build -t "gs_crawler/$image_name:latest" .; then
                echo "✅ Successfully built $image_name locally"
            else
                echo "❌ Failed to build $image_name"
                exit 1
            fi
        else
            # Build mit Buildx für Multi-Platform
            if docker buildx build \
                --platform "$PLATFORMS" \
                --tag "gs_crawler/$image_name:latest" \
                --load \
                .; then
                echo "✅ Successfully built $image_name with buildx"
            else
                echo "❌ Failed to build $image_name"
                exit 1
            fi
        fi
        cd ".."
    else
        echo "❌ Directory $build_dir not found"
        exit 1
    fi
}

# Prüfe Docker-Verfügbarkeit
if ! docker --version >/dev/null 2>&1; then
    echo "❌ Docker is not available. Please install Docker first."
    exit 1
fi

# Baue alle Base-Images lokal
echo "📦 Building images locally (fast mode)..."
build_image_local "python_basic_crawler" "$BASE_DIR/python_basic_crawler"
build_image_local "python_selenium_crawler" "$BASE_DIR/python_selenium_crawler"  
build_image_local "php_basic_crawler" "$BASE_DIR/php_basic_crawler"
build_image_local "flask_monitor" "$BASE_DIR/flask_monitor"

echo ""
echo "🎉 All base images built successfully!"
echo ""
echo "Available local images:"
docker images | grep gs_crawler
echo ""
echo "🚀 You can now build your containers with:"
echo "   docker-compose build"
echo ""
echo "💡 For production builds with multi-platform support,"
echo "   use the GitHub Actions workflow instead."
