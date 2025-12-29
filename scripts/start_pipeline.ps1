# =============================================================================
# Neural Vault Pipeline Startup Script (Windows PowerShell)
# =============================================================================
# Usage:
#   .\start_pipeline.ps1              # Start all services
#   .\start_pipeline.ps1 -Minimal     # Start minimal (Redis + API + UI)
#   .\start_pipeline.ps1 -GPU         # Start with GPU services
#   .\start_pipeline.ps1 -Scale 4     # Scale workers to 4 instances
#   .\start_pipeline.ps1 -Stop        # Stop all services
#   .\start_pipeline.ps1 -Status      # Show service status
# =============================================================================

param(
    [switch]$Minimal,
    [switch]$GPU,
    [switch]$Stop,
    [switch]$Status,
    [int]$Scale = 1
)

$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# Functions
function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host " $Message" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Docker {
    try {
        $null = docker info 2>$null
        Write-Success "Docker is running"
        return $true
    }
    catch {
        Write-Error "Docker not running or not installed"
        return $false
    }
}

function Test-GPU {
    try {
        $null = nvidia-smi 2>$null
        Write-Success "NVIDIA GPU detected"
        return $true
    }
    catch {
        Write-Warning "No NVIDIA GPU detected - using CPU mode"
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [string]$Name,
        [int]$MaxAttempts = 30
    )

    Write-Host -NoNewline "Waiting for $Name..."

    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host " Ready" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Ignore errors, keep waiting
        }
        Write-Host -NoNewline "."
        Start-Sleep -Seconds 2
    }

    Write-Host " Timeout" -ForegroundColor Red
    return $false
}

function Start-MinimalServices {
    Write-Header "Starting Minimal Services"

    docker compose up -d redis
    Start-Sleep -Seconds 2

    docker compose up -d conductor-api mission-control
    Wait-ForService "http://localhost:8010/health" "API" 30
    Wait-ForService "http://localhost:3000/health" "UI" 30

    Write-Success "Minimal services started"
}

function Start-CoreServices {
    Write-Header "Starting Core Services"

    docker compose up -d redis
    Start-Sleep -Seconds 2

    docker compose up -d meilisearch tika ollama
    docker compose up -d conductor-api neural-search-api mission-control

    Wait-ForService "http://localhost:7700/health" "Meilisearch" 60
    Wait-ForService "http://localhost:9998" "Tika" 30
    Wait-ForService "http://localhost:8010/health" "Conductor API" 30
    Wait-ForService "http://localhost:8040/health" "Neural Search API" 60
    Wait-ForService "http://localhost:3000/health" "Mission Control" 30

    Write-Success "Core services started"
}

function Start-PipelineServices {
    param([bool]$UseGPU = $true)

    Write-Header "Starting Intelligence Pipeline"

    # Document Processor (GPU or CPU based on availability)
    if ($UseGPU) {
        Write-Success "Using GPU-accelerated document processor"
        docker compose --profile gpu up -d document-processor
        $dpTimeout = 120
    }
    else {
        Write-Warning "Using CPU-only document processor (slower)"
        docker compose --profile cpu up -d document-processor-cpu
        $dpTimeout = 300
    }

    docker compose up -d universal-router orchestrator

    Wait-ForService "http://localhost:8005/health" "Document Processor" $dpTimeout
    Wait-ForService "http://localhost:8030/health" "Universal Router" 30
    Wait-ForService "http://localhost:8020/health" "Orchestrator" 30

    Write-Success "Pipeline services started"
}

function Start-Workers {
    param([int]$Count = 1)

    Write-Header "Starting Extraction Workers (x$Count)"

    docker compose up -d --scale extraction-worker=$Count extraction-worker
    Start-Sleep -Seconds 5

    Write-Success "$Count worker(s) started"
}

function Start-AudioProcessing {
    Write-Header "Starting Audio Processing"

    docker compose up -d whisperx
    Wait-ForService "http://localhost:9000/health" "WhisperX" 120

    Write-Success "Audio processing started"
}

function Stop-AllServices {
    Write-Header "Stopping All Services"
    docker compose down
    Write-Success "All services stopped"
}

function Initialize-RedisStreams {
    Write-Header "Initializing Redis Streams"

    $streams = @(
        "intake:priority",
        "intake:normal",
        "intake:bulk",
        "extract:documents",
        "extract:images",
        "extract:audio"
    )

    foreach ($stream in $streams) {
        docker exec conductor-redis redis-cli XGROUP CREATE $stream extraction-workers `$ MKSTREAM 2>$null
    }

    Write-Success "Redis Streams initialized"
}

function Show-Status {
    Write-Header "Service Status"
    docker compose ps

    Write-Header "Health Checks"

    $services = @(
        @{Url = "http://localhost:6379"; Name = "Redis"},
        @{Url = "http://localhost:8010/health"; Name = "Conductor API"},
        @{Url = "http://localhost:8040/health"; Name = "Neural Search API"},
        @{Url = "http://localhost:3000/health"; Name = "Mission Control UI"},
        @{Url = "http://localhost:7700/health"; Name = "Meilisearch"},
        @{Url = "http://localhost:9998"; Name = "Tika"},
        @{Url = "http://localhost:8005/health"; Name = "Document Processor"},
        @{Url = "http://localhost:8030/health"; Name = "Universal Router"},
        @{Url = "http://localhost:8020/health"; Name = "Orchestrator"},
        @{Url = "http://localhost:9000/health"; Name = "WhisperX"}
    )

    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            Write-Success $service.Name
        }
        catch {
            Write-Error "$($service.Name) (not responding)"
        }
    }
}

# Main
Write-Header "Neural Vault Pipeline"

if (-not (Test-Docker)) {
    exit 1
}

if ($Stop) {
    Stop-AllServices
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

if ($Minimal) {
    Start-MinimalServices
}
elseif ($GPU) {
    $hasGPU = Test-GPU

    Start-CoreServices
    Start-PipelineServices -UseGPU $hasGPU
    Initialize-RedisStreams
    Start-Workers -Count $Scale

    if ($hasGPU) {
        Start-AudioProcessing
    }
}
else {
    # Full mode
    $hasGPU = Test-GPU

    Start-CoreServices
    Start-PipelineServices -UseGPU $hasGPU
    Initialize-RedisStreams
    Start-Workers -Count $Scale

    if ($hasGPU) {
        Start-AudioProcessing
    }
}

Write-Host ""
Show-Status
