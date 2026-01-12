# Smart Copy v5.0 - TURBO MODE
# Features: Robocopy, Parallel Jobs, Built-in Progress Bar, No Hash Checks

param(
    [int]$MaxJobs = 5  # Parallel folder copies
)

$SourceRoot = "D:\"
$TargetRoot = "F:\"
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogDir = "F:\conductor\scripts\archive\migration_logs\turbo_v5_$Timestamp"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

Write-Host "============================================" -ForegroundColor Magenta
Write-Host "    TURBO MIGRATION v5.0 - ROBOCOPY MODE   " -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host "Log Directory: $LogDir"
Write-Host "Parallel Jobs: $MaxJobs"
Write-Host ""

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
    "F"
)

# --- Get ALL root items ---
$AllItems = Get-ChildItem $SourceRoot -Force -ErrorAction SilentlyContinue | Where-Object {
    $IgnoreList -notcontains $_.Name
}

$TotalFolders = $AllItems.Count
$CompletedFolders = 0
$StartTime = Get-Date
$Jobs = @()

Write-Host "Found $TotalFolders items to process." -ForegroundColor Cyan
Write-Host ""

# --- Process each item ---
foreach ($Item in $AllItems) {
    $Name = $Item.Name
    $SourcePath = $Item.FullName
    
    # Determine Target
    $MapKey = $Map.Keys | Where-Object { $_ -ieq $Name } | Select-Object -First 1
    if ($MapKey) {
        $TargetSubPath = $Map[$MapKey]
    }
    else {
        $TargetSubPath = "_Inbox_Sorting\Rest_of_D\$Name"
    }
    $TargetPath = Join-Path $TargetRoot $TargetSubPath
    
    # Robocopy Log
    $RoboLog = Join-Path $LogDir "robocopy_$($Name -replace '[^a-zA-Z0-9]', '_').log"
    
    if ($Item.PSIsContainer) {
        # Directory -> Robocopy Job
        $JobScript = {
            param($Src, $Tgt, $Log)
            # /E = Include subdirs (even empty)
            # /COPY:DAT = Data, Attributes, Timestamps
            # /R:1 /W:1 = Retry 1x, Wait 1s (fast fail)
            # /MT:4 = Multi-threaded (4 threads per job)
            # /XO = Exclude Older (skip if target is newer)
            # /NP = No Progress (cleaner log)
            # /NFL /NDL = No file/dir list in log (smaller log)
            robocopy $Src $Tgt /E /COPY:DAT /R:1 /W:1 /MT:4 /XO /NP /LOG:$Log
        }
        
        # Start Job
        $Job = Start-Job -ScriptBlock $JobScript -ArgumentList $SourcePath, $TargetPath, $RoboLog
        $Jobs += $Job
        Write-Host "[JOB] Started: $Name" -ForegroundColor Green
        
    }
    else {
        # Single File -> Direct Copy
        $TargetDir = Split-Path $TargetPath -Parent
        if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
        Copy-Item $SourcePath $TargetPath -Force -ErrorAction SilentlyContinue
        Write-Host "[FILE] Copied: $Name" -ForegroundColor DarkGreen
        $CompletedFolders++
    }
    
    # Throttle: Wait if too many jobs
    while (($Jobs | Where-Object { $_.State -eq 'Running' }).Count -ge $MaxJobs) {
        Start-Sleep -Milliseconds 500
        
        # Update Progress
        $RunningJobs = ($Jobs | Where-Object { $_.State -eq 'Running' }).Count
        $DoneJobs = ($Jobs | Where-Object { $_.State -eq 'Completed' }).Count
        $Percent = [math]::Round((($DoneJobs + $CompletedFolders) / $TotalFolders) * 100)
        
        $Elapsed = (Get-Date) - $StartTime
        $Speed = if ($Elapsed.TotalSeconds -gt 0) { [math]::Round(($DoneJobs + $CompletedFolders) / $Elapsed.TotalSeconds, 2) } else { 0 }
        $Remaining = $TotalFolders - ($DoneJobs + $CompletedFolders)
        $ETA = if ($Speed -gt 0) { [math]::Round($Remaining / $Speed / 60, 1) } else { "?" }
        
        Write-Progress -Activity "TURBO MIGRATION" -Status "$Percent% | $RunningJobs active | ETA: ${ETA}min" -PercentComplete $Percent
    }
}

# Wait for all remaining jobs
Write-Host "`nWaiting for remaining jobs to finish..." -ForegroundColor Yellow
$Jobs | Wait-Job | Out-Null

# Final Progress
Write-Progress -Activity "TURBO MIGRATION" -Completed

# Summary
$EndTime = Get-Date
$Duration = $EndTime - $StartTime
$FailedJobs = $Jobs | Where-Object { $_.State -eq 'Failed' }

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "           MIGRATION COMPLETE               " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "Total Items:    $TotalFolders"
Write-Host "Duration:       $($Duration.ToString('hh\:mm\:ss'))"
Write-Host "Failed Jobs:    $($FailedJobs.Count)" -ForegroundColor $(if ($FailedJobs.Count -gt 0) { "Red" } else { "Green" })
Write-Host "Logs:           $LogDir"
Write-Host ""

# Cleanup Jobs
$Jobs | Remove-Job -Force

Write-Host "Done! Check logs for details." -ForegroundColor Cyan
