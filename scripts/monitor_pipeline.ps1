# Real-Time Pipeline Monitoring Script
# Usage: .\scripts\monitor_pipeline.ps1

Write-Host "=== ANTIGRAVITY PIPELINE MONITOR ===" -ForegroundColor Cyan
Write-Host "Monitoring all services in real-time..." -ForegroundColor Yellow
Write-Host ""

# Create a synchronized hashtable for output
$script:LogBuffer = [System.Collections.ArrayList]::Synchronized((New-Object System.Collections.ArrayList))

# Function to format and display log entry
function Write-ServiceLog {
    param(
        [string]$Service,
        [string]$Message,
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss.fff"
    $formatted = "[$timestamp] [$Service] $Message"
    Write-Host $formatted -ForegroundColor $Color
}

# Start background jobs for each service
Write-Host "Starting monitors for:" -ForegroundColor Green
Write-Host "  - Perplexica (Frontend/Backend)"
Write-Host "  - Conductor API (Neural Vault)"
Write-Host "  - Ollama (LLM)"
Write-Host "  - Qdrant (Vector DB)"
Write-Host ""
Write-Host "Press CTRL+C to stop monitoring" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Monitor Perplexica
Start-Job -Name "Perplexica" -ScriptBlock {
    docker logs -f conductor-perplexica 2>&1 | ForEach-Object {
        if ($_ -match "POST|GET|ERROR|search|query") {
            [PSCustomObject]@{
                Service = "PERPLEXICA"
                Message = $_
                Color = if ($_ -match "ERROR") { "Red" } elseif ($_ -match "POST|search") { "Cyan" } else { "Gray" }
            }
        }
    }
} | Out-Null

# Monitor Conductor API
Start-Job -Name "ConductorAPI" -ScriptBlock {
    docker logs -f conductor-api 2>&1 | ForEach-Object {
        if ($_ -match "POST|GET|ERROR|search|qdrant|embedding") {
            [PSCustomObject]@{
                Service = "API"
                Message = $_
                Color = if ($_ -match "ERROR") { "Red" } elseif ($_ -match "search|qdrant") { "Green" } else { "Gray" }
            }
        }
    }
} | Out-Null

# Monitor Ollama
Start-Job -Name "Ollama" -ScriptBlock {
    docker logs -f conductor-ollama 2>&1 | ForEach-Object {
        if ($_ -match "POST|llama|generate|embedding") {
            [PSCustomObject]@{
                Service = "OLLAMA"
                Message = $_
                Color = "Magenta"
            }
        }
    }
} | Out-Null

# Monitor Qdrant
Start-Job -Name "Qdrant" -ScriptBlock {
    docker logs -f conductor-qdrant 2>&1 | ForEach-Object {
        if ($_ -match "search|query|points|collection") {
            [PSCustomObject]@{
                Service = "QDRANT"
                Message = $_
                Color = "Yellow"
            }
        }
    }
} | Out-Null

# Main monitoring loop
try {
    while ($true) {
        # Collect logs from all jobs
        $jobs = Get-Job | Where-Object { $_.State -eq "Running" }
        
        foreach ($job in $jobs) {
            $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
            
            foreach ($entry in $output) {
                if ($entry) {
                    Write-ServiceLog -Service $entry.Service -Message $entry.Message -Color $entry.Color
                }
            }
        }
        
        Start-Sleep -Milliseconds 100
    }
} finally {
    # Cleanup
    Write-Host "`n`nStopping monitors..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "Monitoring stopped." -ForegroundColor Green
}
