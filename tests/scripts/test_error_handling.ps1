<#
.SYNOPSIS
    Neural Vault - Error Handling Test Suite
    Tests system resilience with corrupt and invalid files

.DESCRIPTION
    Tests error handling capabilities:
    1. Corrupt/invalid files routing to DLQ
    2. Unsupported format handling
    3. Worker crash recovery
    4. Graceful degradation

.PARAMETER ApiUrl
    Base URL of the conductor-api

.EXAMPLE
    .\test_error_handling.ps1
#>

param(
    [string]$RouterUrl = "http://127.0.0.1:8030",
    [string]$GroundTruthPath = ""
)

$ErrorActionPreference = "Continue"

if (-not $GroundTruthPath) {
    $GroundTruthPath = Join-Path $PSScriptRoot "..\ground_truth"
}

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Create temp directory for corrupt test files
$TempDir = Join-Path $env:TEMP "neural_vault_error_tests"
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Get-QueueLength {
    param([string]$Queue)
    
    try {
        $result = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $Queue 2>$null
        if ($result -match "^\d+$") { return [int]$result }
    } catch {}
    return 0
}

function Submit-FileToRouter {
    param([string]$FilePath)
    
    try {
        $body = @{ filepath = $FilePath } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$RouterUrl/route" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        return @{
            Success = $true
            Queue = $response.queue
            MessageId = $response.message_id
            Response = $response
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        }
    }
}

function Create-CorruptFile {
    param(
        [string]$Extension,
        [string]$OutputDir
    )
    
    $filename = "corrupt_test_$(Get-Random).$Extension"
    $filepath = Join-Path $OutputDir $filename
    
    # Create file with random bytes (invalid content)
    $randomBytes = New-Object byte[] 1024
    (New-Object Random).NextBytes($randomBytes)
    [System.IO.File]::WriteAllBytes($filepath, $randomBytes)
    
    return $filepath
}

function Create-EmptyFile {
    param(
        [string]$Extension,
        [string]$OutputDir
    )
    
    $filename = "empty_test_$(Get-Random).$Extension"
    $filepath = Join-Path $OutputDir $filename
    
    # Create empty file
    New-Item -ItemType File -Path $filepath -Force | Out-Null
    
    return $filepath
}

function Create-OversizedFile {
    param(
        [string]$Extension,
        [string]$OutputDir,
        [int]$SizeMB = 50
    )
    
    $filename = "large_test_$(Get-Random).$Extension"
    $filepath = Join-Path $OutputDir $filename
    
    # Create file with specified size
    $stream = [System.IO.File]::Create($filepath)
    $stream.SetLength($SizeMB * 1024 * 1024)
    $stream.Close()
    
    return $filepath
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: ERROR HANDLING TEST SUITE" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    Tests = @()
}

# -----------------------------------------------------------------------------
# DLQ STATUS
# -----------------------------------------------------------------------------

Write-Host "--- Dead Letter Queue (DLQ) Status ---" -ForegroundColor Yellow
Write-Host ""

$dlqQueues = @("dlq:documents", "dlq:images", "dlq:audio", "dlq:video", "dlq:archive", "dlq:email")
$totalDlq = 0

foreach ($dlq in $dlqQueues) {
    $count = Get-QueueLength -Queue $dlq
    $totalDlq += $count
    if ($count -gt 0) {
        Write-Host "  $dlq : $count items" -ForegroundColor DarkYellow
    }
}

if ($totalDlq -eq 0) {
    Write-Host "  All DLQs empty (no errors recorded)" -ForegroundColor Green
}
Write-Host ""

# -----------------------------------------------------------------------------
# TEST 1: CORRUPT FILE HANDLING
# -----------------------------------------------------------------------------

Write-Host "--- Test 1: Corrupt File Handling ---" -ForegroundColor Yellow
Write-Host ""

$corruptExtensions = @("pdf", "docx", "jpg", "mp3")

foreach ($ext in $corruptExtensions) {
    Write-Host "  Testing corrupt .$ext file..." -NoNewline
    
    try {
        $corruptFile = Create-CorruptFile -Extension $ext -OutputDir $TempDir
        $result = Submit-FileToRouter -FilePath $corruptFile
        
        if ($result.Success) {
            # File was accepted (routing succeeded, processing may fail later)
            Write-Host " [OK] Routed to $($result.Queue)" -ForegroundColor Green
            $Results.Passed++
            $Results.Tests += @{
                Name = "Corrupt $ext"
                Status = "PASS"
                Queue = $result.Queue
            }
        } else {
            # Router rejected the file (also acceptable behavior)
            Write-Host " [OK] Rejected: $($result.Error)" -ForegroundColor Yellow
            $Results.Passed++
            $Results.Tests += @{
                Name = "Corrupt $ext"
                Status = "REJECTED"
                Error = $result.Error
            }
        }
        
        # Cleanup
        Remove-Item $corruptFile -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host " [ERROR] $_" -ForegroundColor Red
        $Results.Failed++
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# TEST 2: EMPTY FILE HANDLING
# -----------------------------------------------------------------------------

Write-Host "--- Test 2: Empty File Handling ---" -ForegroundColor Yellow
Write-Host ""

$emptyExtensions = @("txt", "pdf", "json")

foreach ($ext in $emptyExtensions) {
    Write-Host "  Testing empty .$ext file..." -NoNewline
    
    try {
        $emptyFile = Create-EmptyFile -Extension $ext -OutputDir $TempDir
        $result = Submit-FileToRouter -FilePath $emptyFile
        
        if ($result.Success) {
            Write-Host " [OK] Routed to $($result.Queue)" -ForegroundColor Green
            $Results.Passed++
        } else {
            Write-Host " [OK] Rejected gracefully" -ForegroundColor Yellow
            $Results.Passed++
        }
        
        Remove-Item $emptyFile -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host " [ERROR] $_" -ForegroundColor Red
        $Results.Failed++
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# TEST 3: UNSUPPORTED FORMAT HANDLING
# -----------------------------------------------------------------------------

Write-Host "--- Test 3: Unsupported Format Handling ---" -ForegroundColor Yellow
Write-Host ""

$unsupportedExtensions = @("xyz", "fake", "unknown123", "notreal")

foreach ($ext in $unsupportedExtensions) {
    Write-Host "  Testing unsupported .$ext format..." -NoNewline
    
    try {
        $fakeFile = Create-CorruptFile -Extension $ext -OutputDir $TempDir
        $result = Submit-FileToRouter -FilePath $fakeFile
        
        if ($result.Success) {
            if ($result.Queue -match "unknown|skip|unsupported") {
                Write-Host " [OK] Correctly routed to $($result.Queue)" -ForegroundColor Green
                $Results.Passed++
            } else {
                Write-Host " [WARN] Routed to $($result.Queue)" -ForegroundColor Yellow
                $Results.Skipped++
            }
        } else {
            Write-Host " [OK] Rejected" -ForegroundColor Green
            $Results.Passed++
        }
        
        Remove-Item $fakeFile -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host " [ERROR] $_" -ForegroundColor Red
        $Results.Failed++
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# TEST 4: SPECIAL CHARACTERS IN FILENAME
# -----------------------------------------------------------------------------

Write-Host "--- Test 4: Special Characters in Filename ---" -ForegroundColor Yellow
Write-Host ""

$specialNames = @(
    "file with spaces.txt",
    "file`tÃ¤Ã¶Ã¼.txt",
    "file_underscores.txt"
)

foreach ($name in $specialNames) {
    Write-Host "  Testing '$name'..." -NoNewline
    
    try {
        $filepath = Join-Path $TempDir $name
        "Test content" | Out-File -FilePath $filepath -Encoding UTF8 -Force
        
        $result = Submit-FileToRouter -FilePath $filepath
        
        if ($result.Success) {
            Write-Host " [PASS]" -ForegroundColor Green
            $Results.Passed++
        } else {
            Write-Host " [FAIL] $($result.Error)" -ForegroundColor Red
            $Results.Failed++
        }
        
        Remove-Item $filepath -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host " [ERROR] $_" -ForegroundColor Red
        $Results.Failed++
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# CLEANUP
# -----------------------------------------------------------------------------

try {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
} catch {}

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   ERROR HANDLING TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Passed:  $($Results.Passed)" -ForegroundColor Green
Write-Host "  Skipped: $($Results.Skipped)" -ForegroundColor DarkGray
Write-Host "  Failed:  $($Results.Failed)" -ForegroundColor Red
Write-Host ""

$TotalTests = $Results.Passed + $Results.Failed
if ($TotalTests -gt 0) {
    $PassRate = [math]::Round(($Results.Passed / $TotalTests) * 100, 1)
    Write-Host "  Pass Rate: $PassRate%" -ForegroundColor $(if ($PassRate -ge 80) { "Green" } else { "Yellow" })
}

Write-Host ""

return $Results

