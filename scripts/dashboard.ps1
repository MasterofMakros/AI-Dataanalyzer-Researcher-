# Migration Live Dashboard
# Reads logs from latest smart_copy_v4 session to visualize progress

$LogBase = "F:\conductor\scripts\archive\migration_logs"
$LatestDir = Get-ChildItem $LogBase | Where-Object { $_.Name -like "safe_copy_v4_*" } | Sort-Object CreationTime -Descending | Select-Object -First 1

if (-not $LatestDir) {
    Write-Host "No active v4 migration found!" -ForegroundColor Red
    exit
}

$SuccessLog = "$($LatestDir.FullName)\success.log"
$ErrorLog = "$($LatestDir.FullName)\errors.csv"

Write-Host "Monitoring: $($LatestDir.Name)" -ForegroundColor Cyan
Start-Sleep -Seconds 2

$StartTime = Get-Date

# Estimation (Total files on D: approx - based on previous scan)
$TotalEstimated = 150000 
# Note: Accurate total is hard without pre-scan, using estimate based on known large folders.
# If v4 script outputs "Total" in logs, we could parse that, but v4 prints to console which we can't read easily from outside.

while ($true) {
    if (Test-Path $SuccessLog) {
        $SuccessCount = (Get-Content $SuccessLog -ErrorAction SilentlyContinue).Count
        $ErrorCount = if (Test-Path $ErrorLog) { (Get-Content $ErrorLog -ErrorAction SilentlyContinue).Count - 1 } else { 0 }
        
        # Calculate Speed
        $Now = Get-Date
        $Elapsed = ($Now - $StartTime).TotalSeconds
        $Speed = if ($Elapsed -gt 0) { [math]::Round($SuccessCount / $Elapsed, 1) } else { 0 }
        
        # Current File (Last line)
        $LastFile = Get-Content $SuccessLog -Tail 1 -ErrorAction SilentlyContinue
        
        # Percentage (Capped at 99% if we exceed estimate)
        $Percent = [math]::Min([math]::Round(($SuccessCount / $TotalEstimated) * 100), 99)
        
        # ETA
        $Remaining = $TotalEstimated - $SuccessCount
        $ETASeconds = if ($Speed -gt 0) { $Remaining / $Speed } else { 0 }

        # Dashboard UI
        Clear-Host
        Write-Host "=== MIGRATION LIVE DASHBOARD ===" -ForegroundColor Magenta
        Write-Host "Time Running:   $([math]::Round($Elapsed/60, 1)) min"
        Write-Host "Speed:          $Speed files/sec"
        Write-Host "Progress:       $Percent % (Est.)"
        Write-Host "Copied:         $SuccessCount / $TotalEstimated (Est)"
        Write-Host "Errors:         $ErrorCount" -ForegroundColor $(if ($ErrorCount -gt 0) { "Red" } else { "Green" })
        Write-Host ""
        Write-Host "Current File:   $LastFile" -ForegroundColor Yellow
        
        # Visual Bar
        Write-Progress -Activity "Migrating Data..." -Status "$Percent% Complete ($Speed f/s)" -PercentComplete $Percent -CurrentOperation "Copying: $LastFile" -SecondsRemaining $ETASeconds
    }
    
    Start-Sleep -Seconds 1
}
