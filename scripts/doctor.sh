#!/bin/bash
# doctor.sh - Repo Health Check (Bash/Linux/WSL)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Running Doctor Check..."

# 1. Check .env
if [ -f ".env" ]; then
    echo -e "${GREEN}OK: .env exists${NC}"
else
    echo -e "${RED}FAIL: .env missing. Run: cp .env.example .env${NC}"
    exit 1
fi

# 2. Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}OK: Docker command available${NC}"
else
    echo -e "${RED}FAIL: Docker not found${NC}"
    exit 1
fi

# 3. Check Compose Config
if docker compose config --quiet; then
    echo -e "${GREEN}OK: Docker Compose config is valid${NC}"
else
    echo -e "${RED}FAIL: Docker Compose config invalid${NC}"
    exit 1
fi

echo -e "${GREEN}Doctor Check Complete.${NC}"
