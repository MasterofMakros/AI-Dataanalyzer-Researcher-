# Migration Master Dashboard v3
# Shows all active merge jobs with progress, data, and ETA

$LogDir = "F:\conductor\scripts\archive\migration_logs"

# Known jobs and their expected sizes (GB)
$ExpectedSizes = @{
    "merge_mediathek" = 2800
    "merge_backup"    = 900
    "merge_synology"  = 2450
}

function Get-LogStats($LogPath, $ExpectedGB) {
    $result = @{
        Name       = [System.IO.Path]::GetFileNameWithoutExtension($LogPath)
        CopiedGB   = 0
        Files      = 0
        Speed      = "N/A"
        Percent    = 0
        ETA        = "?"
        IsActive   = $false
        LastUpdate = $null
    }
    
    if (-not (Test-Path $LogPath)) { return $result }
    
    $item = Get-Item $LogPath
    $result.LastUpdate = $item.LastWriteTime
    $result.IsActive = ((Get-Date) - $item.LastWriteTime).TotalSeconds -lt 30
    
    $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return $result }
    
    # Count files copied
    $result.Files = ([regex]::Matches($content, "Neue Datei")).Count
    
    # Parse bytes copied from log (look for "Bytes" line in summary)
    if ($content -match "Bytes\s*:\s*([\d\s,\.]+)\s+([\d\s,\.]+)") {
        $copiedBytes = $Matches[2] -replace '\s', '' -replace ',', '.'
        try {
            $result.CopiedGB = [math]::Round([double]$copiedBytes / 1GB, 2)
        }
        catch {}
    }
    
    # Estimate from file count if bytes not available
    if ($result.CopiedGB -eq 0 -and $result.Files -gt 0) {
        # Rough estimate: average 5MB per file (better for mixed content)
        $result.CopiedGB = [math]::Round($result.Files * 0.005, 2)
    }
    
    # Calculate percent
    if ($ExpectedGB -gt 0) {
        $result.Percent = [math]::Min([math]::Round(($result.CopiedGB / $ExpectedGB) * 100), 99)
    }
    
    # Calculate speed and ETA based on log file age
    $logAge = (Get-Date) - $item.CreationTime
    if ($logAge.TotalSeconds -gt 0 -and $result.CopiedGB -gt 0) {
        $speedMBs = [math]::Round(($result.CopiedGB * 1024) / $logAge.TotalSeconds, 1)
        $result.Speed = "$speedMBs MB/s"
        
        $remainingGB = $ExpectedGB - $result.CopiedGB
        if ($speedMBs -gt 0) {
            $etaMinutes = [math]::Round(($remainingGB * 1024) / $speedMBs / 60, 0)
            $result.ETA = "$etaMinutes min"
        }
    }
    
    return $result
}

while ($true) {
    Clear-Host
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "              MASTER MIGRATION DASHBOARD v3 - LIVE STATUS                  " -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $jobs = @()
    $totalCopied = 0
    $totalExpected = 0
    
    # Check main merge logs
    @("merge_mediathek", "merge_backup") | ForEach-Object {
        $logPath = "$LogDir\$_.log"
        $expected = $ExpectedSizes[$_]
        $stats = Get-LogStats $logPath $expected
        $jobs += $stats
        $totalCopied += $stats.CopiedGB
        $totalExpected += $expected
    }
    
    # Check Synology sub-logs
    Get-ChildItem "$LogDir\merge_synology_*.log" -ErrorAction SilentlyContinue | ForEach-Object {
        $stats = Get-LogStats $_.FullName 200  # Estimate 200GB per subfolder
        $jobs += $stats
        $totalCopied += $stats.CopiedGB
        $totalExpected += 200
    }
    
    Write-Host "+----------------------------------+--------+----------+----------+----------+" -ForegroundColor DarkGray
    Write-Host "| Job                              | Status | Dateien  | Kopiert  | ETA      |" -ForegroundColor DarkGray
    Write-Host "+----------------------------------+--------+----------+----------+----------+" -ForegroundColor DarkGray
    
    foreach ($job in $jobs) {
        $name = $job.Name
        if ($name.Length -gt 32) { $name = $name.Substring(0, 29) + "..." }
        $name = $name.PadRight(32)
        
        $status = if ($job.IsActive) { "RUN" } else { "DONE" }
        $statusColor = if ($job.IsActive) { "Yellow" } else { "Green" }
        $files = "$($job.Files)".PadLeft(8)
        $copied = "$($job.CopiedGB) GB".PadLeft(8)
        $eta = "$($job.ETA)".PadLeft(8)
        
        Write-Host "| " -NoNewline -ForegroundColor DarkGray
        Write-Host "$name" -NoNewline
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$status".PadRight(6) -NoNewline -ForegroundColor $statusColor
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$files" -NoNewline
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$copied" -NoNewline
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$eta" -NoNewline
        Write-Host " |" -ForegroundColor DarkGray
    }
    
    Write-Host "+----------------------------------+--------+----------+----------+----------+" -ForegroundColor DarkGray
    Write-Host ""
    
    # Overall Summary
    $overallPercent = if ($totalExpected -gt 0) { [math]::Round(($totalCopied / $totalExpected) * 100) } else { 0 }
    $activeCount = ($jobs | Where-Object { $_.IsActive }).Count
    
    Write-Host "============================================================================" -ForegroundColor Magenta
    Write-Host "  GESAMT: $([math]::Round($totalCopied,1)) GB / ~$([math]::Round($totalExpected/1000,1)) TB ($overallPercent%)" -ForegroundColor White
    Write-Host "  Aktive Jobs: $activeCount / $($jobs.Count)" -ForegroundColor White
    Write-Host "============================================================================" -ForegroundColor Magenta
    
    # Progress Bar
    $barWidth = 60
    $visualPercent = [math]::Min($overallPercent, 100)
    $filled = [math]::Round(($visualPercent / 100) * $barWidth)
    $empty = [math]::Max(0, $barWidth - $filled)
    $bar = ("#" * $filled) + ("-" * $empty)
    Write-Host ""
    Write-Host "  [$bar] $overallPercent%" -ForegroundColor $(if ($overallPercent -ge 100) { "Green" } else { "Yellow" })
    
    Write-Host ""
    Write-Host "  Aktualisiert: $(Get-Date -Format 'HH:mm:ss') | Refresh: 3s" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds 3
}
