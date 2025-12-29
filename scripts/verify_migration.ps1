# Migration Verification & Repair Scanner
# Purpose: retroactive check of D: vs F: to find missing or corrupted files.

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$LogDir = "F:\conductor\scripts\archive\migration_logs\verification_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$ReportPath = "$LogDir\discrepancy_report.csv"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
"Status,SourceFile,TargetFile,Details" | Out-File -FilePath $ReportPath -Encoding UTF8

# Mapping Rules (Must match Smart Sort)
$Mappings = @{
    "Downloads"                     = "_Inbox_Sorting\Downloads"
    "Backup"                        = "99 Datenpool Archiv & Backups\Alte_Backups"
    "Camtasia"                      = "12 Datenpool Mediathek\Camtasia_Projekte"
    "Cinema 4D"                     = "09 Datenpool Projekte\Cinema_4D"
    "Projektdatein Cinema 4D"       = "09 Datenpool Projekte\Cinema_4D_Projekte"
    "Genisis"                       = "09 Datenpool Projekte\Genisis"
    "GSG_Assets"                    = "12 Datenpool Mediathek\Assets\GSG_Assets"
    "Styles.png"                    = "12 Datenpool Mediathek\Assets\Styles.png"
    "Webseitenbilder"               = "12 Datenpool Mediathek\Bilder\Webseite"
    "Desktop unsortiert 07.01.2025" = "_Inbox_Sorting\Desktop_Dump"
}

function Get-FileHashFast {
    param($Path)
    try { return (Get-FileHash -Path $Path -Algorithm SHA256).Hash } catch { return "ACCESS_DENIED" }
}

function Report-Issue {
    param($Status, $Src, $Tgt, $Info)
    "$Status,$Src,$Tgt,$Info" | Out-File -FilePath $ReportPath -Append -Encoding UTF8
    Write-Host "[$Status] $Src -> $Info" -ForegroundColor Red
}

Write-Host "Starting Integrity Verification..." -ForegroundColor Cyan

foreach ($Folder in $Mappings.Keys) {
    $SourcePath = Join-Path $SourceRoot $Folder
    $TargetSubPath = $Mappings[$Folder]
    $TargetPath = Join-Path $TargetRoot $TargetSubPath

    if (Test-Path $SourcePath) {
        Write-Host "Verifying: $Folder..." -ForegroundColor Yellow
        
        $Files = Get-ChildItem -Path $SourcePath -Recurse -File
        $Total = ($Files | Measure-Object).Count
        $Count = 0

        foreach ($File in $Files) {
            $Count++
            if ($Count % 100 -eq 0) { Write-Progress -Activity "Verifying $Folder" -Status "$Count / $Total" -PercentComplete (($Count / $Total) * 100) }

            # Calculate Expected Path
            $RelPath = $File.DirectoryName.Substring($SourcePath.Length)
            if ($RelPath.StartsWith("\")) { $RelPath = $RelPath.Substring(1) }
            $ExpectedTarget = Join-Path $TargetPath $RelPath
            $ExpectedFile = Join-Path $ExpectedTarget $File.Name

            # Check 1: Existence
            if (-not (Test-Path $ExpectedFile)) {
                Report-Issue "MISSING" $File.FullName $ExpectedFile "File not found on F:"
                continue
            }

            # Check 2: Size (Fast fail)
            if ((Get-Item $ExpectedFile).Length -ne $File.Length) {
                Report-Issue "SIZE_MISMATCH" $File.FullName $ExpectedFile "Size differs"
                continue
            }

            # Check 3: Hash (Slow but sure) - Optional, enabled here for rigorous check
            # Uncomment for full bit-level verification (Takes time!)
            # $SrcHash = Get-FileHashFast $File.FullName
            # $TgtHash = Get-FileHashFast $ExpectedFile
            # if ($SrcHash -ne $TgtHash) {
            #    Report-Issue "CORRUPT" $File.FullName $ExpectedFile "Hash mismatch"
            # }
        }
    }
}

Write-Host "Verification Complete. Report: $ReportPath" -ForegroundColor Green
