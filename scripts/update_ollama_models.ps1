<# 
.SYNOPSIS
    Neural Vault - Ollama Model Auto-Updater
.DESCRIPTION
    Aktualisiert alle installierten Ollama LLM-Modelle woechentlich.
    Sendet Windows Toast Notifications ins Benachrichtigungs-Center.
.PARAMETER TestNotification
    Sendet nur eine Test-Benachrichtigung
.PARAMETER Enable
    Aktiviert den woechentlichen Scheduled Task
.PARAMETER Disable
    Deaktiviert den Scheduled Task (ohne zu loeschen)
.PARAMETER Status
    Zeigt den aktuellen Status des Scheduled Tasks
.EXAMPLE
    .\update_ollama_models.ps1 -TestNotification
    .\update_ollama_models.ps1 -Enable
    .\update_ollama_models.ps1 -Disable
    .\update_ollama_models.ps1 -Status
#>

param(
    [switch]$TestNotification,
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status,
    [switch]$Force,
    [string]$Container = "conductor-ollama"
)

# Encoding auf UTF-8 setzen
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Konfiguration - WICHTIG: Fallback wenn F: nicht verfuegbar
$SCRIPT_NAME = "NeuralVault-OllamaUpdater"
$TASK_NAME = "NeuralVault-OllamaUpdate"

# Pruefe ob F: verfuegbar ist, sonst nutze C:
if (Test-Path "F:\conductor") {
    $BASE_DIR = "F:\conductor"
} else {
    $BASE_DIR = "$env:USERPROFILE\.neuralvault"
    if (-not (Test-Path $BASE_DIR)) {
        New-Item -ItemType Directory -Path $BASE_DIR -Force | Out-Null
    }
}

$LOG_DIR = Join-Path $BASE_DIR "logs"
$LOG_FILE = Join-Path $LOG_DIR "ollama_update_$(Get-Date -Format 'yyyy-MM-dd').log"

# Erstelle Log-Verzeichnis
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# =============================================================================
# WINDOWS TOAST NOTIFICATION (ASCII-kompatibel)
# =============================================================================

function Show-Notification {
    param(
        [string]$Title,
        [string]$Message,
        [ValidateSet("Success", "Warning", "Error", "Info")]
        [string]$Type = "Info"
    )
    
    # Einfache Implementierung mit PowerShell
    Add-Type -AssemblyName System.Windows.Forms
    
    $icon = switch ($Type) {
        "Success" { [System.Windows.Forms.ToolTipIcon]::Info }
        "Warning" { [System.Windows.Forms.ToolTipIcon]::Warning }
        "Error"   { [System.Windows.Forms.ToolTipIcon]::Error }
        default   { [System.Windows.Forms.ToolTipIcon]::Info }
    }
    
    $balloon = New-Object System.Windows.Forms.NotifyIcon
    $balloon.Icon = [System.Drawing.SystemIcons]::Application
    $balloon.BalloonTipIcon = $icon
    $balloon.BalloonTipTitle = $Title
    $balloon.BalloonTipText = $Message
    $balloon.Visible = $true
    $balloon.ShowBalloonTip(10000)
    
    # Cleanup nach 10 Sekunden
    Start-Sleep -Milliseconds 100
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN"  { Write-Host $logEntry -ForegroundColor Yellow }
        "OK"    { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry }
    }
    
    try {
        Add-Content -Path $LOG_FILE -Value $logEntry -Encoding UTF8
    } catch {
        # Ignoriere Log-Fehler wenn Laufwerk nicht verfuegbar
    }
}

# =============================================================================
# SCHEDULED TASK MANAGEMENT
# =============================================================================

function Show-TaskStatus {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  NEURAL VAULT - Ollama Updater Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    
    if ($task) {
        $info = Get-ScheduledTaskInfo -TaskName $TASK_NAME
        Write-Host ""
        Write-Host "  Task Name:     $TASK_NAME" -ForegroundColor White
        Write-Host "  Status:        $($task.State)" -ForegroundColor $(if($task.State -eq 'Ready'){'Green'}else{'Yellow'})
        Write-Host "  Letzte Ausfuehrung: $($info.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Naechste Ausfuehrung: $($info.NextRunTime)" -ForegroundColor Gray
        Write-Host "  Letztes Ergebnis: $($info.LastTaskResult)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Steuerung:" -ForegroundColor White
        Write-Host "    -Enable   Aktivieren" -ForegroundColor DarkGray
        Write-Host "    -Disable  Deaktivieren" -ForegroundColor DarkGray
    } else {
        Write-Host ""
        Write-Host "  Task '$TASK_NAME' nicht gefunden." -ForegroundColor Yellow
        Write-Host "  Verwende -Enable um zu erstellen." -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Enable-UpdateTask {
    Write-Host "Erstelle/Aktiviere Scheduled Task..." -ForegroundColor Cyan
    
    $scriptPath = $MyInvocation.ScriptName
    if (-not $scriptPath) {
        $scriptPath = "F:\conductor\scripts\update_ollama_models.ps1"
    }
    
    # XML fuer Task (funktioniert ohne Admin fuer aktuellen User)
    $taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Neural Vault - Aktualisiert Ollama LLM-Modelle woechentlich</Description>
    <Author>$env:USERNAME</Author>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-05T03:00:00</StartBoundary>
      <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Sunday />
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT10M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -WindowStyle Hidden -File "$scriptPath"</Arguments>
      <WorkingDirectory>$BASE_DIR</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
    
    try {
        # Loesche existierenden Task
        schtasks /delete /tn $TASK_NAME /f 2>$null
        
        # Speichere XML temporaer
        $tempXml = [System.IO.Path]::GetTempFileName() + ".xml"
        $taskXml | Out-File -FilePath $tempXml -Encoding Unicode
        
        # Erstelle Task
        schtasks /create /tn $TASK_NAME /xml $tempXml
        
        Remove-Item $tempXml -Force
        
        Write-Host ""
        Write-Host "[OK] Task '$TASK_NAME' erstellt!" -ForegroundColor Green
        Write-Host "     Naechste Ausfuehrung: Sonntag 03:00 Uhr" -ForegroundColor Gray
        Write-Host ""
        
        Show-Notification -Title "Neural Vault Updater" -Message "Woechentliches Update aktiviert (Sonntag 03:00)" -Type "Success"
        
    } catch {
        Write-Host "[FEHLER] Task konnte nicht erstellt werden: $_" -ForegroundColor Red
    }
}

function Disable-UpdateTask {
    Write-Host "Deaktiviere Scheduled Task..." -ForegroundColor Yellow
    
    try {
        schtasks /change /tn $TASK_NAME /disable
        Write-Host "[OK] Task '$TASK_NAME' deaktiviert." -ForegroundColor Green
        Show-Notification -Title "Neural Vault Updater" -Message "Woechentliches Update deaktiviert" -Type "Warning"
    } catch {
        Write-Host "[FEHLER] $_" -ForegroundColor Red
    }
}

# =============================================================================
# DOCKER/OLLAMA FUNKTIONEN
# =============================================================================

function Test-DockerRunning {
    try {
        $null = docker info 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-InstalledModels {
    $output = docker exec $Container ollama list 2>&1
    if ($LASTEXITCODE -ne 0) { return @() }
    
    return $output | Select-Object -Skip 1 | ForEach-Object {
        ($_ -split '\s+')[0]
    } | Where-Object { $_ }
}

function Update-Model {
    param([string]$ModelName)
    
    Write-Log "Aktualisiere: $ModelName"
    
    try {
        $output = docker exec $Container ollama pull $ModelName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            if ($output -match "up to date|already exists") {
                Write-Log "  $ModelName ist aktuell" "INFO"
                return @{ Updated = $false; Success = $true }
            } else {
                Write-Log "  $ModelName aktualisiert!" "OK"
                return @{ Updated = $true; Success = $true }
            }
        } else {
            Write-Log "  Fehler: $output" "ERROR"
            return @{ Updated = $false; Success = $false }
        }
    } catch {
        Write-Log "  Exception: $_" "ERROR"
        return @{ Updated = $false; Success = $false }
    }
}

# =============================================================================
# HAUPTPROGRAMM
# =============================================================================

# Parameter-Handling
if ($TestNotification) {
    Write-Host "Sende Test-Benachrichtigung..."
    Show-Notification -Title "Neural Vault Test" -Message "Benachrichtigungen funktionieren!" -Type "Success"
    Write-Host "[OK] Test gesendet!" -ForegroundColor Green
    exit 0
}

if ($Status) {
    Show-TaskStatus
    exit 0
}

if ($Enable) {
    Enable-UpdateTask
    exit 0
}

if ($Disable) {
    Disable-UpdateTask
    exit 0
}

# Pruefe ob F: Laufwerk verfuegbar
if (-not (Test-Path "F:\")) {
    Write-Log "Laufwerk F: nicht verfuegbar - Update uebersprungen" "WARN"
    Show-Notification -Title "Neural Vault Update" -Message "Laufwerk F: nicht verfuegbar - Update uebersprungen" -Type "Warning"
    exit 0
}

# Normaler Update-Lauf
Write-Log "=============================================="
Write-Log "NEURAL VAULT - OLLAMA AUTO-UPDATE"
Write-Log "=============================================="

# Docker pruefen
if (-not (Test-DockerRunning)) {
    Write-Log "Docker nicht gestartet. Starte..." "WARN"
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Start-Sleep -Seconds 60
    
    if (-not (Test-DockerRunning)) {
        Write-Log "Docker Start fehlgeschlagen!" "ERROR"
        Show-Notification -Title "Ollama Update Fehler" -Message "Docker konnte nicht gestartet werden" -Type "Error"
        exit 1
    }
}

# Container pruefen
$running = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $Container }
if (-not $running) {
    Write-Log "Container starten..." "WARN"
    Set-Location "F:\conductor"
    docker compose up -d
    Start-Sleep -Seconds 30
}

# Modelle aktualisieren
$models = Get-InstalledModels
Write-Log "Gefundene Modelle: $($models.Count)"

if ($models.Count -eq 0) {
    Write-Log "Keine Modelle gefunden" "WARN"
    Show-Notification -Title "Ollama Update" -Message "Keine Modelle gefunden" -Type "Warning"
    exit 0
}

$success = 0; $failed = 0; $updated = 0

foreach ($model in $models) {
    if ($model) {
        $result = Update-Model -ModelName $model
        if ($result.Success) {
            $success++
            if ($result.Updated) { $updated++ }
        } else {
            $failed++
        }
    }
}

# Zusammenfassung
Write-Log "=============================================="
Write-Log "FERTIG: $success OK, $updated aktualisiert, $failed Fehler"
Write-Log "=============================================="

# Benachrichtigung
if ($failed -gt 0) {
    Show-Notification -Title "Ollama Update" -Message "$updated aktualisiert, $failed Fehler!" -Type "Warning"
} elseif ($updated -gt 0) {
    Show-Notification -Title "Ollama Update" -Message "$updated Modell(e) aktualisiert!" -Type "Success"
} else {
    Show-Notification -Title "Ollama Update" -Message "Alle $($models.Count) Modelle aktuell" -Type "Info"
}

# Log Cleanup
Get-ChildItem $LOG_DIR -Filter "ollama_update_*.log" -ErrorAction SilentlyContinue | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | 
    Remove-Item -Force -ErrorAction SilentlyContinue

exit $failed
