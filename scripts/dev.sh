#!/bin/bash
# =============================================================================
# GS Crawler - Local Development Script
#
# Usage:
#   ./scripts/dev.sh setup     - First-time setup (build base images)
#   ./scripts/dev.sh up        - Start containers (asks which to rebuild)
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

# Prompts the user to choose which services to rebuild before "up".
# Sets BUILD_ALL, NO_BUILD, SELECTED_SERVICES for the caller.
select_services_to_build() {
    local services=($(docker compose -f "$COMPOSE_FILE" config --services))

    echo "Welche Container sollen neu gebaut werden?"
    echo ""
    local i=1
    for s in "${services[@]}"; do
        printf "  %2d) %s\n" "$i" "$s"
        i=$((i + 1))
    done
    echo ""
    echo "   a) Alle (Standard)"
    echo "   n) Keinen (nur starten, kein Rebuild)"
    echo ""
    read -p "Auswahl (Enter = alle, Nummern getrennt durch Leerzeichen, z.B. '3 7'): " selection
    selection="${selection:-a}"

    BUILD_ALL=false
    NO_BUILD=false
    SELECTED_SERVICES=()

    if [ "$selection" = "a" ] || [ "$selection" = "A" ]; then
        BUILD_ALL=true
    elif [ "$selection" = "n" ] || [ "$selection" = "N" ]; then
        NO_BUILD=true
    else
        for num in $selection; do
            local idx=$((num - 1))
            if [[ "$num" =~ ^[0-9]+$ ]] && [ "$idx" -ge 0 ] && [ "$idx" -lt "${#services[@]}" ]; then
                SELECTED_SERVICES+=("${services[$idx]}")
            else
                echo -e "${YELLOW}⚠️  Ungültige Nummer '$num' wird ignoriert${NC}"
            fi
        done

        if [ "${#SELECTED_SERVICES[@]}" -eq 0 ]; then
            echo -e "${YELLOW}⚠️  Keine gültige Auswahl, breche ab.${NC}"
            exit 1
        fi
    fi
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

        select_services_to_build

        echo ""
        if [ "$BUILD_ALL" = true ]; then
            echo "🚀 Starting containers (rebuilding all)..."
            docker compose -f "$COMPOSE_FILE" up -d --build
        elif [ "$NO_BUILD" = true ]; then
            echo "🚀 Starting containers (no rebuild)..."
            docker compose -f "$COMPOSE_FILE" up -d
        else
            echo "🔨 Rebuilding: ${SELECTED_SERVICES[*]}"
            docker compose -f "$COMPOSE_FILE" build "${SELECTED_SERVICES[@]}"
            echo "🚀 Starting containers..."
            docker compose -f "$COMPOSE_FILE" up -d
        fi
        echo ""
        echo -e "${GREEN}✅ Containers started${NC}"
        echo ""
        echo "Health Monitor: http://localhost:5015"
        echo "Altstadtfest:   http://localhost:5016"
        echo ""
        echo "Run './scripts/dev.sh logs' to follow logs"
        ;;

    down)
        print_header
        echo "🛑 Stopping containers..."
        docker compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}✅ Containers stopped${NC}"
        ;;

    logs)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            docker compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
        else
            docker compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;

    build)
        print_header
        if ! check_base_images; then
            echo "Building base images first..."
            "$SCRIPT_DIR/build-base-images-local.sh"
        fi

        echo "🔨 Building all containers..."
        docker compose -f "$COMPOSE_FILE" build
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;

    ps)
        docker compose -f "$COMPOSE_FILE" ps
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
            docker compose -f "$COMPOSE_FILE" ps --services
            exit 1
        fi
        docker compose -f "$COMPOSE_FILE" exec "$SERVICE" /bin/sh
        ;;

    restart)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            echo "🔄 Restarting $SERVICE..."
            docker compose -f "$COMPOSE_FILE" restart "$SERVICE"
        else
            echo "🔄 Restarting all containers..."
            docker compose -f "$COMPOSE_FILE" restart
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
        echo "  up         Start containers (asks which to rebuild)"
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
