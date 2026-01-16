<#
.SYNOPSIS
    E2E Test Harness for AI-Dataanalyzer-Researcher
    
.DESCRIPTION
    Runs complete E2E test suite including:
    - Stack readiness checks
    - Seed data ingestion
    - Playwright E2E tests
    - Optional k6 benchmarks
    
.PARAMETER SkipIngestion
    Skip the smart_ingest seed run
    
.PARAMETER RunBenchmark
    Run k6 performance benchmarks after tests
    
.EXAMPLE
    .\e2e_run.ps1
    .\e2e_run.ps1 -SkipIngestion
    .\e2e_run.ps1 -RunBenchmark
#>

param(
    [switch]$SkipIngestion,
    [switch]$RunBenchmark
)

$ErrorActionPreference = "Stop"
$RepoRoot = "F:\AI-Dataanalyzer-Researcher"
$UIDir = "$RepoRoot\ui\perplexica"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArtifactsDir = "$RepoRoot\artifacts\e2e\$Timestamp"

# Create artifacts directory
New-Item -ItemType Directory -Force -Path $ArtifactsDir | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " E2E Test Harness - $Timestamp" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# =============================================================================
# 1) DOCKER STACK
# =============================================================================

Write-Host "`n[1/6] Starting Docker Stack..." -ForegroundColor Yellow
Set-Location $RepoRoot
docker compose up -d 2>&1 | Out-File "$ArtifactsDir\docker_up.log"

# Wait for services
Write-Host "      Waiting 10s for services to stabilize..."
Start-Sleep -Seconds 10

# =============================================================================
# 2) READINESS CHECKS
# =============================================================================

Write-Host "`n[2/6] Running Readiness Checks..." -ForegroundColor Yellow

$ReadinessResults = @{}

# Perplexica UI
try {
    $r = Invoke-WebRequest -Uri "http://localhost:3100" -TimeoutSec 10 -UseBasicParsing
    $ReadinessResults.PerplexicaUI = $r.StatusCode -eq 200
    Write-Host "      Perplexica UI: OK" -ForegroundColor Green
} catch {
    $ReadinessResults.PerplexicaUI = $false
    Write-Host "      Perplexica UI: FAIL" -ForegroundColor Red
}

# Ollama
try {
    $r = Invoke-RestMethod -Uri "http://localhost:11435/api/tags" -TimeoutSec 10
    $modelCount = $r.models.Count
    $ReadinessResults.Ollama = $modelCount -gt 0
    Write-Host "      Ollama: OK ($modelCount models)" -ForegroundColor Green
} catch {
    $ReadinessResults.Ollama = $false
    Write-Host "      Ollama: FAIL" -ForegroundColor Red
}

# Qdrant
try {
    $r = Invoke-RestMethod -Uri "http://localhost:6333/collections" -TimeoutSec 10
    $ReadinessResults.Qdrant = $true
    Write-Host "      Qdrant: OK" -ForegroundColor Green
} catch {
    $ReadinessResults.Qdrant = $false
    Write-Host "      Qdrant: FAIL" -ForegroundColor Red
}

# Tika
try {
    $r = Invoke-WebRequest -Uri "http://localhost:9998/tika" -TimeoutSec 10 -UseBasicParsing
    $ReadinessResults.Tika = $r.StatusCode -eq 200
    Write-Host "      Tika: OK" -ForegroundColor Green
} catch {
    $ReadinessResults.Tika = $false
    Write-Host "      Tika: FAIL" -ForegroundColor Red
}

# Check if all passed
$allReady = $ReadinessResults.Values | Where-Object { $_ -eq $false } | Measure-Object
if ($allReady.Count -gt 0) {
    Write-Host "`n[ERROR] Not all services are ready. Aborting." -ForegroundColor Red
    $ReadinessResults | ConvertTo-Json | Out-File "$ArtifactsDir\readiness.json"
    exit 1
}

$ReadinessResults | ConvertTo-Json | Out-File "$ArtifactsDir\readiness.json"

# =============================================================================
# 3) SEED INGESTION
# =============================================================================

if (-not $SkipIngestion) {
    Write-Host "`n[3/6] Running Seed Ingestion..." -ForegroundColor Yellow
    Set-Location $RepoRoot
    $env:PYTHONPATH = $RepoRoot
    
    try {
        python scripts\smart_ingest.py --once 2>&1 | Out-File "$ArtifactsDir\ingestion.log"
        Write-Host "      Ingestion: OK" -ForegroundColor Green
    } catch {
        Write-Host "      Ingestion: FAIL (see logs)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[3/6] Skipping Ingestion (--SkipIngestion)" -ForegroundColor Yellow
}

# =============================================================================
# 4) PLAYWRIGHT E2E TESTS
# =============================================================================

Write-Host "`n[4/6] Running Playwright E2E Tests..." -ForegroundColor Yellow
Set-Location $UIDir

$env:E2E_UI_BASE_URL = "http://localhost:3100"

try {
    npm run test:e2e 2>&1 | Tee-Object -FilePath "$ArtifactsDir\playwright.log"
    $PlaywrightExit = $LASTEXITCODE
    
    if ($PlaywrightExit -eq 0) {
        Write-Host "      Playwright: PASSED" -ForegroundColor Green
    } else {
        Write-Host "      Playwright: FAILED (exit $PlaywrightExit)" -ForegroundColor Red
    }
} catch {
    Write-Host "      Playwright: ERROR - $_" -ForegroundColor Red
    $PlaywrightExit = 1
}

# Copy Playwright report
if (Test-Path "$UIDir\playwright-report") {
    Copy-Item -Recurse "$UIDir\playwright-report" "$ArtifactsDir\playwright-report"
}

# =============================================================================
# 5) LOG ANALYSIS
# =============================================================================

Write-Host "`n[5/6] Analyzing Logs for Errors..." -ForegroundColor Yellow
Set-Location $RepoRoot

$ErrorPatterns = @("ERROR", "Traceback", "Exception", "CRITICAL")
$Services = @("conductor-api", "conductor-neural-search", "conductor-ollama", "conductor-perplexica")

foreach ($svc in $Services) {
    $logs = docker compose logs -n 100 $svc 2>&1
    $errors = $logs | Select-String -Pattern ($ErrorPatterns -join "|")
    
    if ($errors.Count -gt 0) {
        Write-Host "      $svc : $($errors.Count) errors found" -ForegroundColor Yellow
        $errors | Out-File "$ArtifactsDir\errors_$svc.log"
    } else {
        Write-Host "      $svc : No errors" -ForegroundColor Green
    }
}

# =============================================================================
# 6) OPTIONAL BENCHMARK
# =============================================================================

if ($RunBenchmark) {
    Write-Host "`n[6/6] Running k6 Benchmark..." -ForegroundColor Yellow
    
    if (Get-Command k6 -ErrorAction SilentlyContinue) {
        k6 run --env BASE_URL=http://localhost:3100 "$RepoRoot\bench\k6_search.js" 2>&1 | Tee-Object -FilePath "$ArtifactsDir\k6_results.log"
    } else {
        Write-Host "      k6 not installed, skipping benchmark" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[6/6] Skipping Benchmark (use -RunBenchmark)" -ForegroundColor Yellow
}

# =============================================================================
# SUMMARY
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " E2E Run Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Artifacts: $ArtifactsDir"
Write-Host "Playwright Exit Code: $PlaywrightExit"

exit $PlaywrightExit
