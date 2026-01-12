# Smart Sort & Clean Script (Enterprise Edition)
# Purpose: Move remaining known folders from D: to F: with Audit-Grade Logging

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$LogDir = "F:\conductor\scripts\archive\migration_logs\smart_sort_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$ManifestPath = "$LogDir\move_manifest.csv"

# Create Log Directory
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Initialize Manifest
"Timestamp,Action,Source,Destination,Status,Details" | Out-File -FilePath $ManifestPath -Encoding UTF8

function Write-LogEntry {
    param(
        [string]$Action,
        [string]$Source,
        [string]$Dest,
        [string]$Status,
        [string]$Details
    )
    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$TimeStamp,$Action,$Source,$Dest,$Status,$Details" | Out-File -FilePath $ManifestPath -Append -Encoding UTF8
    $Color = "Red"
    if ($Status -eq "SUCCESS") { $Color = "Green" }
    Write-Host "[$TimeStamp] [$Status] $Action : $Source -> $Dest" -ForegroundColor $Color
}

# Mapping Rules
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

Write-Host "Starting Smart Sort with Audit Logging to: $LogDir" -ForegroundColor Yellow

foreach ($Folder in $Mappings.Keys) {
    $SourcePath = Join-Path $SourceRoot $Folder
    $TargetSubPath = $Mappings[$Folder]
    $TargetPath = Join-Path $TargetRoot $TargetSubPath
    $RoboLog = "$LogDir\robocopy_$($Folder).log"

    if (Test-Path $SourcePath) {
        if (-not (Test-Path $TargetPath)) {
            New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
        }

        # Check if directory or file
        if ((Get-Item $SourcePath) -is [System.IO.DirectoryInfo]) {
            # Execute Robocopy Move (Direct Invocation with Multi-Threading)
            # /MT:32 -> Use 32 Threads (Greatly speeds up small files like assets)
            # /MOVE: Moves files AND dirs
            # /E: Copy empty subdirs
            # Removed /IS to skip identical files (Speed optimization)
            try {
                & robocopy "$SourcePath" "$TargetPath" /E /MOVE /R:3 /W:1 /NP /V /MT:32 /LOG+:"$RoboLog"
                
                # Check LastExitCode (Robocopy uses bitmap)
                # 0 = No errors, no copying
                # 1 = One or more files copied successfully
                # 2 = Extra files or directories were detected
                # 4 = Mismatched files or directories were detected
                # 8 = Some files or directories could not be copied (Retry limit exceeded)
                # 16 = Serious error. Robocopy did not copy any files.
                
                if ($LASTEXITCODE -lt 8) {
                    Write-LogEntry "MOVE_DIR" $SourcePath $TargetPath "SUCCESS" "Moved via Robocopy (Code $LASTEXITCODE)"
                }
                else {
                    Write-LogEntry "MOVE_DIR" $SourcePath $TargetPath "ERROR" "Robocopy Error Code: $LASTEXITCODE"
                }
            }
            catch {
                Write-LogEntry "MOVE_DIR" $SourcePath $TargetPath "ERROR" $_.Exception.Message
            }
        }
        else {
            # Single File Move
            try {
                Move-Item -Path $SourcePath -Destination $TargetPath -Force
                Write-LogEntry "MOVE_FILE" $SourcePath $TargetPath "SUCCESS" "Standard Move-Item"
            }
            catch {
                Write-LogEntry "MOVE_FILE" $SourcePath $TargetPath "ERROR" $_.Exception.Message
            }
        }
    }
    else {
        Write-LogEntry "SKIP" $SourcePath "N/A" "INFO" "Source not found"
    }
}

Write-Host "Operation Complete. Manifest: $ManifestPath" -ForegroundColor Green
Get-Content $ManifestPath | Select-Object -First 10
