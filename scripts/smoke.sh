#!/bin/bash
#
# Smoke test for Conductor stack - checks reachable endpoints.
# Run after `docker compose up -d` to confirm healthy state.
#
# Usage:
#   ./scripts/smoke.sh            # base stack
#   ./scripts/smoke.sh --overlay  # base + intelligence overlay
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

OVERLAY=false
for arg in "$@"; do
    case "$arg" in
        --overlay) OVERLAY=true ;;
        -h|--help)
            echo "Usage: $0 [--overlay]"
            exit 0
            ;;
    esac
done

compose_args=()
if [ "$OVERLAY" = true ]; then
    compose_args=(-f docker-compose.yml -f docker-compose.intelligence.yml)
fi

running_services=$(docker compose "${compose_args[@]}" ps --services --status running 2>/dev/null || true)
if [ -z "$running_services" ]; then
    echo -e "${RED}❌ No running services detected.${NC}"
    echo -e "${CYAN}💡 TIP: Start the stack first:${NC}"
    echo "   docker compose up -d"
    exit 1
fi

is_running() {
    echo "$running_services" | grep -Fxq "$1"
}

# Service endpoints from README (checked only if service is running)
endpoints=(
    "perplexica|Perplexica UI|http://localhost:3100|200"
    "conductor-api|Conductor API|http://localhost:8010/health|200"
    "neural-search-api|Neural Search API|http://localhost:8040/health|200"
    "qdrant|Qdrant|http://localhost:6335|200"
    "ollama|Ollama|http://localhost:11435|200"
    "orchestrator|Orchestrator|http://localhost:8020/health|200"
    "n8n|n8n|http://localhost:5680|200"
    "tika|Tika|http://localhost:9998|200"
    "special-parser|Special Parser|http://localhost:8016/health|200"
)

passed=0
failed=0
skipped=0

echo -e "\n${CYAN}🔍 CONDUCTOR SMOKE TEST${NC}"
echo "=================================================="

checked=0
for entry in "${endpoints[@]}"; do
    IFS="|" read -r service name url expected <<< "$entry"
    if ! is_running "$service"; then
        echo -e "${YELLOW}⚠️  $name${NC} (Service not running)"
        ((skipped++))
        continue
    fi

    checked=$((checked + 1))
    status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")

    if [ "$status" == "$expected" ]; then
        echo -e "${GREEN}✅ $name${NC} ($url)"
        ((passed++))
    elif [ "$status" == "000" ]; then
        echo -e "${RED}❌ $name${NC} (Not reachable)"
        ((failed++))
    else
        echo -e "${YELLOW}⚠️  $name${NC} (Status: $status)"
        ((skipped++))
    fi
done

if [ $checked -eq 0 ]; then
    echo -e "${RED}❌ No running services matched smoke targets.${NC}"
    exit 1
fi

echo "=================================================="
echo -e "RESULTS: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}, ${YELLOW}$skipped skipped${NC}"

if [ $failed -gt 0 ]; then
    echo -e "\n${CYAN}💡 TIP: Make sure services are running with:${NC}"
    echo "   docker compose up -d"
    exit 1
fi

echo -e "\n${GREEN}✅ All critical services are reachable!${NC}"
exit 0
