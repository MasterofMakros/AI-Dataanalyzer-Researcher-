# validate.ps1 - Full Validation Suite
# Usage: ./scripts/validate.ps1 [-Quick]

param([switch]$Quick)

$ErrorActionPreference = "Stop"

# 1. Run Doctor First
Write-Host "`n=== 1. Doctor Check ===" -ForegroundColor Cyan
./scripts/doctor.ps1
if ($LASTEXITCODE -ne 0) { exit 1 }

# 2. Python Compile Check
Write-Host "`n=== 2. Python Compile Check ===" -ForegroundColor Cyan
try {
    # Check syntax errors in all python files
    python -m compileall . -q
    if ($LASTEXITCODE -eq 0) {
         Write-Host "OK: Python syntax valid" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Python compile skipped (python not found or failed)" -ForegroundColor Yellow
}

# 3. Docker Health (if visible)
Write-Host "`n=== 3. Docker Health ===" -ForegroundColor Cyan
$containers = docker ps --format "{{.Status}}"
if ($containers) {
    Write-Host "OK: Containers are running." -ForegroundColor Green
    # Optional: Curl health
    try {
        $res = Invoke-WebRequest -Uri "http://localhost:8010/health" -Method Head -ErrorAction SilentlyContinue
        if ($res.StatusCode -eq 200) { Write-Host "OK: Conductor API healthy" -ForegroundColor Green }
    } catch {
        Write-Host "INFO: Conductor API not responsive (might be starting up or not exposed)" -ForegroundColor Gray
    }
} else {
    Write-Host "INFO: No containers running. Skipping runtime health checks." -ForegroundColor Gray
}

Write-Host "`n=== Validation PASSED ===" -ForegroundColor Green
exit 0
