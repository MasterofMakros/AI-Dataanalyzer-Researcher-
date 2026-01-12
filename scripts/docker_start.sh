#!/bin/bash
# =============================================================================
# Neural Vault Docker Startup Script
# =============================================================================
# Usage:
#   ./docker_start.sh              # Start all services
#   ./docker_start.sh api          # Start only API and dependencies
#   ./docker_start.sh rebuild      # Rebuild and start
#   ./docker_start.sh logs         # Show logs
#   ./docker_start.sh stop         # Stop all services
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')]${NC} $1"
}

# Check .env file
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            warn ".env nicht gefunden, kopiere .env.example..."
            cp .env.example .env
            warn "Bitte .env anpassen!"
        else
            error ".env nicht gefunden!"
            exit 1
        fi
    fi
}

# Core services (minimal)
CORE_SERVICES="redis tika qdrant"

# API services
API_SERVICES="$CORE_SERVICES conductor-api"

# All services
ALL_SERVICES=""

case "${1:-all}" in
    "api")
        check_env
        log "Starte API-Services..."
        docker compose up -d $API_SERVICES
        log "Warte auf Services..."
        sleep 10
        log "Health Check..."
        curl -s http://localhost:8010/health | python -m json.tool || warn "API noch nicht bereit"
        log "API verfügbar unter: http://localhost:8010"
        log "API Docs: http://localhost:8010/docs"
        ;;

    "rebuild")
        check_env
        log "Rebuild conductor-api..."
        docker compose build conductor-api
        docker compose up -d conductor-api
        log "Rebuild abgeschlossen"
        ;;

    "logs")
        docker compose logs -f ${2:-conductor-api}
        ;;

    "stop")
        log "Stoppe alle Services..."
        docker compose down
        log "Gestoppt"
        ;;

    "status")
        docker compose ps
        ;;

    "all"|"")
        check_env
        log "Starte alle Services..."
        docker compose up -d
        log "Alle Services gestartet"
        docker compose ps
        ;;

    *)
        echo "Usage: $0 {api|rebuild|logs|stop|status|all}"
        exit 1
        ;;
esac
