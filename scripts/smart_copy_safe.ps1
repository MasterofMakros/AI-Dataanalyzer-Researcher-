# Smart Copy (Safe Mode) - SIMPLIFIED
# No complex log rotation. Just works.

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogDir = "F:\conductor\scripts\archive\migration_logs\safe_copy_$Timestamp"
$ErrorLog = "$LogDir\errors.csv"
$SuccessLog = "$LogDir\success.log"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
"Time,File,Error" | Out-File $ErrorLog -Encoding UTF8
"[START] $Timestamp" | Out-File $SuccessLog -Encoding UTF8

function Log-Error($File, $Msg) {
    "$(Get-Date -Format 'HH:mm:ss'),$File,$Msg" | Out-File $ErrorLog -Append -Encoding UTF8
    Write-Host "[FAIL] $File" -ForegroundColor Red
}

function Log-Success($File) {
    # Append to success log (simple, no rotation)
    "$File" | Out-File $SuccessLog -Append -Encoding UTF8
}

function Get-Hash($Path) {
    try { return (Get-FileHash $Path -Algorithm MD5).Hash } catch { return $null }
}

function Copy-Safe($Src, $DestParent) {
    if (-not (Test-Path $DestParent)) {
        New-Item -ItemType Directory -Path $DestParent -Force | Out-Null
    }
    
    $Name = Split-Path $Src -Leaf
    $Dest = Join-Path $DestParent $Name
    
    # Fast path: Target missing
    if (-not (Test-Path $Dest)) {
        try {
            Copy-Item $Src $Dest -Force -ErrorAction Stop
            Log-Success $Name
        }
        catch {
            Log-Error $Name $_.Exception.Message
        }
        return
    }
    
    # Conflict: Check hash
    $SrcHash = Get-Hash $Src
    $DestHash = Get-Hash $Dest
    
    if ($SrcHash -eq $DestHash) {
        # Identical - skip
        return
    }
    
    # Different content - rename and copy
    $Ext = [IO.Path]::GetExtension($Name)
    $Base = [IO.Path]::GetFileNameWithoutExtension($Name)
    $NewName = "${Base}_CONFLICT_$Timestamp$Ext"
    $NewDest = Join-Path $DestParent $NewName
    
    try {
        Copy-Item $Src $NewDest -Force
        Log-Success "$Name -> $NewName"
    }
    catch {
        Log-Error $Name "Conflict copy failed: $($_.Exception.Message)"
    }
}

function Process-Dir($SrcDir, $TgtDir, $UseHeuristic = $false) {
    $Files = Get-ChildItem $SrcDir -Recurse -File -ErrorAction SilentlyContinue
    $Total = ($Files | Measure-Object).Count
    $i = 0
    
    foreach ($F in $Files) {
        $i++
        if ($i % 500 -eq 0) { Write-Host "Progress: $i / $Total" -ForegroundColor Cyan }
        
        if ($UseHeuristic) {
            # Sort by file type
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
            # Preserve structure
            $Rel = $F.DirectoryName.Substring($SrcDir.Length).TrimStart('\')
            $TargetDir = Join-Path $TgtDir $Rel
        }
        
        Copy-Safe $F.FullName $TargetDir
    }
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

Write-Host "=== SAFE COPY START ===" -ForegroundColor Yellow
Write-Host "Errors: $ErrorLog" -ForegroundColor Red

foreach ($Folder in $Map.Keys) {
    $Src = Join-Path $SourceRoot $Folder
    $Tgt = Join-Path $TargetRoot $Map[$Folder]
    
    if (Test-Path $Src) {
        Write-Host "Processing: $Folder" -ForegroundColor Cyan
        $UseHeuristic = ($Folder -eq "Desktop unsortiert 07.01.2025")
        Process-Dir $Src $Tgt $UseHeuristic
    }
    else {
        Write-Host "Skipped (not found): $Folder" -ForegroundColor DarkGray
    }
}

Write-Host "=== DONE ===" -ForegroundColor Green
