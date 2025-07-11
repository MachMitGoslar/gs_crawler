#!/bin/bash

# Baut alle Base-Images für das GS Crawler System

echo "🔧 Building GS Crawler Base Images..."
echo "=================================="

# Basis-Pfad
BASE_DIR="."

# Funktion zum Bauen eines Base-Images
build_image() {
    local image_name=$1
    local build_dir=$2
    
    echo "🏗️  Building $image_name..."
    
    if [ -d "$build_dir" ]; then
        cd "$build_dir"
        if docker build -t "gs_crawler/$image_name:latest" .; then
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
echo "Available images:"
docker images | grep gs_crawler

echo ""
echo "🚀 You can now update your docker-compose.yml to use these base images."
