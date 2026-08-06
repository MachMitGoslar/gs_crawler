#!/bin/bash
# =============================================================================
# GS Crawler - Local Development Script
#
# Usage:
#   ./scripts/dev.sh setup     - First-time setup (build base images)
#   ./scripts/dev.sh up        - Start all containers
#   ./scripts/dev.sh down      - Stop all containers
#   ./scripts/dev.sh logs      - Follow logs (optional: service name)
#   ./scripts/dev.sh build     - Rebuild all containers
#   ./scripts/dev.sh ps        - Show running containers
#   ./scripts/dev.sh test      - Run scraper config tests
#   ./scripts/dev.sh shell <s> - Open shell in container
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/compose.dev.yaml"
WEBSERVER_COMPOSE_FILE="$PROJECT_ROOT/compose.webserver.yaml"
COMPOSE_ARGS=(-f "$COMPOSE_FILE" -f "$WEBSERVER_COMPOSE_FILE")

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${GREEN}=== GS Crawler Development ===${NC}"
    echo ""
}

check_base_images() {
    # Check if base images exist locally
    if ! docker images | grep -q "ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler"; then
        echo -e "${YELLOW}⚠️  Base images not found locally.${NC}"
        echo "Run './scripts/dev.sh setup' first to build base images."
        return 1
    fi
    return 0
}

case "${1:-help}" in
    setup)
        print_header
        echo "🔧 Setting up local development environment..."
        echo ""

        # Create output directory
        mkdir -p httpdocs/crawler

        # Build base images
        "$SCRIPT_DIR/build-base-images-local.sh"

        echo ""
        echo -e "${GREEN}✅ Setup complete!${NC}"
        echo ""
        echo "Next: Run './scripts/dev.sh up' to start containers"
        ;;

    up)
        print_header
        if ! check_base_images; then
            exit 1
        fi

        echo "🚀 Starting containers..."
        docker compose "${COMPOSE_ARGS[@]}" up -d --build
        echo ""
        echo -e "${GREEN}✅ Containers started${NC}"
        echo ""
        echo "Health Monitor: http://localhost:5015"
        echo "Altstadtfest:   http://localhost:5016"
        echo "Webserver:      http://localhost:8888/crawler/"
        echo ""
        echo "Run './scripts/dev.sh logs' to follow logs"
        ;;

    down)
        print_header
        echo "🛑 Stopping containers..."
        docker compose "${COMPOSE_ARGS[@]}" down
        echo -e "${GREEN}✅ Containers stopped${NC}"
        ;;

    logs)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            docker compose "${COMPOSE_ARGS[@]}" logs -f "$SERVICE"
        else
            docker compose "${COMPOSE_ARGS[@]}" logs -f
        fi
        ;;

    build)
        print_header
        if ! check_base_images; then
            echo "Building base images first..."
            "$SCRIPT_DIR/build-base-images-local.sh"
        fi

        echo "🔨 Building all containers..."
        docker compose "${COMPOSE_ARGS[@]}" build
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;

    ps)
        docker compose "${COMPOSE_ARGS[@]}" ps
        ;;

    test)
        print_header
        echo "🧪 Testing scraper configurations..."
        "$SCRIPT_DIR/test-all-configs.sh"
        ;;

    shell)
        SERVICE="${2:-}"
        if [ -z "$SERVICE" ]; then
            echo "Usage: ./scripts/dev.sh shell <service_name>"
            echo ""
            echo "Available services:"
            docker compose "${COMPOSE_ARGS[@]}" ps --services
            exit 1
        fi
        docker compose "${COMPOSE_ARGS[@]}" exec "$SERVICE" /bin/sh
        ;;

    restart)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            echo "🔄 Restarting $SERVICE..."
            docker compose "${COMPOSE_ARGS[@]}" restart "$SERVICE"
        else
            echo "🔄 Restarting all containers..."
            docker compose "${COMPOSE_ARGS[@]}" restart
        fi
        echo -e "${GREEN}✅ Restart complete${NC}"
        ;;

    *)
        echo "GS Crawler - Local Development"
        echo ""
        echo "Usage: ./scripts/dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup      First-time setup (builds base images)"
        echo "  up         Start all containers"
        echo "  down       Stop all containers"
        echo "  logs [svc] Follow logs (optionally for specific service)"
        echo "  build      Rebuild all containers"
        echo "  ps         Show running containers"
        echo "  test       Run scraper config tests (no Docker needed)"
        echo "  shell <s>  Open shell in container"
        echo "  restart    Restart containers (optionally specific service)"
        echo ""
        echo "First time? Run: ./scripts/dev.sh setup"
        ;;
esac
