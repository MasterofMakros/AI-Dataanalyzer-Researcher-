<#
.SYNOPSIS
    Neural Vault - Live Worker Monitoring
    Real-time view of worker activity and queue progress

.EXAMPLE
    .\monitor_workers.ps1
    .\monitor_workers.ps1 -RefreshSeconds 5
#>

param(
    [int]$RefreshSeconds = 3,
    [switch]$Continuous
)

function Get-QueueStats {
    $queues = @{
        "documents" = @{ stream = "extract:documents"; workers = 4 }
        "images" = @{ stream = "extract:images"; workers = 3 }
        "audio" = @{ stream = "extract:audio"; workers = 2 }
        "video" = @{ stream = "extract:video"; workers = 1 }
        "archive" = @{ stream = "extract:archive"; workers = 1 }
        "email" = @{ stream = "extract:email"; workers = 1 }
        "enrich" = @{ stream = "enrich:ner"; workers = 1 }
    }
    
    $results = @{}
    foreach ($name in $queues.Keys) {
        $stream = $queues[$name].stream
        $len = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $stream 2>$null
        if ($len -match "^\d+$") {
            $results[$name] = @{
                pending = [int]$len
                workers = $queues[$name].workers
            }
        }
    }
    return $results
}

function Get-WorkerActivity {
    $workers = @(
        @{ name = "Documents-1"; container = "ai-dataanalyzer-researcher-worker-documents-1"; color = "Green" }
        @{ name = "Documents-2"; container = "ai-dataanalyzer-researcher-worker-documents-2"; color = "Green" }
        @{ name = "Images-1"; container = "ai-dataanalyzer-researcher-worker-images-1"; color = "Magenta" }
        @{ name = "Audio-1"; container = "ai-dataanalyzer-researcher-worker-audio-1"; color = "Cyan" }
        @{ name = "Video-1"; container = "ai-dataanalyzer-researcher-worker-video-1"; color = "Blue" }
        @{ name = "Archive-1"; container = "ai-dataanalyzer-researcher-worker-archive-1"; color = "DarkYellow" }
    )
    
    $activity = @()
    foreach ($w in $workers) {
        $log = docker logs $w.container --tail 3 2>&1 | Select-Object -Last 1
        if ($log -match '"message":\s*"([^"]+)"') {
            $msg = $Matches[1]
        } elseif ($log -match "Processing:\s*(.+)") {
            $msg = "Processing: " + $Matches[1]
        } else {
            $msg = "Idle"
        }
        
        $activity += @{
            Worker = $w.name
            Status = $msg.Substring(0, [Math]::Min(50, $msg.Length))
            Color = $w.color
        }
    }
    return $activity
}

function Get-IndexStats {
    try {
        $stats = Invoke-RestMethod -Uri "http://127.0.0.1:8010/index/stats" -TimeoutSec 3
        return $stats.numberOfDocuments
    } catch { return "?" }
}

function Show-Dashboard {
    Clear-Host
    
    Write-Host ""
    Write-Host "  =================================================" -ForegroundColor Cyan
    Write-Host "      NEURAL VAULT - LIVE WORKER MONITOR" -ForegroundColor Cyan
    Write-Host "      $(Get-Date -Format 'HH:mm:ss') | Refresh: ${RefreshSeconds}s" -ForegroundColor DarkGray
    Write-Host "  =================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Queue Status
    Write-Host "  QUEUE STATUS" -ForegroundColor Yellow
    Write-Host "  -------------------------------------------------" -ForegroundColor DarkGray
    
    $queues = Get-QueueStats
    $totalPending = 0
    
    foreach ($name in @("documents", "images", "audio", "video", "archive", "email", "enrich")) {
        if ($queues[$name]) {
            $pending = $queues[$name].pending
            $workers = $queues[$name].workers
            $totalPending += $pending
            
            $barLen = [Math]::Min(20, [Math]::Ceiling($pending / 100))
            $bar = "#" * $barLen + "-" * (20 - $barLen)
            
            $color = if ($pending -eq 0) { "DarkGray" } elseif ($pending -gt 500) { "Red" } else { "White" }
            
            Write-Host "  $($name.PadRight(12)) [$bar] " -NoNewline
            Write-Host "$($pending.ToString().PadLeft(5))" -NoNewline -ForegroundColor $color
            Write-Host " ($workers workers)"
        }
    }
    
    Write-Host ""
    Write-Host "  Total Pending: $totalPending" -ForegroundColor White
    Write-Host ""
    
    # Worker Activity
    Write-Host "  WORKER ACTIVITY" -ForegroundColor Yellow
    Write-Host "  -------------------------------------------------" -ForegroundColor DarkGray
    
    $activity = Get-WorkerActivity
    foreach ($a in $activity) {
        Write-Host "  $($a.Worker.PadRight(14)) " -NoNewline
        if ($a.Status -eq "Idle") {
            Write-Host "[Idle]" -ForegroundColor DarkGray
        } else {
            Write-Host "$($a.Status)" -ForegroundColor $a.Color
        }
    }
    
    Write-Host ""
    
    # Index Stats
    $indexCount = Get-IndexStats
    Write-Host "  INDEX: $indexCount documents" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
}

# Main
if ($Continuous) {
    while ($true) {
        Show-Dashboard
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-Dashboard
}
