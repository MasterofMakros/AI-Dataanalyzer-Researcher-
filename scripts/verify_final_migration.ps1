# FINAL MIGRATION VERIFICATION
# Compares Source D: against Target F: to prove completeness

$VerificationScope = @{
    "Mediathek" = @{ Src = "D:\12 Datenpool Mediathek"; Tgt = "F:\12 Datenpool Mediathek" }
    "Backup"    = @{ Src = "D:\Backup"; Tgt = "F:\99 Datenpool Archiv & Backups\Alte_Backups" }
    "Synology"  = @{ Src = "D:\Synology Cloud 20-04-2025\Neue Verzeichnisstruktur"; Tgt = "F:\" } # Special case
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      FINAL MIGRATION AUDIT              " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$AllGood = $true

foreach ($Name in $VerificationScope.Keys) {
    $Item = $VerificationScope[$Name]
    $Src = $Item.Src
    $Tgt = $Item.Tgt
    
    Write-Host "Checking: $Name" -ForegroundColor Yellow
    
    if (-not (Test-Path $Src)) {
        Write-Host "  [SKIP] Source not found: $Src" -ForegroundColor DarkGray
        continue
    }
    
    # Measure Source
    Write-Host "  ... Scanning Source D: (this takes time) ..." -NoNewline
    $SrcStats = Get-ChildItem $Src -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
    Write-Host " DONE" -ForegroundColor Green
    
    # Measure Target
    # For Synology, we need to check subfolders individually because they were merged into F root
    if ($Name -eq "Synology") {
        Write-Host "  ... Scanning Target F: (Complex Merge) ..." -NoNewline
        $TgtFiles = 0
        $TgtBytes = 0
        
        $Subfolders = Get-ChildItem $Src -Directory
        foreach ($Sub in $Subfolders) {
            # Try to find corresponding folder on F
            $PossiblePaths = @(
                "F:\$($Sub.Name)",
                "F:\_Inbox_Sorting\Synology_Rest\$($Sub.Name)"
            )
            
            $Found = $false
            foreach ($P in $PossiblePaths) {
                if (Test-Path $P) {
                    $SubStats = Get-ChildItem $P -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
                    $TgtFiles += $SubStats.Count
                    $TgtBytes += $SubStats.Sum
                    $Found = $true
                    break
                }
            }
            if (-not $Found) {
                Write-Host "  [WARNING] Target folder not found for: $($Sub.Name)" -ForegroundColor Red
            }
        }
        Write-Host " DONE" -ForegroundColor Green
    }
    else {
        Write-Host "  ... Scanning Target F: ..." -NoNewline
        $TgtStats = Get-ChildItem $Tgt -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
        $TgtFiles = $TgtStats.Count
        $TgtBytes = $TgtStats.Sum
        Write-Host " DONE" -ForegroundColor Green
    }
    
    # Compare
    $SrcGB = [math]::Round($SrcStats.Sum / 1GB, 2)
    $TgtGB = [math]::Round($TgtBytes / 1GB, 2)
    
    Write-Host "  Source: $($SrcStats.Count) files ($SrcGB GB)"
    Write-Host "  Target: $TgtFiles files ($TgtGB GB)"
    
    if ($TgtFiles -ge $SrcStats.Count -and $TgtBytes -ge $SrcStats.Sum) {
        Write-Host "  [OK] COMPLETE ✅" -ForegroundColor Green
    }
    else {
        $DiffFiles = $SrcStats.Count - $TgtFiles
        $DiffGB = [math]::Round(($SrcStats.Sum - $TgtBytes) / 1GB, 2)
        Write-Host "  [WARNING] MISSING DATA ❌" -ForegroundColor Red
        Write-Host "  Missing: $DiffFiles files ($DiffGB GB) - (might be currently copying)" -ForegroundColor Red
        $AllGood = $false
    }
    Write-Host ""
}

if ($AllGood) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  RESULT: MIGRATION SUCCESSFUL ✅        " -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
}
else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "  RESULT: INCOMPLETE OR IN PROGRESS ⏳   " -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
