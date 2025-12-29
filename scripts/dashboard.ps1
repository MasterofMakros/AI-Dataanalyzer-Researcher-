# Master Migration Dashboard v6 - Docker Style
# Features: Data Rate, Per-Job Progress Bars, Overall Status

$LogDir = "F:\conductor\scripts\archive\migration_logs"

# Adjusted Expected Sizes (GB) based on Verification
$ExpectedSizes = @{
    "merge_mediathek" = 3000
    "merge_backup"    = 960
    "merge_synology"  = 2500
}

function Get-LogStats($LogPath, $ExpectedGB) {
    $result = @{ Name = $null; CopiedGB = 0; Files = 0; Speed = "0.0 MB/s"; Percent = 0; ETA = "?"; IsActive = $false; Bar = "" }
    if (-not (Test-Path $LogPath)) { return $result }
    
    $result.Name = [System.IO.Path]::GetFileNameWithoutExtension($LogPath) -replace "merge_", "" -replace "synology_", "Syn:"
    $item = Get-Item $LogPath
    $result.IsActive = ((Get-Date) - $item.LastWriteTime).TotalSeconds -lt 60
    
    $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
    $result.Files = if ($content) { ([regex]::Matches($content, "Neue Datei")).Count } else { 0 }
    
    # Heuristic: 20MB avg (Mediathek) vs 5MB (others)
    $multiplier = if ($result.Name -match "mediathek") { 0.02 } else { 0.005 }
    $result.CopiedGB = [math]::Round($result.Files * $multiplier, 2)
    
    if ($ExpectedGB -gt 0) {
        $result.Percent = [math]::Min([math]::Round(($result.CopiedGB / $ExpectedGB) * 100), 100)
    }
    else {
        $result.Percent = 0
    }
    
    # Speed Calc
    $logAge = (Get-Date) - $item.CreationTime
    if ($logAge.TotalSeconds -gt 0 -and $result.CopiedGB -gt 0) {
        $speedMBs = [math]::Round(($result.CopiedGB * 1024) / $logAge.TotalSeconds, 1)
        $result.Speed = "$speedMBs MB/s"
        if ($speedMBs -gt 0 -and $result.Percent -lt 100) {
            $remGB = $ExpectedGB - $result.CopiedGB
            $etaMin = [math]::Round(($remGB * 1024) / $speedMBs / 60, 0)
            $result.ETA = "${etaMin}m"
        }
    }
    
    # Progress Bar [####......]
    $barLen = 20
    $filled = [math]::Round(($result.Percent / 100) * $barLen)
    $filled = [math]::Min($filled, $barLen)
    $empty = $barLen - $filled
    $result.Bar = "[" + ("#" * $filled) + ("-" * $empty) + "]"
    
    return $result
}

while ($true) {
    Clear-Host
    Write-Host "===================== MIGRATION PROGRESS =====================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "NAME                           PROGRESS               RATE      ETA    FILES" -ForegroundColor DarkGray
    Write-Host "----------------------------------------------------------------------------" -ForegroundColor DarkGray
    
    $activeLogs = Get-ChildItem "$LogDir\merge_*.log" | Sort-Object LastWriteTime -Descending
    $totalGB = 0
    $totalFiles = 0
    
    foreach ($log in $activeLogs) {
        $nameBase = $log.BaseName -replace "merge_", ""
        $expected = if ($ExpectedSizes.ContainsKey("merge_$nameBase")) { $ExpectedSizes["merge_$nameBase"] } else { 200 }
        
        $stats = Get-LogStats $log.FullName $expected
        $totalGB += $stats.CopiedGB
        $totalFiles += $stats.Files
        
        $col = if ($stats.IsActive) { "Cyan" } else { "Green" }
        
        $line = "{0,-30} {1,-22} {2,-9} {3,-6} {4}" -f 
        $stats.Name.Substring(0, [math]::Min(30, $stats.Name.Length)), 
        "$($stats.Bar) $($stats.Percent)%", 
        $stats.Speed, 
        $stats.ETA,
        $stats.Files
            
        Write-Host $line -ForegroundColor $col
    }
    
    Write-Host ""
    Write-Host "----------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "TOTAL: ~ $([math]::Round($totalGB,2)) GB  |  $totalFiles Files Transferred" -ForegroundColor White
    Write-Host "STATUS: $(if (@(Get-Process | Where-Object ProcessName -match "robocopy").Count -gt 0) { "RUNNING..." } else { "IDLE / COMPLETE" })" -ForegroundColor Yellow
    Write-Host ""
    
    Start-Sleep -Seconds 2
}
