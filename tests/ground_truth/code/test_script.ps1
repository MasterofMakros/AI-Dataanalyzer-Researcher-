# PowerShell Test File
param(
    [string]\ = "Welt",
    [int]\ = 3
)

function Get-Greeting {
    param([string]\)
    return "Hallo, \!"
}

function Get-SystemInfo {
    return @{
        ComputerName = \DESKTOP-7INDSPH
        OS = (Get-CimInstance Win32_OperatingSystem).Caption
        RAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    }
}

# Hauptprogramm
for (\ = 1; \ -le \; \++) {
    Write-Host "\. \"
}

\ = Get-SystemInfo
Write-Host "System: \ - \"
