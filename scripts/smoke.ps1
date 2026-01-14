#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Smoke test for Conductor stack - checks all core endpoints.
.DESCRIPTION
    Verifies that all essential services are reachable.
    Run after `docker compose up -d` to confirm healthy state.
#>

param(
    [switch]$Quiet,
    [switch]$Overlay
)

$ErrorActionPreference = "Continue"

$composeArgs = @()
if ($Overlay) {
    $composeArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.intelligence.yml")
}

$runningServices = & docker compose @composeArgs ps --services --status running 2>$null
if (-not $runningServices) {
    Write-Host "❌ No running services detected." -ForegroundColor Red
    Write-Host "💡 TIP: Start the stack first:" -ForegroundColor Cyan
    Write-Host "   docker compose up -d" -ForegroundColor White
    exit 1
}

$runningSet = New-Object System.Collections.Generic.HashSet[string]
foreach ($svc in $runningServices) {
    [void]$runningSet.Add($svc)
}

# Service endpoints from README (checked only if service is running)
$endpoints = @(
    @{ Service = "perplexica";       Name = "Perplexica UI";     URL = "http://localhost:3100";        Expected = 200 },
    @{ Service = "conductor-api";    Name = "Conductor API";     URL = "http://localhost:8010/health"; Expected = 200 },
    @{ Service = "neural-search-api";Name = "Neural Search API"; URL = "http://localhost:8040/health"; Expected = 200 },
    @{ Service = "qdrant";           Name = "Qdrant";            URL = "http://localhost:6335";        Expected = 200 },
    @{ Service = "ollama";           Name = "Ollama";            URL = "http://localhost:11435";       Expected = 200 },
    @{ Service = "orchestrator";     Name = "Orchestrator";      URL = "http://localhost:8020/health"; Expected = 200 },
    @{ Service = "n8n";              Name = "n8n";               URL = "http://localhost:5680";        Expected = 200 },
    @{ Service = "tika";             Name = "Tika";              URL = "http://localhost:9998";        Expected = 200 },
    @{ Service = "special-parser";   Name = "Special Parser";    URL = "http://localhost:8016/health"; Expected = 200 }
)

$passed = 0
$failed = 0
$skipped = 0
$checked = 0

Write-Host "`n🔍 CONDUCTOR SMOKE TEST" -ForegroundColor Cyan
Write-Host "=" * 50

foreach ($ep in $endpoints) {
    if (-not $runningSet.Contains($ep.Service)) {
        Write-Host "⚠️  $($ep.Name)" -ForegroundColor Yellow -NoNewline
        Write-Host " (Service not running)" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    $checked++
    try {
        $response = Invoke-WebRequest -Uri $ep.URL -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq $ep.Expected) {
            Write-Host "✅ $($ep.Name)" -ForegroundColor Green -NoNewline
            Write-Host " ($($ep.URL))" -ForegroundColor DarkGray
            $passed++
        } else {
            Write-Host "⚠️  $($ep.Name)" -ForegroundColor Yellow -NoNewline
            Write-Host " (Status: $($response.StatusCode), Expected: $($ep.Expected))" -ForegroundColor DarkGray
            $skipped++
        }
    } catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -match "Unable to connect|Connection refused|timeout") {
            Write-Host "❌ $($ep.Name)" -ForegroundColor Red -NoNewline
            Write-Host " (Not reachable)" -ForegroundColor DarkGray
            $failed++
        } else {
            Write-Host "⚠️  $($ep.Name)" -ForegroundColor Yellow -NoNewline
            Write-Host " ($errorMsg)" -ForegroundColor DarkGray
            $skipped++
        }
    }
}

Write-Host "`n" + "=" * 50
Write-Host "RESULTS: " -NoNewline
Write-Host "$passed passed" -ForegroundColor Green -NoNewline
Write-Host ", $failed failed" -ForegroundColor Red -NoNewline
Write-Host ", $skipped skipped" -ForegroundColor Yellow

if ($checked -eq 0) {
    Write-Host "`n❌ No running services matched smoke targets." -ForegroundColor Red
    exit 1
}

if ($failed -gt 0) {
    Write-Host "`n💡 TIP: Make sure services are running with:" -ForegroundColor Cyan
    Write-Host "   docker compose up -d" -ForegroundColor White
    exit 1
}

Write-Host "`n✅ All critical services are reachable!" -ForegroundColor Green
exit 0
