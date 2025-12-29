# Synology Cloud Merge Script
# Merges D:\Synology Cloud...\Neue Verzeichnisstruktur into F: structure

$Source = "D:\Synology Cloud 20-04-2025\Neue Verzeichnisstruktur"
$LogDir = "F:\conductor\scripts\archive\migration_logs"

# Known Datenpool folders -> Merge directly
$KnownFolders = @(
    "01 Datenpool Selbstversorgung",
    "02 Datenpool Energieversorgung",
    "03 Datenpool Gesundheit",
    "04 Datenpool Grenzwissenschaften",
    "05 Datenpool Wohnen",
    "06 Datenpool Produktentwicklung",
    "07 Datenpool Persönliche Angelegenheiten",
    "08 Datenpool Bibliothek",
    "09 Datenpool Projekte",
    "10 Datenpool Finanzen",
    "11 Datenpool Softwareanwendungen",
    "12 Datenpool Mediathek"
)

$Jobs = @()

Get-ChildItem $Source -Directory -Force | ForEach-Object {
    $FolderName = $_.Name
    $SourcePath = $_.FullName
    
    if ($KnownFolders -contains $FolderName) {
        # Known structure -> Merge to F:\<same name>
        $TargetPath = "F:\$FolderName"
    }
    else {
        # Unknown -> Inbox
        $TargetPath = "F:\_Inbox_Sorting\Synology_Rest\$FolderName"
    }
    
    $LogFile = "$LogDir\merge_synology_$($FolderName -replace '[^a-zA-Z0-9]', '_').log"
    
    Write-Host "Starting: $FolderName" -ForegroundColor Cyan
    Write-Host "  -> $TargetPath" -ForegroundColor DarkGray
    
    $Job = Start-Job -ScriptBlock {
        param($Src, $Tgt, $Log)
        robocopy $Src $Tgt /E /COPY:DAT /R:1 /W:1 /MT:4 /XO /NP /LOG:$Log
    } -ArgumentList $SourcePath, $TargetPath, $LogFile
    
    $Jobs += $Job
}

Write-Host "`nWaiting for all jobs to complete..." -ForegroundColor Yellow
$Jobs | Wait-Job | Out-Null

Write-Host "`n=== SYNOLOGY MERGE COMPLETE ===" -ForegroundColor Green
$Jobs | ForEach-Object {
    $state = $_.State
    Write-Host "Job $($_.Id): $state"
}
$Jobs | Remove-Job -Force
