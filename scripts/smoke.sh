#!/bin/bash
#
# Smoke test for Conductor stack - checks all core endpoints.
# Run after `docker compose up -d` to confirm healthy state.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Service endpoints from README
declare -A endpoints=(
    ["Mission Control"]="http://localhost:3000"
    ["Perplexica"]="http://localhost:3100"
    ["Conductor API"]="http://localhost:8010/health"
    ["Neural Search API"]="http://localhost:8040/health"
    ["Qdrant"]="http://localhost:6335"
    ["Ollama"]="http://localhost:11435"
    ["Orchestrator"]="http://localhost:8020/health"
    ["n8n"]="http://localhost:5680"
    ["Tika"]="http://localhost:9998"
)

passed=0
failed=0
skipped=0

echo -e "\n${CYAN}🔍 CONDUCTOR SMOKE TEST${NC}"
echo "=================================================="

for name in "${!endpoints[@]}"; do
    url="${endpoints[$name]}"
    
    # Check endpoint with curl
    status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
    
    if [ "$status" == "200" ]; then
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

echo "=================================================="
echo -e "RESULTS: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}, ${YELLOW}$skipped skipped${NC}"

if [ $failed -gt 0 ]; then
    echo -e "\n${CYAN}💡 TIP: Make sure services are running with:${NC}"
    echo "   docker compose up -d"
    exit 1
fi

echo -e "\n${GREEN}✅ All critical services are reachable!${NC}"
exit 0
