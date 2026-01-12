# Smart Sort & Clean Script (Safe Mode with Hashing)
# Purpose: Move folders/files with hash-based conflict resolution and detailed CSV logging.

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$LogDir = "F:\conductor\scripts\archive\migration_logs\smart_sort_safe_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$ManifestPath = "$LogDir\transfer_manifest.csv"

# Create Log Directory
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Initialize CSV Header (LLM Friendly: Concise columns)
"Time,Result,Type,SourceFile,ConflictInfo" | Out-File -FilePath $ManifestPath -Encoding UTF8

function Write-Log {
    param($Result, $Type, $SourceFile, $ConflictInfo = "")
    $Time = Get-Date -Format "HH:mm:ss"
    "$Time,$Result,$Type,$SourceFile,$ConflictInfo" | Out-File -FilePath $ManifestPath -Append -Encoding UTF8
    
    $Color = "Green"
    if ($Result -match "CONFLICT|ERROR") { $Color = "Yellow" }
    if ($Result -match "FAIL") { $Color = "Red" }
    Write-Host "[$Time] $Result : $SourceFile $ConflictInfo" -ForegroundColor $Color
}

function Get-FileHashFast {
    param($Path)
    try {
        # SHA256 is standard, MD5 is faster but SHA256 is preferred for "AI Stack" integrity
        return (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    }
    catch {
        return $null
    }
}

function Move-Safe {
    param($Source, $DestinationParent)
    
    if (-not (Test-Path $DestinationParent)) {
        New-Item -ItemType Directory -Path $DestinationParent -Force | Out-Null
    }

    $FileName = Split-Path $Source -Leaf
    $DestPath = Join-Path $DestinationParent $FileName

    # Case 1: Target does not exist -> Fast Move
    if (-not (Test-Path $DestPath)) {
        try {
            Move-Item -Path $Source -Destination $DestPath -Force -ErrorAction Stop
            Write-Log "MOVED" "File" $FileName
        }
        catch {
            Write-Log "FAIL" "File" $FileName $_.Exception.Message
        }
        return
    }

    # Case 2: Target exists -> Conflict Resolution
    $SrcHash = Get-FileHashFast $Source
    $DestHash = Get-FileHashFast $DestPath

    if ($SrcHash -eq $DestHash) {
        # Identical Content -> Delete Source (Moved)
        Remove-Item -Path $Source -Force
        Write-Log "SKIPPED" "File" $FileName "Hash Match (Identical)"
    }
    else {
        # Different Content -> Rename Source and Move
        $Extension = [System.IO.Path]::GetExtension($Source)
        $BaseName = [System.IO.Path]::GetFileNameWithoutExtension($Source)
        $NewName = "${BaseName}_CONFLICT_$(Get-Date -Format 'yyyyMMddHHmmss')${Extension}"
        $NewDestPath = Join-Path $DestinationParent $NewName
        
        try {
            Move-Item -Path $Source -Destination $NewDestPath -Force
            Write-Log "RESOLVED" "File" $FileName "Renamed to $NewName (Hash Mismatch)"
        }
        catch {
            Write-Log "FAIL" "File" $FileName "Rename Failed: $($_.Exception.Message)"
        }
    }
}

# Recursively Process Folders
function Invoke-FolderProcessing {
    param($SrcDir, $TargetDir)
    
    # Get all files recursively
    $Files = Get-ChildItem -Path $SrcDir -Recurse -File
    
    foreach ($File in $Files) {
        # Calculate relative path to preserve subfolder structure
        $RelPath = $File.DirectoryName.Substring($SrcDir.Length)
        if ($RelPath.StartsWith("\")) { $RelPath = $RelPath.Substring(1) }
        
        $CurrentTargetDir = Join-Path $TargetDir $RelPath
        
        Move-Safe $File.FullName $CurrentTargetDir
    }
    
    # Cleanup Empty Folders in Source
    Get-ChildItem -Path $SrcDir -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
        if ((Get-ChildItem -Path $_.FullName | Measure-Object).Count -eq 0) {
            Remove-Item -Path $_.FullName -Force
        }
    }
}

# --- Mapping Configuration ---
# Update GSG_Assets to correct target
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

Write-Host "Starting Safe Sort with Hashing..." -ForegroundColor Magenta

foreach ($Folder in $Mappings.Keys) {
    $SourcePath = Join-Path $SourceRoot $Folder
    $TargetSubPath = $Mappings[$Folder]
    $TargetPath = Join-Path $TargetRoot $TargetSubPath

    if (Test-Path $SourcePath) {
        if ((Get-Item $SourcePath) -is [System.IO.DirectoryInfo]) {
            Write-Host "Processing Directory: $SourcePath" -ForegroundColor Cyan
            Invoke-FolderProcessing $SourcePath $TargetPath
        }
        else {
            # Single File
            Move-Safe $SourcePath (Split-Path $TargetPath -Parent)
        }
        
        # Try to remove root source folder if empty
        if ((Test-Path $SourcePath) -and (Get-ChildItem $SourcePath | Measure-Object).Count -eq 0) {
            Remove-Item $SourcePath -Force
        }
    }
}

Write-Host "Done. Manifest at: $ManifestPath" -ForegroundColor Green
