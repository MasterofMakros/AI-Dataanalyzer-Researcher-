# cli_pattern.ps1 - Standard CLI Pattern
# Usage: ./cli_pattern.ps1 [-Target] <path> [-DryRun]

param (
    [Parameter(Mandatory=$true)]
    [string]$Target,

    [switch]$DryRun = $false
)

# 1. Error Handling & Strict Mode
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 2. Output Helpers
function Write-Step { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "OK: $msg" -ForegroundColor Green }
function Write-ErrorMsg { param($msg) Write-Host "FAIL: $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "INFO: $msg" -ForegroundColor Gray }

# 3. Validation Logic
if (-not (Test-Path $Target)) {
    Write-ErrorMsg "Target path '$Target' does not exist."
    exit 1
}

# 4. Core Execution Block
try {
    Write-Step "Starting Operation on $Target"

    if ($DryRun) {
        Write-Info "Dry Run active. Not making changes."
    } else {
        # Actual logic here
        Write-Info "Processing..."
        Start-Sleep -Milliseconds 500
    }

    Write-Success "Operation Complete."
} catch {
    Write-ErrorMsg "Unexpected Error: $_"
    exit 1
}
