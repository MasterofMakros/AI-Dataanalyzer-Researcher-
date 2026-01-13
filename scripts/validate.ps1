# validate.ps1 - Full Validation Suite
# Usage: ./scripts/validate.ps1 [-Quick] [-SkipDocker]

param(
    [switch]$Quick,
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
$script:failures = 0

function Test-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $Action
        Write-Host "OK: $Name" -ForegroundColor Green
    } catch {
        Write-Host "FAIL: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $script:failures++
    }
}

# 1. Doctor Check
Test-Step "Doctor Check" {
    if (Test-Path "./scripts/doctor.ps1") {
        ./scripts/doctor.ps1
        if ($LASTEXITCODE -ne 0) { throw "Doctor failed" }
    } else {
        Write-Host "SKIP: doctor.ps1 not found" -ForegroundColor Yellow
    }
}

# 2. Python Compile Check
Test-Step "Python Compile Check" {
    $result = python -m compileall . -q 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python compile failed" }
}

# 3. Pytest (Backend Tests)
if (-not $Quick) {
    Test-Step "Backend Tests (pytest)" {
        if (Test-Path "./tests") {
            pytest tests/ --tb=short -q
            if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
        } else {
            Write-Host "SKIP: tests/ not found" -ForegroundColor Yellow
        }
    }
}

# 4. Frontend Lint Check
if (-not $Quick) {
    Test-Step "Frontend Lint Check" {
        if (Test-Path "./ui/perplexica/package.json") {
            Push-Location ./ui/perplexica
            npm run lint --if-present
            if ($LASTEXITCODE -ne 0) { throw "npm lint failed" }
            Pop-Location
        } else {
            Write-Host "SKIP: ui/perplexica not found" -ForegroundColor Yellow
        }
    }
}

# 5. Frontend Build Check
if (-not $Quick) {
    Test-Step "Frontend Build Check" {
        if (Test-Path "./ui/perplexica/package.json") {
            Push-Location ./ui/perplexica
            npm run build --if-present 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "npm build failed" }
            Pop-Location
        } else {
            Write-Host "SKIP: ui/perplexica not found" -ForegroundColor Yellow
        }
    }
}

# 6. Docker Compose Validation
if (-not $SkipDocker) {
    Test-Step "Docker Compose Config" {
        docker compose config --quiet
        if ($LASTEXITCODE -ne 0) { throw "docker compose config invalid" }
    }
}

# 7. Smoke Test (if containers running)
if (-not $SkipDocker) {
    Test-Step "Smoke Test" {
        $containers = docker ps --format "{{.Names}}" 2>$null
        if ($containers) {
            if (Test-Path "./scripts/smoke.ps1") {
                ./scripts/smoke.ps1 -Quiet
            }
        } else {
            Write-Host "SKIP: No containers running" -ForegroundColor Yellow
        }
    }
}

# Summary
Write-Host "`n" + "=" * 50
if ($script:failures -eq 0) {
    Write-Host "✅ VALIDATION PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ VALIDATION FAILED ($script:failures issues)" -ForegroundColor Red
    exit 1
}
