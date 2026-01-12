#!/bin/bash
# validate.sh - Full Validation Suite (Bash)

set -e

echo -e "\n=== 1. Doctor Check ==="
./scripts/doctor.sh

echo -e "\n=== 2. Python Compile Check ==="
if command -v python3 &> /dev/null; then
    python3 -m compileall . -q
    echo "OK: Python syntax valid"
else
    echo "SKIP: Python3 not found"
fi

echo -e "\n=== 3. Docker Health ==="
if [ "$(docker ps -q)" ]; then
    echo "OK: Containers are running."
else
    echo "INFO: No containers running."
fi

echo -e "\n=== Validation PASSED ==="
