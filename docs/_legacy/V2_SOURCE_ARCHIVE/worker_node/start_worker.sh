#!/bin/bash
# Conductor Worker Node - Linux/macOS Start Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     CONDUCTOR WORKER NODE              ║${NC}"
echo -e "${CYAN}║     Cross-Platform AI Processing       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
echo ""

# Configuration - Edit these for your setup
export CONDUCTOR_API_URL="${CONDUCTOR_API_URL:-http://192.168.1.254:8000}"
export REDIS_HOST="${REDIS_HOST:-192.168.1.254}"
export REDIS_PORT="${REDIS_PORT:-6379}"

echo -e "${GREEN}[INFO]${NC} Target Conductor: $CONDUCTOR_API_URL"
echo -e "${GREEN}[INFO]${NC} Redis: $REDIS_HOST:$REDIS_PORT"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 not found! Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}[INFO]${NC} Python version: $PYTHON_VERSION"

# Change to script directory
cd "$(dirname "$0")"

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${GREEN}[INFO]${NC} Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}[INFO]${NC} Checking dependencies..."
pip install -q -r requirements.txt

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[WARNING]${NC} FFmpeg not found. Install with:"
    echo "  macOS:  brew install ffmpeg"
    echo "  Linux:  sudo apt install ffmpeg"
fi

# Run the worker
echo -e "${GREEN}[INFO]${NC} Starting Worker..."
echo ""
python3 worker.py

# Handle exit
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Worker crashed with exit code $EXIT_CODE"
    read -p "Press Enter to exit..."
fi
