# Migration Dashboard v4 - Flicker-Free
# Uses cursor positioning to update values in place

$LogDir = "F:\conductor\scripts\archive\migration_logs"

$ExpectedSizes = @{
    "merge_mediathek" = 2800
    "merge_backup"    = 900
}

function Get-LogStats($LogPath, $ExpectedGB) {
    $result = @{ CopiedGB = 0; Files = 0; Percent = 0; ETA = "?"; IsActive = $false }
    if (-not (Test-Path $LogPath)) { return $result }
    
    $item = Get-Item $LogPath
    $result.IsActive = ((Get-Date) - $item.LastWriteTime).TotalSeconds -lt 30
    
    $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return $result }
    
    $result.Files = ([regex]::Matches($content, "Neue Datei")).Count
    if ($result.Files -gt 0) { $result.CopiedGB = [math]::Round($result.Files * 0.05, 2) }
    if ($ExpectedGB -gt 0) { $result.Percent = [math]::Min([math]::Round(($result.CopiedGB / $ExpectedGB) * 100), 99) }
    
    $logAge = (Get-Date) - $item.CreationTime
    if ($logAge.TotalSeconds -gt 0 -and $result.CopiedGB -gt 0) {
        $speedMBs = [math]::Round(($result.CopiedGB * 1024) / $logAge.TotalSeconds, 1)
        $remainingGB = $ExpectedGB - $result.CopiedGB
        if ($speedMBs -gt 0) { $result.ETA = "$([math]::Round(($remainingGB * 1024) / $speedMBs / 60, 0))m" }
    }
    return $result
}

# Draw static frame once
Clear-Host
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "              MASTER MIGRATION DASHBOARD v4 - LIVE                         " -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "+----------------------------------+--------+----------+----------+----------+"
Write-Host "| Job                              | Status | Dateien  | Kopiert  | ETA      |"
Write-Host "+----------------------------------+--------+----------+----------+----------+"

# Row positions (line numbers for each job)
$rowStart = 7
$jobs = @("merge_mediathek", "merge_backup")
$synologyLogs = @()

# Draw initial rows
foreach ($i in 0..($jobs.Count - 1)) {
    Write-Host "| $($jobs[$i].PadRight(32)) |        |          |          |          |"
}

# Synology placeholder rows
Write-Host "| synology_* jobs below...         |        |          |          |          |"
$synologyRowStart = $rowStart + $jobs.Count + 1

for ($s = 0; $s -lt 15; $s++) {
    Write-Host "|                                  |        |          |          |          |"
}

Write-Host "+----------------------------------+--------+----------+----------+----------+"
$summaryRow = $synologyRowStart + 15 + 1
Write-Host ""
Write-Host "  GESAMT:                                                                      "
Write-Host "  Fortschritt: [------------------------------------------------------------]  "
Write-Host ""
Write-Host "  Aktualisiert:                                                                "

# Update loop
while ($true) {
    $totalCopied = 0
    $totalExpected = 0
    
    # Update main jobs
    foreach ($i in 0..($jobs.Count - 1)) {
        $jobName = $jobs[$i]
        $logPath = "$LogDir\$jobName.log"
        $expected = $ExpectedSizes[$jobName]
        $stats = Get-LogStats $logPath $expected
        
        $totalCopied += $stats.CopiedGB
        $totalExpected += $expected
        
        $status = if ($stats.IsActive) { "RUN" } else { "DONE" }
        $statusColor = if ($stats.IsActive) { "Yellow" } else { "Green" }
        
        [Console]::SetCursorPosition(35, $rowStart + $i)
        Write-Host "$status   " -NoNewline -ForegroundColor $statusColor
        [Console]::SetCursorPosition(44, $rowStart + $i)
        Write-Host "$($stats.Files)".PadLeft(8) -NoNewline
        [Console]::SetCursorPosition(55, $rowStart + $i)
        Write-Host "$($stats.CopiedGB) GB".PadLeft(8) -NoNewline
        [Console]::SetCursorPosition(66, $rowStart + $i)
        Write-Host "$($stats.ETA)".PadLeft(8) -NoNewline
    }
    
    # Update Synology sub-jobs
    $synologyLogs = Get-ChildItem "$LogDir\merge_synology_*.log" -ErrorAction SilentlyContinue
    $sIdx = 0
    foreach ($log in $synologyLogs) {
        if ($sIdx -ge 15) { break }
        $stats = Get-LogStats $log.FullName 200
        $totalCopied += $stats.CopiedGB
        $totalExpected += 200
        
        $name = $log.BaseName -replace "merge_synology_", ""
        if ($name.Length -gt 32) { $name = $name.Substring(0, 29) + "..." }
        
        $status = if ($stats.IsActive) { "RUN" } else { "DONE" }
        $statusColor = if ($stats.IsActive) { "Yellow" } else { "Green" }
        
        [Console]::SetCursorPosition(2, $synologyRowStart + $sIdx)
        Write-Host $name.PadRight(32) -NoNewline
        [Console]::SetCursorPosition(35, $synologyRowStart + $sIdx)
        Write-Host "$status   " -NoNewline -ForegroundColor $statusColor
        [Console]::SetCursorPosition(44, $synologyRowStart + $sIdx)
        Write-Host "$($stats.Files)".PadLeft(8) -NoNewline
        [Console]::SetCursorPosition(55, $synologyRowStart + $sIdx)
        Write-Host "$($stats.CopiedGB) GB".PadLeft(8) -NoNewline
        [Console]::SetCursorPosition(66, $synologyRowStart + $sIdx)
        Write-Host "$($stats.ETA)".PadLeft(8) -NoNewline
        
        $sIdx++
    }
    
    # Update summary
    $overallPercent = if ($totalExpected -gt 0) { [math]::Round(($totalCopied / $totalExpected) * 100) } else { 0 }
    
    [Console]::SetCursorPosition(10, $summaryRow)
    Write-Host "$([math]::Round($totalCopied,1)) GB / ~$([math]::Round($totalExpected/1000,1)) TB ($overallPercent%)".PadRight(50) -NoNewline
    
    # Progress bar
    $barWidth = 60
    $filled = [math]::Round(($overallPercent / 100) * $barWidth)
    $bar = ("#" * $filled) + ("-" * ($barWidth - $filled))
    [Console]::SetCursorPosition(16, $summaryRow + 1)
    Write-Host $bar -NoNewline -ForegroundColor $(if ($overallPercent -ge 100) { "Green" } else { "Yellow" })
    
    # Timestamp
    [Console]::SetCursorPosition(16, $summaryRow + 3)
    Write-Host "$(Get-Date -Format 'HH:mm:ss')   " -NoNewline
    
    Start-Sleep -Seconds 5
}
