$ErrorActionPreference = "Stop"

function Write-Status {
    param($Message)
    Write-Host "[CONDUCTOR] $Message" -ForegroundColor Cyan
}

function Check-Docker {
    Write-Status "Checking Docker status..."
    try {
        docker ps > $null 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Docker daemon not reachable" }
        Write-Host "✅ Docker is running." -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Docker is NOT running." -ForegroundColor Red
        return $false
    }
}

function Start-Docker {
    Write-Status "Attempting to start Docker Desktop..."
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        Write-Status "Waiting for Docker to initialize (this may take a minute)..."
        
        # Wait up to 60 seconds
        for ($i=0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 2
            if (Check-Docker) { return $true }
            Write-Host "." -NoNewline
        }
    } else {
        Write-Error "Docker Desktop not found at default location: $dockerPath"
    }
    return $false
}

# --- Main Sequence ---

# 1. Check/Start Docker
if (-not (Check-Docker)) {
    if (-not (Start-Docker)) {
        Write-Error "Could not start Docker. Please start Docker Desktop manually."
        exit 1
    }
}

# 2. Check Directories
$conductorRoot = "F:\conductor"
if (-not (Test-Path $conductorRoot)) {
    Write-Error "Conductor root not found at $conductorRoot"
    exit 1
}

Set-Location $conductorRoot

# 3. Check .env
if (-not (Test-Path ".env")) {
    Write-Warning ".env file missing! Creating from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️ Created .env - please check configuration!" -ForegroundColor Yellow
}

# 4. Start Stack
Write-Status "Starting Neural Vault Stack..."
docker-compose up -d

# 5. Wait for key services
Write-Status "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# 6. Check Ollama
$ollamaUrl = "http://localhost:11435"
try {
    $response = Invoke-WebRequest -Uri "$ollamaUrl/api/tags" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Ollama is ready at $ollamaUrl" -ForegroundColor Green
    }
} catch {
    Write-Warning "⚠️ Ollama is not yet responding at $ollamaUrl. It might still be pulling the model."
    Write-Host "You can check status with: docker logs -f conductor-ollama"
}

Write-Status "startup complete!"
Write-Host "You can now run the UI: python scripts/search_ui.py" -ForegroundColor Green
