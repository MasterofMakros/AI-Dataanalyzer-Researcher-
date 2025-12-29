# Enhanced Migration Dashboard v2 - ASCII Version
# Shows per-folder progress with sizes and overall completion

$LogBase = "F:\conductor\scripts\archive\migration_logs"
$LatestDir = Get-ChildItem $LogBase | Where-Object { $_.Name -like "turbo_v5_*" } | Sort-Object CreationTime -Descending | Select-Object -First 1

if (-not $LatestDir) {
    Write-Host "No active v5 migration found!" -ForegroundColor Red
    exit
}

$LogDir = $LatestDir.FullName
Write-Host "Monitoring: $($LatestDir.Name)" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to exit" -ForegroundColor DarkGray
Write-Host ""

function Get-RobocopyLogStats($LogPath) {
    $result = @{
        Name       = [System.IO.Path]::GetFileNameWithoutExtension($LogPath) -replace "robocopy_", ""
        Status     = "Unknown"
        Files      = 0
        Copied     = 0
        Skipped    = 0
        Failed     = 0
        SizeMB     = 0
        LastUpdate = (Get-Item $LogPath).LastWriteTime
        IsActive   = $false
    }
    
    $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return $result }
    
    $result.IsActive = ((Get-Date) - $result.LastUpdate).TotalSeconds -lt 30
    
    # Count "Neue Datei" entries
    $newFiles = ([regex]::Matches($content, "Neue Datei")).Count
    $result.Copied = $newFiles
    $result.Status = if ($result.IsActive) { "AKTIV" } else { "FERTIG" }
    
    # Parse size from log
    $sizeMatches = [regex]::Matches($content, "(\d+\.?\d*)\s*([gmk]?)\s+D:")
    foreach ($m in $sizeMatches) {
        $val = [double]$m.Groups[1].Value
        $unit = $m.Groups[2].Value.ToLower()
        if ($unit -eq "g") { $result.SizeMB += $val * 1024 }
        elseif ($unit -eq "m") { $result.SizeMB += $val }
        elseif ($unit -eq "k") { $result.SizeMB += $val / 1024 }
    }
    $result.SizeMB = [math]::Round($result.SizeMB, 1)
    
    return $result
}

while ($true) {
    Clear-Host
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "           MIGRATION DASHBOARD v2 - DETAILED VIEW                       " -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $logs = Get-ChildItem "$LogDir\*.log" -ErrorAction SilentlyContinue
    $totalCopied = 0
    $totalSizeMB = 0
    $activeJobs = 0
    $completedJobs = 0
    
    Write-Host "+------------------------------------+----------+----------+----------+" -ForegroundColor DarkGray
    Write-Host "| Ordner                             | Status   | Dateien  | Update   |" -ForegroundColor DarkGray
    Write-Host "+------------------------------------+----------+----------+----------+" -ForegroundColor DarkGray
    
    foreach ($log in $logs) {
        $stats = Get-RobocopyLogStats $log.FullName
        
        $name = $stats.Name
        if ($name.Length -gt 34) { $name = $name.Substring(0, 31) + "..." }
        $name = $name.PadRight(34)
        
        $statusColor = if ($stats.IsActive) { "Yellow" } else { "Green" }
        $status = $stats.Status.PadRight(8)
        $files = "$($stats.Copied)".PadLeft(8)
        $lastUpdate = $stats.LastUpdate.ToString("HH:mm:ss")
        
        Write-Host "| " -NoNewline -ForegroundColor DarkGray
        Write-Host "$name" -NoNewline
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$status" -NoNewline -ForegroundColor $statusColor
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$files" -NoNewline
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "$lastUpdate" -NoNewline
        Write-Host " |" -ForegroundColor DarkGray
        
        $totalCopied += $stats.Copied
        $totalSizeMB += $stats.SizeMB
        if ($stats.IsActive) { $activeJobs++ } else { $completedJobs++ }
    }
    
    Write-Host "+------------------------------------+----------+----------+----------+" -ForegroundColor DarkGray
    Write-Host ""
    
    # Overall Summary
    $totalGB = [math]::Round($totalSizeMB / 1024, 2)
    $pctComplete = if ($logs.Count -gt 0) { [math]::Round(($completedJobs / $logs.Count) * 100) } else { 0 }
    
    Write-Host "========================================================================" -ForegroundColor Magenta
    Write-Host "  GESAMT                                                                " -ForegroundColor Magenta
    Write-Host "========================================================================" -ForegroundColor Magenta
    Write-Host "  Jobs:          $completedJobs / $($logs.Count) abgeschlossen ($activeJobs aktiv)" -ForegroundColor White
    Write-Host "  Dateien:       $totalCopied kopiert" -ForegroundColor White
    Write-Host "  Datenvolumen:  $totalGB GB" -ForegroundColor White
    Write-Host "  Fortschritt:   $pctComplete%" -ForegroundColor White
    Write-Host "========================================================================" -ForegroundColor Magenta
    
    # Visual Progress Bar (ASCII)
    $barWidth = 50
    $filled = [math]::Round(($pctComplete / 100) * $barWidth)
    $empty = $barWidth - $filled
    $bar = ("#" * $filled) + ("-" * $empty)
    Write-Host ""
    $barColor = if ($pctComplete -eq 100) { "Green" } else { "Yellow" }
    Write-Host "  [$bar] $pctComplete%" -ForegroundColor $barColor
    
    Write-Host ""
    Write-Host "  Letzte Aktualisierung: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds 2
}
