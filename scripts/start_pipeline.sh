#!/bin/bash
# =============================================================================
# Neural Vault Pipeline Startup Script
# =============================================================================
# Usage:
#   ./start_pipeline.sh              # Start all services
#   ./start_pipeline.sh --minimal    # Start minimal (Redis + API + UI)
#   ./start_pipeline.sh --gpu        # Start with GPU services
#   ./start_pipeline.sh --scale N    # Scale workers to N instances
#   ./start_pipeline.sh --stop       # Stop all services
#   ./start_pipeline.sh --status     # Show service status
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
SCALE_WORKERS=1
MODE="full"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --minimal)
            MODE="minimal"
            shift
            ;;
        --gpu)
            MODE="gpu"
            shift
            ;;
        --scale)
            SCALE_WORKERS="$2"
            shift 2
            ;;
        --stop)
            MODE="stop"
            shift
            ;;
        --status)
            MODE="status"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --minimal    Start minimal services (Redis, API, UI)"
            echo "  --gpu        Start GPU-accelerated services"
            echo "  --scale N    Scale extraction workers to N instances"
            echo "  --stop       Stop all services"
            echo "  --status     Show service status"
            echo "  --help       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon not running."
        exit 1
    fi
    print_success "Docker is running"
}

check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            print_success "NVIDIA GPU detected"
            return 0
        fi
    fi
    print_warning "No NVIDIA GPU detected - using CPU mode"
    return 1
}

check_env() {
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        print_warning ".env file not found!"
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            echo -n "Creating .env from .env.example... "
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success "Created .env"
            print_warning "PLEASE EDIT .env TO CONFIGURE SECRETS BEFORE PRODUCTION USE!"
            sleep 3
        else
            print_error ".env.example not found. Cannot configure environment."
            exit 1
        fi
    else
        print_success "Environment configured (.env found)"
    fi
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -n "Waiting for $name..."
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}Ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo -e " ${RED}Timeout${NC}"
    return 1
}

start_minimal() {
    print_header "Starting Minimal Services"

    docker compose up -d redis
    wait_for_service "http://localhost:6379" "Redis" 10 || true

    docker compose up -d conductor-api perplexica
    wait_for_service "http://localhost:8010/health" "API" 30
    wait_for_service "http://localhost:3100" "Perplexica UI" 30

    print_success "Minimal services started"
}

start_core() {
    print_header "Starting Core Services"

    # Redis first
    docker compose up -d redis
    sleep 2

    # Search & Storage & LLM
    docker compose up -d tika ollama

    # API & Neural Search & UI
    docker compose up -d conductor-api neural-search-api perplexica

    wait_for_service "http://localhost:9998" "Tika" 30
    wait_for_service "http://localhost:8010/health" "Conductor API" 30
    wait_for_service "http://localhost:8040/health" "Neural Search API" 60
    wait_for_service "http://localhost:3100" "Perplexica UI" 30

    print_success "Core services started"
}

start_pipeline() {
    print_header "Starting Intelligence Pipeline"

    # Document Processor (GPU or CPU based on availability)
    if [[ $HAS_GPU -eq 1 ]]; then
        print_success "Using GPU-accelerated document processor"
        docker compose --profile gpu up -d document-processor
    else
        print_warning "Using CPU-only document processor (slower)"
        docker compose --profile cpu up -d document-processor-cpu
    fi

    # Router & Orchestrator
    docker compose up -d universal-router orchestrator

    # Wait for services (longer timeout for CPU mode)
    local dp_timeout=120
    [[ $HAS_GPU -eq 0 ]] && dp_timeout=300

    wait_for_service "http://localhost:8005/health" "Document Processor" $dp_timeout
    wait_for_service "http://localhost:8030/health" "Universal Router" 30
    wait_for_service "http://localhost:8020/health" "Orchestrator" 30

    print_success "Pipeline services started"
}

start_workers() {
    print_header "Starting Extraction Workers (x$SCALE_WORKERS)"

    docker compose up -d --scale extraction-worker=$SCALE_WORKERS extraction-worker

    sleep 5
    print_success "$SCALE_WORKERS worker(s) started"
}

start_audio() {
    print_header "Starting Audio Processing"

    docker compose up -d whisperx
    wait_for_service "http://localhost:9000/health" "WhisperX" 120

    print_success "Audio processing started"
}

stop_all() {
    print_header "Stopping All Services"
    docker compose down
    print_success "All services stopped"
}

show_status() {
    print_header "Service Status"
    docker compose ps

    echo ""
    print_header "Health Checks"

    services=(
        "http://localhost:6379|Redis"
        "http://localhost:8010/health|Conductor API"
        "http://localhost:8040/health|Neural Search API"
        "http://localhost:3100|Perplexica UI"
        "http://localhost:9998|Tika"
        "http://localhost:8005/health|Document Processor"
        "http://localhost:8030/health|Universal Router"
        "http://localhost:8020/health|Orchestrator"
        "http://localhost:9000/health|WhisperX"
    )

    for service in "${services[@]}"; do
        url="${service%|*}"
        name="${service#*|}"
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$name"
        else
            print_error "$name (not responding)"
        fi
    done
}

init_redis_streams() {
    print_header "Initializing Redis Streams"

    docker exec conductor-redis redis-cli XGROUP CREATE intake:priority extraction-workers $ MKSTREAM 2>/dev/null || true
    docker exec conductor-redis redis-cli XGROUP CREATE intake:normal extraction-workers $ MKSTREAM 2>/dev/null || true
    docker exec conductor-redis redis-cli XGROUP CREATE intake:bulk extraction-workers $ MKSTREAM 2>/dev/null || true
    docker exec conductor-redis redis-cli XGROUP CREATE extract:documents extraction-workers $ MKSTREAM 2>/dev/null || true
    docker exec conductor-redis redis-cli XGROUP CREATE extract:images extraction-workers $ MKSTREAM 2>/dev/null || true
    docker exec conductor-redis redis-cli XGROUP CREATE extract:audio extraction-workers $ MKSTREAM 2>/dev/null || true

    print_success "Redis Streams initialized"
}

init_data() {
    print_header "Initializing Data & Models"

    # 1. Pull Ollama Model
    if docker compose ps | grep -q "conductor-ollama"; then
        echo -n "Pulling Ollama model (llama3.2)... "
        docker exec conductor-ollama ollama pull llama3.2 > /dev/null 2>&1
        print_success "Model pulled"
    else
        print_warning "Ollama container not running. Skipping model pull."
    fi

}

# Main
print_header "Neural Vault Pipeline"

# Handle --init flag specifically
if [[ "$1" == "--init" ]]; then
    check_env
    check_docker
    check_gpu && HAS_GPU=1 || HAS_GPU=0
    
    print_header "Running Full Initialization"
    start_core
    start_pipeline
    init_redis_streams
    init_data
    
    echo ""
    print_success "Initialization Complete. System is ready."
    exit 0
fi

echo "Mode: $MODE"
echo "Workers: $SCALE_WORKERS"
echo ""

check_env
check_docker

case $MODE in
    minimal)
        start_minimal
        init_search_index
        ;;
    gpu)
        HAS_GPU=1
        check_gpu || print_warning "GPU mode requested but no GPU found"
        start_core
        init_search_index
        start_pipeline
        init_redis_streams
        start_workers
        start_audio
        ;;
    full)
        HAS_GPU=0
        check_gpu && HAS_GPU=1

        start_core
        init_search_index
        start_pipeline
        init_redis_streams
        start_workers

        if [[ $HAS_GPU -eq 1 ]]; then
            start_audio
        fi
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
esac

echo ""
print_header "Summary"
show_status
