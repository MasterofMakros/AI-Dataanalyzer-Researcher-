# Migration Dashboard v5 - Simple & Reliable
# Uses Clear-Host but with 10s refresh to reduce flicker

$LogDir = "F:\conductor\scripts\archive\migration_logs"

while ($true) {
    Clear-Host
    Write-Host "============== MIGRATION DASHBOARD ==============" -ForegroundColor Cyan
    Write-Host ""
    
    $totalCopied = 0
    $totalExpected = 6000  # ~6TB total expected
    
    # Get all merge logs
    $logs = Get-ChildItem "$LogDir\merge_*.log" -ErrorAction SilentlyContinue | Sort-Object Name
    
    foreach ($log in $logs) {
        $name = $log.BaseName -replace "merge_", "" -replace "synology_", "S:"
        if ($name.Length -gt 35) { $name = $name.Substring(0, 32) + "..." }
        
        $content = Get-Content $log.FullName -Raw -ErrorAction SilentlyContinue
        $files = if ($content) { ([regex]::Matches($content, "Neue Datei")).Count } else { 0 }
        $copiedGB = [math]::Round($files * 0.05, 1)
        $totalCopied += $copiedGB
        
        $isActive = ((Get-Date) - $log.LastWriteTime).TotalSeconds -lt 30
        $status = if ($isActive) { "RUN " } else { "DONE" }
        $color = if ($isActive) { "Yellow" } else { "Green" }
        
        Write-Host "$($name.PadRight(38)) " -NoNewline
        Write-Host "$status" -NoNewline -ForegroundColor $color
        Write-Host " | $($files.ToString().PadLeft(5)) files | $($copiedGB.ToString().PadLeft(6)) GB"
    }
    
    # Summary
    $pct = [math]::Round(($totalCopied / $totalExpected) * 100, 1)
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Magenta
    Write-Host "  TOTAL: $([math]::Round($totalCopied,1)) GB (~$pct%)" -ForegroundColor White
    Write-Host "=================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Last update: $(Get-Date -Format 'HH:mm:ss') | Next in 10s" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds 10
}
</Parameter>
<parameter name="Complexity">2
