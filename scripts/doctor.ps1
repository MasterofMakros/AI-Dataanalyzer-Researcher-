# doctor.ps1 - Repo Health Check
# Usage: ./scripts/doctor.ps1

$ErrorActionPreference = "Stop"

function Write-Ok { param($msg) Write-Host "OK: $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "FAIL: $msg" -ForegroundColor Red }

Write-Host "Running Doctor Check..." -ForegroundColor Cyan

# 1. Check .env
if (Test-Path ".env") {
    Write-Ok ".env exists"
} else {
    Write-Fail ".env missing. Run: Copy-Item .env.example .env"
    exit 1
}

# 2. Check Docker
try {
    docker --version | Out-Null
    Write-Ok "Docker command available"
} catch {
    Write-Fail "Docker not found in PATH"
    exit 1
}

# 3. Check Compose Config
try {
    docker compose config --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker Compose config is valid"
    } else {
        Write-Fail "Docker Compose config invalid"
        exit 1
    }
} catch {
    Write-Fail "Failed to run docker compose config"
    exit 1
}

# 4. Check Python
try {
    python --version | Out-Null
    Write-Ok "Python available"
} catch {
    Write-Fail "Python not found"
    # Non-critical for some agents if they use docker only
}

Write-Host "Doctor Check Complete." -ForegroundColor Green
exit 0
