#!/bin/bash
#
# validate.sh - Full Validation Suite for Linux/macOS
# Usage: ./scripts/validate.sh [--quick] [--skip-docker]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

QUICK=false
SKIP_DOCKER=false
FAILURES=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --quick) QUICK=true ;;
        --skip-docker) SKIP_DOCKER=true ;;
    esac
done

test_step() {
    local name=$1
    local cmd=$2
    echo -e "\n${CYAN}=== $name ===${NC}"
    if eval "$cmd"; then
        echo -e "${GREEN}OK: $name${NC}"
    else
        echo -e "${RED}FAIL: $name${NC}"
        ((FAILURES++))
    fi
}

# 1. Doctor Check
test_step "Doctor Check" '
    if [ -f "./scripts/doctor.sh" ]; then
        ./scripts/doctor.sh
    else
        echo -e "${YELLOW}SKIP: doctor.sh not found${NC}"
    fi
'

# 2. Python Compile Check
test_step "Python Compile Check" '
    python3 -m compileall . -q 2>/dev/null || python -m compileall . -q
'

# 3. Pytest (Backend Tests)
if [ "$QUICK" = false ]; then
    test_step "Backend Tests (pytest)" '
        if [ -d "./tests" ]; then
            pytest tests/ --tb=short -q
        else
            echo -e "${YELLOW}SKIP: tests/ not found${NC}"
        fi
    '
fi

# 4. Frontend Build Check
if [ "$QUICK" = false ]; then
    test_step "Frontend Build Check" '
        if [ -f "./ui/perplexica/package.json" ]; then
            cd ./ui/perplexica && npm run build --if-present >/dev/null 2>&1 && cd ../..
        else
            echo -e "${YELLOW}SKIP: ui/perplexica not found${NC}"
        fi
    '
fi

# 5. Docker Compose Validation
if [ "$SKIP_DOCKER" = false ]; then
    test_step "Docker Compose Config" '
        docker compose config --quiet
    '
fi

# 6. Smoke Test (if containers running)
if [ "$SKIP_DOCKER" = false ]; then
    test_step "Smoke Test" '
        containers=$(docker ps --format "{{.Names}}" 2>/dev/null)
        if [ -n "$containers" ]; then
            if [ -f "./scripts/smoke.sh" ]; then
                ./scripts/smoke.sh
            fi
        else
            echo -e "${YELLOW}SKIP: No containers running${NC}"
        fi
    '
fi

# Summary
echo ""
echo "=================================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED ($FAILURES issues)${NC}"
    exit 1
fi
