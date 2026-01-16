#!/bin/bash
# Run the consolidated docker-compose setup
# Usage: ./scripts/run-consolidated.sh [up|down|logs|build]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

ACTION="${1:-up}"

cd "$PROJECT_ROOT"

case "$ACTION" in
    up)
        echo "Starting consolidated crawler stack..."
        docker compose -f compose.consolidated.yaml up -d
        echo ""
        echo "Services started. Check status with:"
        echo "  docker compose -f compose.consolidated.yaml ps"
        echo ""
        echo "Health monitor: http://localhost:5015"
        ;;
    down)
        echo "Stopping consolidated crawler stack..."
        docker compose -f compose.consolidated.yaml down
        ;;
    logs)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            docker compose -f compose.consolidated.yaml logs -f "$SERVICE"
        else
            docker compose -f compose.consolidated.yaml logs -f
        fi
        ;;
    build)
        echo "Building all images..."
        docker compose -f compose.consolidated.yaml build
        ;;
    ps)
        docker compose -f compose.consolidated.yaml ps
        ;;
    *)
        echo "Usage: $0 [up|down|logs|build|ps]"
        echo ""
        echo "Commands:"
        echo "  up     - Start all services"
        echo "  down   - Stop all services"
        echo "  logs   - Follow logs (optionally specify service name)"
        echo "  build  - Build all images"
        echo "  ps     - Show running services"
        exit 1
        ;;
esac
