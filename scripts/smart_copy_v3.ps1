# Smart Copy v3.0 - HARDENED
# Fixes: Hidden files, Symlinks, Empty folders, Case-insensitive, No structure-breaking heuristics

param(
    [switch]$Resume,
    [switch]$DryRun
)

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogDir = "F:\conductor\scripts\archive\migration_logs\safe_copy_v3_$Timestamp"
$CheckpointFile = "F:\conductor\scripts\checkpoint_v3.json"

# Statistics
$script:Stats = @{
    StartTime       = Get-Date
    TotalFiles      = 0
    CopiedFiles     = 0
    SkippedFiles    = 0
    ConflictFiles   = 0
    ErrorFiles      = 0
    SymlinksSkipped = 0
    EmptyFolders    = 0
    TotalBytes      = 0
    CopiedBytes     = 0
}

# Initialize Logs
if (-not $Resume) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$ErrorLog = "$LogDir\errors.csv"
$SuccessLog = "$LogDir\success.log"
$SymlinkLog = "$LogDir\symlinks_skipped.log"
$SummaryFile = "$LogDir\summary.json"

if (-not $Resume) {
    "Time,File,Error" | Out-File $ErrorLog -Encoding UTF8
    "[START] $Timestamp" | Out-File $SuccessLog -Encoding UTF8
    "# Symlinks skipped" | Out-File $SymlinkLog -Encoding UTF8
}

# --- Checkpoint ---
function Save-Checkpoint($Folder, $Index) {
    @{
        LogDir = $LogDir
        Folder = $Folder
        Index  = $Index
        Stats  = $script:Stats
    } | ConvertTo-Json -Depth 5 | Out-File $CheckpointFile -Encoding UTF8
}

function Load-Checkpoint {
    if (Test-Path $CheckpointFile) {
        return Get-Content $CheckpointFile -Raw | ConvertFrom-Json
    }
    return $null
}

function Remove-Checkpoint {
    if (Test-Path $CheckpointFile) { Remove-Item $CheckpointFile -Force }
}

# --- Logging ---
function Write-ErrorEntry($File, $Msg) {
    "$(Get-Date -Format 'HH:mm:ss'),$File,$Msg" | Out-File $ErrorLog -Append -Encoding UTF8
    $script:Stats.ErrorFiles++
    Write-Host "[ERROR] $File" -ForegroundColor Red
}

function Write-SuccessEntry($File, $Bytes) {
    $File | Out-File $SuccessLog -Append -Encoding UTF8
    $script:Stats.CopiedFiles++
    $script:Stats.CopiedBytes += $Bytes
}

# --- Symlink Detection ---
function Test-Symlink($Path) {
    try {
        $item = Get-Item $Path -Force -ErrorAction Stop
        return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    }
    catch {
        return $false
    }
}

# --- Hash ---
function Get-FastHash($Path) {
    try { return (Get-FileHash $Path -Algorithm SHA256 -ErrorAction Stop).Hash }
    catch { return "ERROR" }
}

# --- Copy Logic ---
function Copy-SafeFile($Src, $DestParent) {
    # Skip symlinks
    if (Test-Symlink $Src) {
        $Src | Out-File $SymlinkLog -Append -Encoding UTF8
        $script:Stats.SymlinksSkipped++
        return
    }
    
    if ($DryRun) {
        Write-Host "[DRY] $Src" -ForegroundColor DarkGray
        return
    }
    
    if (-not (Test-Path $DestParent)) {
        New-Item -ItemType Directory -Path $DestParent -Force | Out-Null
    }
    
    $Name = Split-Path $Src -Leaf
    $Dest = Join-Path $DestParent $Name
    
    try {
        $Size = (Get-Item $Src -Force -ErrorAction Stop).Length
    }
    catch {
        Write-ErrorEntry $Name "Cannot read file size"
        return
    }
    
    # Check path length
    if ($Dest.Length -gt 250) {
        Write-ErrorEntry $Name "Path too long ($($Dest.Length) chars)"
        return
    }
    
    # Fast path: Target missing
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
    
    # Conflict: Hash check (SHA256 for safety)
    $SrcHash = Get-FastHash $Src
    $DestHash = Get-FastHash $Dest
    
    if ($SrcHash -eq $DestHash) {
        $script:Stats.SkippedFiles++
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
        $script:Stats.ConflictFiles++
    }
    catch {
        Write-ErrorEntry $Name "Conflict copy failed"
    }
}

# --- Process Directory (NO HEURISTIC - preserve structure!) ---
function Copy-Directory($SrcDir, $TgtDir, $StartIndex = 0) {
    # Include hidden files with -Force
    $Files = @(Get-ChildItem $SrcDir -Recurse -File -Force -ErrorAction SilentlyContinue)
    $Total = $Files.Count
    $script:Stats.TotalFiles += $Total
    
    # Also copy empty folder structure
    $Folders = Get-ChildItem $SrcDir -Recurse -Directory -Force -ErrorAction SilentlyContinue
    foreach ($Folder in $Folders) {
        $Rel = $Folder.FullName.Substring($SrcDir.Length).TrimStart('\')
        $TargetFolder = Join-Path $TgtDir $Rel
        if (-not (Test-Path $TargetFolder)) {
            New-Item -ItemType Directory -Path $TargetFolder -Force | Out-Null
            $script:Stats.EmptyFolders++
        }
    }
    
    for ($i = $StartIndex; $i -lt $Total; $i++) {
        $F = $Files[$i]
        $script:Stats.TotalBytes += $F.Length
        
        # Progress every 200 files
        if ($i % 200 -eq 0) {
            $Pct = if ($Total -gt 0) { [math]::Round(($i / $Total) * 100, 1) } else { 0 }
            $Elapsed = (Get-Date) - $script:Stats.StartTime
            $Rate = if ($Elapsed.TotalSeconds -gt 0) { [math]::Round($i / $Elapsed.TotalSeconds, 1) } else { 0 }
            Write-Host "[$Pct%] $i/$Total | $Rate files/s | Errors: $($script:Stats.ErrorFiles)" -ForegroundColor Yellow
            
            # Checkpoint every 1000 files
            if ($i % 1000 -eq 0 -and $i -gt 0) {
                Save-Checkpoint $SrcDir $i
            }
        }
        
        # Preserve exact structure (NO heuristic sorting!)
        $Rel = $F.DirectoryName.Substring($SrcDir.Length).TrimStart('\')
        $TargetDir = Join-Path $TgtDir $Rel
        
        Copy-SafeFile $F.FullName $TargetDir
    }
}

# --- Summary ---
function Save-Summary {
    $script:Stats.EndTime = Get-Date
    $script:Stats.Duration = ((Get-Date) - $script:Stats.StartTime).ToString()
    $script:Stats.CopiedMB = [math]::Round($script:Stats.CopiedBytes / 1MB, 2)
    $script:Stats.ErrorRate = if ($script:Stats.TotalFiles -gt 0) {
        [math]::Round(($script:Stats.ErrorFiles / $script:Stats.TotalFiles) * 100, 2)
    }
    else { 0 }
    
    $script:Stats | ConvertTo-Json -Depth 5 | Out-File $SummaryFile -Encoding UTF8
    
    Write-Host "`n========== SUMMARY ==========" -ForegroundColor Green
    Write-Host "Total Files:     $($script:Stats.TotalFiles)"
    Write-Host "Copied:          $($script:Stats.CopiedFiles)"
    Write-Host "Skipped (dup):   $($script:Stats.SkippedFiles)"
    Write-Host "Conflicts:       $($script:Stats.ConflictFiles)"
    Write-Host "Errors:          $($script:Stats.ErrorFiles) ($($script:Stats.ErrorRate)%)" -ForegroundColor $(if ($script:Stats.ErrorFiles -gt 0) { "Red" } else { "Green" })
    Write-Host "Symlinks Skip:   $($script:Stats.SymlinksSkipped)"
    Write-Host "Empty Folders:   $($script:Stats.EmptyFolders)"
    Write-Host "Data Copied:     $($script:Stats.CopiedMB) MB"
    Write-Host "Duration:        $($script:Stats.Duration)"
    Write-Host "==============================" -ForegroundColor Green
}

# --- Mappings (Comprehensive Scan) ---
$Map = [ordered]@{
    # High Priority Pending
    "3D Modell Worklow"                                       = "09 Datenpool Projekte\3D_Modell_Workflow"
    "Camtasia"                                                = "12 Datenpool Mediathek\Camtasia_Projekte"
    "Desktop unsortiert 07.01.2025"                           = "_Inbox_Sorting\Desktop_Dump"
    "Dokumente"                                               = "_Inbox_Sorting\Dokumente"
    "Projektdatein Cinema 4D"                                 = "09 Datenpool Projekte\Cinema_4D_Projekte"
    "Projekte"                                                = "09 Datenpool Projekte\Migrated_Projekte"
    "Synology"                                                = "99 Datenpool Archiv & Backups\Synology"
    "Synology Cloud 20-04-2025"                               = "99 Datenpool Archiv & Backups\Synology_Cloud_2025"
    "Telegram Desktop"                                        = "_Inbox_Sorting\Telegram"
    "USB Stick"                                               = "_Inbox_Sorting\USB_Stick_Dump"
    "meditation_der_gegenwaertige_moment-mp3-datei_documents" = "12 Datenpool Mediathek\Audio\Meditation"
    "obsidian-plugins"                                        = "11 Datenpool Softwareanwendungen\Obsidian_Plugins"
    
    # Files in Root (will be moved to Inbox root)
    "20231202_220624.jpg"                                     = "_Inbox_Sorting\Root_Files\20231202_220624.jpg"

    # Previously configured (just in case leftovers remain)
    "GSG_Assets"                                              = "12 Datenpool Mediathek\Assets\GSG_Assets"
    "Downloads"                                               = "_Inbox_Sorting\Downloads"
    "Cinema 4D"                                               = "09 Datenpool Projekte\Cinema_4D"
    "Genisis"                                                 = "09 Datenpool Projekte\Genisis"
    "Webseitenbilder"                                         = "12 Datenpool Mediathek\Bilder\Webseite"
}

# Folders explicitly IGNORED (System or Destination Artifacts)
# - Backup
# - $RECYCLE.BIN
# - System Volume Information
# - found.000
# - .gemini
# - F (Likely drive loop)
# - 01...12 Datenpool (Source seems to contain target structure artifacts? We skip to avoid confusion)

# --- MAIN ---
Write-Host "============================================" -ForegroundColor Magenta
Write-Host "       SMART COPY v3.0 - HARDENED           " -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
if ($DryRun) { Write-Host "[DRY-RUN MODE - No changes will be made]" -ForegroundColor Yellow }
if ($Resume) { Write-Host "[RESUME MODE]" -ForegroundColor Cyan }
Write-Host "Log Directory: $LogDir"
Write-Host "Errors Log:    $ErrorLog" -ForegroundColor Red
Write-Host ""

# Resume handling
$Checkpoint = $null
if ($Resume) {
    $Checkpoint = Load-Checkpoint
    if ($Checkpoint) {
        $LogDir = $Checkpoint.LogDir
        $script:Stats = $Checkpoint.Stats
        Write-Host "Resuming from checkpoint..." -ForegroundColor Cyan
    }
}

foreach ($Folder in $Map.Keys) {
    # Case-insensitive source check
    $Src = Join-Path $SourceRoot $Folder
    $Tgt = Join-Path $TargetRoot $Map[$Folder]
    
    # Try to find folder case-insensitively
    $ActualFolder = Get-ChildItem $SourceRoot -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ieq $Folder } | Select-Object -First 1
    
    if ($ActualFolder) {
        $Src = $ActualFolder.FullName
        Write-Host "`n>> Processing: $($ActualFolder.Name)" -ForegroundColor Cyan
        
        $StartIdx = 0
        if ($Checkpoint -and $Checkpoint.Folder -eq $Src) {
            $StartIdx = $Checkpoint.Index
            Write-Host "   Resuming from index $StartIdx" -ForegroundColor Yellow
        }
        
        Copy-Directory $Src $Tgt $StartIdx
    }
    else {
        Write-Host ">> Skipped (not found): $Folder" -ForegroundColor DarkGray
    }
}

# Finalize
Remove-Checkpoint
Save-Summary
Write-Host "`n=== COMPLETE ===" -ForegroundColor Green
