# POWERSHELL DATA INTEGRITY MANIFEST GENERATOR v2.0 (SOP-001 Compliant)
# Role: Data Engineer
# Purpose: Create an immutable ledger of all files on F: to prove migration integrity.
# Standards: SOP-001 (3-Tier Retry), Resumable, Streaming Hash.

param(
    [string]$RootPath = "F:\",
    [string]$ManifestPath = "F:\conductor\manifest_ledger.csv",
    [switch]$FullStart = $false
)

$ErrorActionPreference = "Stop"
$ErrorList = @()

function Get-FileHash-WithRetry {
    param([string]$FilePath)
    
    # TIER 1: Fast Retry (Transient locks)
    for ($i = 0; $i -lt 3; $i++) {
        try {
            $algo = [System.Security.Cryptography.SHA256]::Create()
            $stream = [System.IO.File]::OpenRead($FilePath)
            $hashBytes = $algo.ComputeHash($stream)
            $stream.Close()
            return [BitConverter]::ToString($hashBytes).Replace("-", "")
        }
        catch {
            Start-Sleep -Milliseconds 100
        }
    }

    # TIER 2: Slow Retry (Network/App locks)
    Write-Warning "File locked/busy, entering slow retry: $FilePath"
    Start-Sleep -Seconds 5
    try {
        $algo = [System.Security.Cryptography.SHA256]::Create()
        $stream = [System.IO.File]::OpenRead($FilePath)
        $hashBytes = $algo.ComputeHash($stream)
        $stream.Close()
        return [BitConverter]::ToString($hashBytes).Replace("-", "")
    }
    catch {
        # TIER 3: Log Failure for Final Sweep
        Write-Warning "FAILED to hash: $FilePath. Adding to Error Ledger."
        return "ERROR"
    }
}

# Setup Manifest File
if ($FullStart -or -not (Test-Path $ManifestPath)) {
    Write-Host "Creating new Manifest Ledger at: $ManifestPath" -ForegroundColor Cyan
    "Path,Size,Modified,SHA256" | Out-File $ManifestPath -Encoding UTF8
}

$processedPaths = @{}

# Load existing progress
if (-not $FullStart -and (Test-Path $ManifestPath)) {
    Write-Host "Loading existing manifest to resume..." -NoNewline -ForegroundColor Yellow
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    # Read CSV efficiently
    $reader = [System.IO.File]::OpenText($ManifestPath)
    $header = $reader.ReadLine() # Skip header
    while (($line = $reader.ReadLine()) -ne $null) {
        # Simple CSV parse assuming quotes
        $parts = $line.Split(',') 
        # Path is usually the first part, strip quotes
        if ($parts.Count -ge 1) { 
            $p = $parts[0].Trim('"')
            $processedPaths[$p] = $true 
        }
    }
    $reader.Close()
    $timer.Stop()
    Write-Host " Done ($($processedPaths.Count) files loaded in $($timer.Elapsed.TotalSeconds)s)" -ForegroundColor Green
}

Write-Host "Starting Data Integrity Crawl (SOP-001 Hardened) on: $RootPath" -ForegroundColor Cyan
Write-Host "Tracking 3-Tier Retries for locked files."

$fileCount = 0
$startTime = Get-Date
$exclude = @("System Volume Information", "`$RECYCLE.BIN", "conductor\scripts\archive")

Get-ChildItem -Path $RootPath -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $file = $_
    
    # Skip excluded
    $skip = $false
    foreach ($ex in $exclude) { if ($file.FullName -match [regex]::Escape($ex)) { $skip = $true; break } }
    if ($skip) { return }

    if ($processedPaths.ContainsKey($file.FullName)) { return }

    $fileCount++
    if ($fileCount % 100 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $rate = [math]::Round($fileCount / ([math]::Max($elapsed.TotalSeconds, 1)), 1)
        Write-Progress -Activity "Hashing Data Lake" -Status "Processed: $fileCount ($rate files/s)" -CurrentOperation "$($file.Name)"
    }

    $hash = Get-FileHash-WithRetry -FilePath $file.FullName
    
    if ($hash -eq "ERROR") {
        $global:ErrorList += $file.FullName
    }
    
    $modDate = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    $record = "`"$($file.FullName)`",$($file.Length),`"$modDate`",`"$hash`""
    $record | Out-File -FilePath $ManifestPath -Append -Encoding UTF8
}

# FINAL SWEEP
if ($ErrorList.Count -gt 0) {
    Write-Host "Starting Final Sweep for $($ErrorList.Count) failed files..." -ForegroundColor Magenta
    foreach ($path in $ErrorList) {
        $hash = Get-FileHash-WithRetry -FilePath $path
        if ($hash -ne "ERROR") {
            $file = Get-Item $path
            $modDate = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            $record = "`"$($file.FullName)`",$($file.Length),`"$modDate`",`"$hash`""
            $record | Out-File -FilePath $ManifestPath -Append -Encoding UTF8
            Write-Host "Recovered: $path" -ForegroundColor Green
        }
        else {
            Write-Error "PERMANENT FAILURE: $path"
        }
    }
}

Write-Host "Generaton Complete. Ledger: $ManifestPath" -ForegroundColor Green
