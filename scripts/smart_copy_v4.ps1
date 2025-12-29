# Smart Copy v4.0 - UNIVERSAL COVERAGE
# Iterates ALL items on SourceRoot.
# 1. Maps known folders to specific targets.
# 2. Moves unknown folders to Safe Inbox.
# 3. Skips critical system folders.

param(
    [switch]$Resume,
    [switch]$DryRun
)

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogDir = "F:\conductor\scripts\archive\migration_logs\safe_copy_v4_$Timestamp"
$CheckpointFile = "F:\conductor\scripts\checkpoint_v4.json"

# --- Mappings ---
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
    "3D Modell Worklow"             = "09 Datenpool Projekte\3D_Modell_Workflow"
    "Dokumente"                     = "_Inbox_Sorting\Dokumente"
    "Projekte"                      = "09 Datenpool Projekte\Migrated_Projekte"
    "Synology"                      = "99 Datenpool Archiv & Backups\Synology"
    "Synology Cloud 20-04-2025"     = "99 Datenpool Archiv & Backups\Synology_Cloud_2025"
    "Telegram Desktop"              = "_Inbox_Sorting\Telegram"
    "USB Stick"                     = "_Inbox_Sorting\USB_Stick_Dump"
    "obsidian-plugins"              = "11 Datenpool Softwareanwendungen\Obsidian_Plugins"
}

# --- Ignore List ---
$IgnoreList = @(
    "`$RECYCLE.BIN",
    "System Volume Information",
    "found.000",
    ".gemini",
    ".gemini_safety_log",
    "F" # Prevent drive loop
)

# Statistics
$script:Stats = @{
    StartTime = Get-Date
    TotalFiles = 0; CopiedFiles = 0; SkippedFiles = 0; ConflictFiles = 0; ErrorFiles = 0
    UnknownFoldersFound = 0
}

# Init Logs
if (-not $Resume) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$ErrorLog = "$LogDir\errors.csv"
$SuccessLog = "$LogDir\success.log"
if (-not $Resume) { "Time,File,Error" | Out-File $ErrorLog -Encoding UTF8 }

# --- Helper Functions ---
function Write-Log($File, $Msg, $IsError = $true) {
    if ($IsError) {
        "$(Get-Date -Format 'HH:mm:ss'),$File,$Msg" | Out-File $ErrorLog -Append -Encoding UTF8
        Write-Host "[ERROR] $File" -ForegroundColor Red
        $script:Stats.ErrorFiles++
    }
    else {
        "$File" | Out-File $SuccessLog -Append -Encoding UTF8
        $script:Stats.CopiedFiles++
    }
}

function Get-FastHash($Path) {
    try { return (Get-FileHash $Path -Algorithm SHA256 -ErrorAction Stop).Hash } catch { return "ERR" }
}

function Copy-SafeFile($Src, $DestParent) {
    if ($DryRun) { Write-Host "[DRY] $Src -> $DestParent"; return }
    if (-not (Test-Path $DestParent)) { New-Item -ItemType Directory -Path $DestParent -Force | Out-Null }
    
    $Name = Split-Path $Src -Leaf
    $Dest = Join-Path $DestParent $Name
    
    if (-not (Test-Path $Dest)) {
        try { Copy-Item $Src $Dest -Force -ErrorAction Stop; Write-Log $Name "OK" $false }
        catch { Write-Log $Name $_.Exception.Message $true }
        return
    }
    
    $SrcHash = Get-FastHash $Src
    $DestHash = Get-FastHash $Dest
    if ($SrcHash -ne $DestHash) {
        $NewName = "$([IO.Path]::GetFileNameWithoutExtension($Name))_CONFLICT_$Timestamp$([IO.Path]::GetExtension($Name))"
        try { Copy-Item $Src (Join-Path $DestParent $NewName) -Force; Write-Log "$Name -> $NewName" "OK" $false }
        catch { Write-Log $Name "Conflict Copy Failed" $true }
    }
    else {
        $script:Stats.SkippedFiles++
    }
}

function Copy-Recursive($SrcDir, $TgtDir) {
    $Files = Get-ChildItem $SrcDir -Recurse -File -Force -ErrorAction SilentlyContinue
    $Total = $Files.Count
    $i = 0
    Write-Host "   Processing $Total files..." -ForegroundColor DarkGray
    
    foreach ($F in $Files) {
        $i++
        if ($i % 500 -eq 0) { Write-Host "   [$([math]::Round(($i/$Total)*100))%] $i/$Total" -ForegroundColor Yellow }
        
        $RelPath = $F.DirectoryName.Substring($SrcDir.Length).TrimStart('\')
        $CurrentTgt = Join-Path $TgtDir $RelPath
        Copy-SafeFile $F.FullName $CurrentTgt
    }
}

# --- MAIN LOOP ---
Write-Host "=== UNIVERSAL MIGRATION V4 ===" -ForegroundColor Magenta
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"

$RootItems = Get-ChildItem $SourceRoot -Force -ErrorAction SilentlyContinue

foreach ($Item in $RootItems) {
    $Name = $Item.Name
    
    # 1. Check Ignore List
    if ($IgnoreList -contains $Name) {
        Write-Host "Skipped (System): $Name" -ForegroundColor DarkGray
        continue
    }

    # 2. Determine Target
    $TargetSubPath = ""
    
    # Case-insensitive map check
    $MapKey = $Map.Keys | Where-Object { $_ -ieq $Name } | Select-Object -First 1
    
    if ($MapKey) {
        # Known Mapping
        $TargetSubPath = $Map[$MapKey]
        Write-Host ">> Mapping: $Name -> $TargetSubPath" -ForegroundColor Cyan
    }
    else {
        # Unknown -> Inbox Sorting
        $TargetSubPath = "_Inbox_Sorting\Rest_of_D\$Name"
        Write-Host ">> Unknown: $Name -> $TargetSubPath" -ForegroundColor Yellow
        $script:Stats.UnknownFoldersFound++
    }
    
    $FullTarget = Join-Path $TargetRoot $TargetSubPath
    
    # 3. Process
    if ($Item.PSIsContainer) {
        Copy-Recursive $Item.FullName $FullTarget
    }
    else {
        # Root File
        Copy-SafeFile $Item.FullName (Split-Path $FullTarget -Parent)
    }
}

Write-Host "`n=== DONE ===" -ForegroundColor Green
$script:Stats | Out-String | Write-Host
