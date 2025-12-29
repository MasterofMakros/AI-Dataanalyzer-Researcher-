# Smart Copy v2.0 - With Checkpoint & Statistics
# Features: Resume capability, Summary report, Better progress tracking

param(
    [switch]$Resume,       # Continue from checkpoint
    [switch]$DryRun        # Show what would happen without copying
)

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogDir = "F:\conductor\scripts\archive\migration_logs\safe_copy_v2_$Timestamp"

# Checkpoint file (for resume)
$CheckpointFile = "F:\conductor\scripts\checkpoint.json"

# Statistics
$Stats = @{
    StartTime     = Get-Date
    TotalFiles    = 0
    CopiedFiles   = 0
    SkippedFiles  = 0
    ConflictFiles = 0
    ErrorFiles    = 0
    TotalBytes    = 0
    CopiedBytes   = 0
}

# Initialize
if (-not $Resume) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$ErrorLog = "$LogDir\errors.csv"
$SuccessLog = "$LogDir\success.log"
$SummaryFile = "$LogDir\summary.json"

if (-not $Resume) {
    "Time,File,Error" | Out-File $ErrorLog -Encoding UTF8
    "[START] $Timestamp" | Out-File $SuccessLog -Encoding UTF8
}

# Checkpoint Functions
function Save-Checkpoint($CurrentFolder, $CurrentIndex) {
    @{
        LogDir        = $LogDir
        CurrentFolder = $CurrentFolder
        CurrentIndex  = $CurrentIndex
        Stats         = $Stats
        Timestamp     = (Get-Date).ToString()
    } | ConvertTo-Json | Out-File $CheckpointFile -Encoding UTF8
}

function Get-Checkpoint {
    if (Test-Path $CheckpointFile) {
        return Get-Content $CheckpointFile | ConvertFrom-Json
    }
    return $null
}

function Remove-Checkpoint {
    if (Test-Path $CheckpointFile) {
        Remove-Item $CheckpointFile -Force
    }
}

# Logging
function Write-ErrorEntry($File, $Msg) {
    "$(Get-Date -Format 'HH:mm:ss'),$File,$Msg" | Out-File $ErrorLog -Append -Encoding UTF8
    $Stats.ErrorFiles++
}

function Write-SuccessEntry($File, $Bytes) {
    $File | Out-File $SuccessLog -Append -Encoding UTF8
    $Stats.CopiedFiles++
    $Stats.CopiedBytes += $Bytes
}

# Hash
function Get-FastHash($Path) {
    try { return (Get-FileHash $Path -Algorithm MD5).Hash } catch { return $null }
}

# Copy Logic
function Copy-SafeFile($Src, $DestParent) {
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would copy: $Src" -ForegroundColor Cyan
        return
    }
    
    if (-not (Test-Path $DestParent)) {
        New-Item -ItemType Directory -Path $DestParent -Force | Out-Null
    }
    
    $Name = Split-Path $Src -Leaf
    $Dest = Join-Path $DestParent $Name
    $Size = (Get-Item $Src -ErrorAction SilentlyContinue).Length
    
    # Fast path
    if (-not (Test-Path $Dest)) {
        try {
            Copy-Item $Src $Dest -Force -ErrorAction Stop
            Write-SuccessEntry $Name $Size
        }
        catch {
            Write-ErrorEntry $Name $_.Exception.Message
        }
        return
    }
    
    # Conflict check
    $SrcHash = Get-FastHash $Src
    $DestHash = Get-FastHash $Dest
    
    if ($SrcHash -eq $DestHash) {
        $Stats.SkippedFiles++
        return
    }
    
    # Resolve conflict
    $Ext = [IO.Path]::GetExtension($Name)
    $Base = [IO.Path]::GetFileNameWithoutExtension($Name)
    $NewName = "${Base}_CONFLICT_$Timestamp$Ext"
    $NewDest = Join-Path $DestParent $NewName
    
    try {
        Copy-Item $Src $NewDest -Force
        Write-SuccessEntry "$Name -> $NewName" $Size
        $Stats.ConflictFiles++
    }
    catch {
        Write-ErrorEntry $Name "Conflict copy failed: $($_.Exception.Message)"
    }
}

# Process Directory
function Copy-Directory($SrcDir, $TgtDir, $UseHeuristic, $StartIndex = 0) {
    $Files = @(Get-ChildItem $SrcDir -Recurse -File -ErrorAction SilentlyContinue)
    $Total = $Files.Count
    $Stats.TotalFiles += $Total
    
    for ($i = $StartIndex; $i -lt $Total; $i++) {
        $F = $Files[$i]
        $Stats.TotalBytes += $F.Length
        
        # Progress
        if ($i % 100 -eq 0) {
            $Pct = [math]::Round(($i / $Total) * 100, 1)
            $Elapsed = (Get-Date) - $Stats.StartTime
            $Rate = if ($Elapsed.TotalSeconds -gt 0) { $i / $Elapsed.TotalSeconds } else { 0 }
            $ETA = if ($Rate -gt 0) { [math]::Round(($Total - $i) / $Rate / 60, 1) } else { "?" }
            
            Write-Host "[$Pct%] $i/$Total | Rate: $([math]::Round($Rate,1))/s | ETA: ${ETA}min" -ForegroundColor Yellow
            
            # Save checkpoint every 500 files
            if ($i % 500 -eq 0) {
                Save-Checkpoint $SrcDir $i
            }
        }
        
        # Target path
        if ($UseHeuristic) {
            $Ext = $F.Extension.ToLower()
            $TypeDir = "Misc"
            if ($Ext -match "\.(jpg|jpeg|png|gif|tif|bmp|svg)") { $TypeDir = "Images" }
            elseif ($Ext -match "\.(mp4|mkv|mov|avi)") { $TypeDir = "Video" }
            elseif ($Ext -match "\.(mp3|wav|flac|ogg)") { $TypeDir = "Audio" }
            elseif ($Ext -match "\.(pdf|doc|docx|txt|md)") { $TypeDir = "Documents" }
            elseif ($Ext -match "\.(zip|rar|7z)") { $TypeDir = "Archives" }
            elseif ($Ext -match "\.(exe|msi|iso)") { $TypeDir = "Software" }
            elseif ($Ext -match "\.(c4d|blend|fbx|obj)") { $TypeDir = "3D" }
            $TargetDir = Join-Path $TgtDir $TypeDir
        }
        else {
            $Rel = $F.DirectoryName.Substring($SrcDir.Length).TrimStart('\')
            $TargetDir = Join-Path $TgtDir $Rel
        }
        
        Copy-SafeFile $F.FullName $TargetDir
    }
}

# Save Summary
function Save-Summary {
    $Stats.EndTime = Get-Date
    $Stats.Duration = ($Stats.EndTime - $Stats.StartTime).ToString()
    $Stats.CopiedMB = [math]::Round($Stats.CopiedBytes / 1MB, 2)
    $Stats.ErrorRate = if ($Stats.TotalFiles -gt 0) { 
        [math]::Round(($Stats.ErrorFiles / $Stats.TotalFiles) * 100, 2) 
    }
    else { 0 }
    
    $Stats | ConvertTo-Json -Depth 3 | Out-File $SummaryFile -Encoding UTF8
    
    Write-Host "`n=== SUMMARY ===" -ForegroundColor Green
    Write-Host "Total Files:    $($Stats.TotalFiles)"
    Write-Host "Copied:         $($Stats.CopiedFiles)"
    Write-Host "Skipped:        $($Stats.SkippedFiles)"
    Write-Host "Conflicts:      $($Stats.ConflictFiles)"
    Write-Host "Errors:         $($Stats.ErrorFiles) ($($Stats.ErrorRate)%)"
    Write-Host "Data Copied:    $($Stats.CopiedMB) MB"
    Write-Host "Duration:       $($Stats.Duration)"
    Write-Host "Report:         $SummaryFile" -ForegroundColor Cyan
}

# Mappings
$Map = @{
    "GSG_Assets"                    = "12 Datenpool Mediathek\Assets\GSG_Assets"
    "Downloads"                     = "_Inbox_Sorting\Downloads"
    "Backup"                        = "99 Datenpool Archiv & Backups\Alte_Backups"
    "Camtasia"                      = "12 Datenpool Mediathek\Camtasia_Projekte"
    "Cinema 4D"                     = "09 Datenpool Projekte\Cinema_4D"
    "Projektdatein Cinema 4D"       = "09 Datenpool Projekte\Cinema_4D_Projekte"
    "Genisis"                       = "09 Datenpool Projekte\Genisis"
    "Webseitenbilder"               = "12 Datenpool Mediathek\Bilder\Webseite"
    "Desktop unsortiert 07.01.2025" = "_Inbox_Sorting\Desktop_Dump"
}

# Main
Write-Host "=== SMART COPY v2.0 ===" -ForegroundColor Magenta
if ($DryRun) { Write-Host "[DRY-RUN MODE]" -ForegroundColor Yellow }
if ($Resume) { Write-Host "[RESUME MODE]" -ForegroundColor Cyan }
Write-Host "Errors: $ErrorLog" -ForegroundColor Red

# Check for resume
$Checkpoint = $null

if ($Resume) {
    $Checkpoint = Load-Checkpoint
    if ($Checkpoint) {
        $LogDir = $Checkpoint.LogDir
        Write-Host "Resuming from: $($Checkpoint.CurrentFolder) at index $($Checkpoint.CurrentIndex)"
    }
}

foreach ($Folder in $Map.Keys) {
    $Src = Join-Path $SourceRoot $Folder
    $Tgt = Join-Path $TargetRoot $Map[$Folder]
    
    if (Test-Path $Src) {
        Write-Host "`nProcessing: $Folder" -ForegroundColor Cyan
        $UseHeuristic = ($Folder -eq "Desktop unsortiert 07.01.2025")
        
        $StartIdx = 0
        if ($Checkpoint -and $Checkpoint.CurrentFolder -eq $Src) {
            $StartIdx = $Checkpoint.CurrentIndex
        }
        
        Copy-Directory $Src $Tgt $UseHeuristic $StartIdx
    }
    else {
        Write-Host "Skipped (not found): $Folder" -ForegroundColor DarkGray
    }
}

# Cleanup & Report
Remove-Checkpoint
Save-Summary
Write-Host "`n=== DONE ===" -ForegroundColor Green
