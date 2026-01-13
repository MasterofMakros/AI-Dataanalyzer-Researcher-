<#
.SYNOPSIS
    Neural Vault - Cross-Platform Visual Test Suite
    ASCII architecture visualization for all shells (Windows/Linux/macOS)

.DESCRIPTION
    Features:
    - ASCII architecture diagram in terminal
    - Highlighted components per test phase
    - Works on Windows (PowerShell), Linux (bash), macOS (zsh)
    - Progress bars and ETA
    - Color-coded results

.EXAMPLE
    .\test_visual.ps1
    pwsh ./test_visual.ps1  # Cross-platform
#>

param(
    [string]$RouterUrl = "http://127.0.0.1:8030",
    [string]$ApiUrl = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot

# =============================================================================
# ASCII ARCHITECTURE DIAGRAMS
# =============================================================================

function Show-Architecture {
    param(
        [string]$HighlightSection = "",
        [string]$HighlightColor = "Cyan"
    )
    
    # Define sections with their highlight status
    $sections = @{
        "INTAKE" = @"
    +------------------+
    |     INTAKE       |
    +------------------+
    | [File Upload]    |
    |       |          |
    |       v          |
    | [Universal Router]
    |       |          |
    |       v          |
    | {Format Detect}  |
    +------------------+
"@
        "QUEUES" = @"
         |
         v
    +------------------+
    |     QUEUES       |
    +------------------+
    | documents | images|
    | audio   | video  |
    | archive | email  |
    +------------------+
"@
        "WORKERS" = @"
         |
         v
    +------------------+
    |    WORKERS       |
    +------------------+
    | Tika    | Surya  |
    | WhisperX| FFmpeg |
    | 7zip    | Email  |
    +------------------+
"@
        "ENRICHMENT" = @"
         |
         v
    +------------------+
    |   ENRICHMENT     |
    +------------------+
    |   [enrich:ner]   |
    |       |          |
    |   [GLiNER NER]   |
    +------------------+
"@
        "INDEX" = @"
         |
         v
    +------------------+
    |     INDEX        |
    +------------------+
    |  [Qdrant]        |
    |       |          |
    |  [Qdrant Vector] |
    +------------------+
"@
        "SEARCH" = @"
         |
         v
    +------------------+
    |     SEARCH       |
    +------------------+
    |  [Query] -> [Result]
    +------------------+
"@
    }
    
    foreach ($section in @("INTAKE", "QUEUES", "WORKERS", "ENRICHMENT", "INDEX", "SEARCH")) {
        $color = if ($HighlightSection -eq $section) { $HighlightColor } else { "DarkGray" }
        $marker = if ($HighlightSection -eq $section) { " <<<" } else { "" }
        
        $lines = $sections[$section] -split "`n"
        foreach ($line in $lines) {
            Write-Host $line -ForegroundColor $color -NoNewline
            if ($line -match $section -and $HighlightSection -eq $section) {
                Write-Host " <<<" -ForegroundColor Yellow -NoNewline
            }
            Write-Host ""
        }
    }
}

function Show-MiniArchitecture {
    param(
        [string]$ActiveComponent = "",
        [string]$ActiveColor = "Green"
    )
    
    $components = @(
        @{ Name = "INTAKE"; Symbol = "[IN]"; Tests = @("Routing") },
        @{ Name = "QUEUES"; Symbol = "[QU]"; Tests = @("Routing") },
        @{ Name = "WORKERS"; Symbol = "[WK]"; Tests = @("Extraction", "Transcription", "OCR", "Archive") },
        @{ Name = "ENRICH"; Symbol = "[EN]"; Tests = @("Extraction") },
        @{ Name = "INDEX"; Symbol = "[IX]"; Tests = @("Extraction") },
        @{ Name = "SEARCH"; Symbol = "[SR]"; Tests = @("Extraction") }
    )
    
    Write-Host ""
    Write-Host "  Pipeline: " -NoNewline -ForegroundColor White
    
    foreach ($i in 0..($components.Count - 1)) {
        $comp = $components[$i]
        $isActive = $comp.Tests -contains $ActiveComponent
        $color = if ($isActive) { $ActiveColor } else { "DarkGray" }
        
        Write-Host $comp.Symbol -NoNewline -ForegroundColor $color
        
        if ($i -lt $components.Count - 1) {
            Write-Host " -> " -NoNewline -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}

function Show-DetailedArchitecture {
    param([string]$TestName = "")
    
    $activeSection = switch ($TestName) {
        "Routing" { "INTAKE" }
        "Extraction" { "WORKERS" }
        "Transcription" { "WORKERS" }
        "OCR" { "WORKERS" }
        "Archive" { "WORKERS" }
        "ErrorHandling" { "INTAKE" }
        default { "" }
    }
    
    $activeColor = switch ($TestName) {
        "Routing" { "Green" }
        "Extraction" { "Cyan" }
        "Transcription" { "Yellow" }
        "OCR" { "Magenta" }
        "Archive" { "DarkYellow" }
        "ErrorHandling" { "Red" }
        default { "White" }
    }
    
    Write-Host ""
    Write-Host "  +=============================================+" -ForegroundColor DarkGray
    Write-Host "  |           NEURAL VAULT PIPELINE             |" -ForegroundColor DarkGray
    Write-Host "  +=============================================+" -ForegroundColor DarkGray
    
    # INTAKE
    $intakeColor = if ($activeSection -eq "INTAKE") { $activeColor } else { "DarkGray" }
    $intakeMarker = if ($activeSection -eq "INTAKE") { " <-- TESTING" } else { "" }
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[INTAKE]" -NoNewline -ForegroundColor $intakeColor
    Write-Host " File -> Router -> Detect" -NoNewline -ForegroundColor $intakeColor
    Write-Host $intakeMarker -ForegroundColor Yellow
    Write-Host "  |       |" -ForegroundColor DarkGray
    
    # QUEUES
    $queueColor = if ($activeSection -eq "QUEUES") { $activeColor } else { "DarkGray" }
    Write-Host "  |       v" -ForegroundColor DarkGray
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[QUEUES]" -NoNewline -ForegroundColor $queueColor
    Write-Host " doc|img|audio|video|archive" -ForegroundColor $queueColor
    Write-Host "  |       |" -ForegroundColor DarkGray
    
    # WORKERS
    $workerColor = if ($activeSection -eq "WORKERS") { $activeColor } else { "DarkGray" }
    $workerMarker = if ($activeSection -eq "WORKERS") { " <-- TESTING" } else { "" }
    $workerDetail = switch ($TestName) {
        "Extraction" { "Tika/Docling" }
        "Transcription" { "WhisperX" }
        "OCR" { "Surya OCR" }
        "Archive" { "7zip" }
        default { "All Workers" }
    }
    Write-Host "  |       v" -ForegroundColor DarkGray
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[WORKERS]" -NoNewline -ForegroundColor $workerColor
    Write-Host " $workerDetail" -NoNewline -ForegroundColor $workerColor
    Write-Host $workerMarker -ForegroundColor Yellow
    Write-Host "  |       |" -ForegroundColor DarkGray
    
    # ENRICHMENT
    $enrichColor = if ($activeSection -eq "ENRICHMENT") { $activeColor } else { "DarkGray" }
    Write-Host "  |       v" -ForegroundColor DarkGray
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[ENRICH]" -NoNewline -ForegroundColor $enrichColor
    Write-Host " NER Entity Extraction" -ForegroundColor $enrichColor
    Write-Host "  |       |" -ForegroundColor DarkGray
    
    # INDEX
    $indexColor = if ($activeSection -eq "INDEX") { $activeColor } else { "DarkGray" }
    Write-Host "  |       v" -ForegroundColor DarkGray
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[INDEX]" -NoNewline -ForegroundColor $indexColor
    Write-Host " Qdrant" -ForegroundColor $indexColor
    Write-Host "  |       |" -ForegroundColor DarkGray
    
    # SEARCH
    $searchColor = if ($activeSection -eq "SEARCH") { $activeColor } else { "DarkGray" }
    Write-Host "  |       v" -ForegroundColor DarkGray
    Write-Host "  |  " -NoNewline -ForegroundColor DarkGray
    Write-Host "[SEARCH]" -NoNewline -ForegroundColor $searchColor
    Write-Host " Query -> Results" -ForegroundColor $searchColor
    
    Write-Host "  +=============================================+" -ForegroundColor DarkGray
    Write-Host ""
}

# =============================================================================
# PROGRESS BAR
# =============================================================================

function Show-Progress {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Status,
        [int]$Width = 30
    )
    
    $percent = [math]::Floor(($Current / $Total) * 100)
    $filled = [math]::Floor($Width * $Current / $Total)
    $empty = $Width - $filled
    
    $bar = "[" + ("#" * $filled) + ("-" * $empty) + "]"
    
    Write-Host "`r  $bar $percent% - $Status                    " -NoNewline
}

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

$TestSuites = [ordered]@{
    "Routing" = @{ Script = "test_all_formats.ps1"; Desc = "Format Detection" }
    "Extraction" = @{ Script = "test_extraction_quality.ps1"; Desc = "Content Quality" }
    "Transcription" = @{ Script = "test_transcription.ps1"; Desc = "Audio/Video" }
    "OCR" = @{ Script = "test_ocr_accuracy.ps1"; Desc = "Image Text" }
    "Archive" = @{ Script = "test_archive_extraction.ps1"; Desc = "Unpacking" }
    "ErrorHandling" = @{ Script = "test_error_handling.ps1"; Desc = "DLQ/Errors" }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Clear-Host

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "       NEURAL VAULT - VISUAL TEST SUITE       " -ForegroundColor Cyan
Write-Host "       Cross-Platform Shell Visualization      " -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "       $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ""

$results = @()
$current = 0
$total = $TestSuites.Count

foreach ($testName in $TestSuites.Keys) {
    $current++
    $config = $TestSuites[$testName]
    
    # Show architecture with highlighted section
    Show-DetailedArchitecture -TestName $testName
    
    Write-Host "  Testing: " -NoNewline -ForegroundColor White
    Write-Host "$testName" -NoNewline -ForegroundColor Cyan
    Write-Host " ($($config.Desc))" -ForegroundColor DarkGray
    
    Show-Progress -Current $current -Total $total -Status "Running..."
    
    # Run test
    $scriptPath = Join-Path $ScriptDir $config.Script
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    $passed = 0; $failed = 0; $skipped = 0; $status = "SKIP"
    
    if (Test-Path $scriptPath) {
        try {
            $output = & $scriptPath 2>&1
            $outputStr = $output -join "`n"
            
            if ($outputStr -match "Passed:\s*(\d+)") { $passed = [int]$Matches[1] }
            if ($outputStr -match "Failed:\s*(\d+)") { $failed = [int]$Matches[1] }
            if ($outputStr -match "Skipped:\s*(\d+)") { $skipped = [int]$Matches[1] }
            
            if ($failed -gt 0) { $status = "FAIL" }
            elseif ($passed -gt 0) { $status = "PASS" }
        } catch { $status = "ERROR"; $failed = 1 }
    }
    
    $stopwatch.Stop()
    
    # Show result
    $statusColor = switch ($status) { "PASS" { "Green" } "FAIL" { "Red" } "SKIP" { "DarkGray" } default { "Yellow" } }
    
    Write-Host ""
    Write-Host "  Result: " -NoNewline
    Write-Host "[$status]" -NoNewline -ForegroundColor $statusColor
    Write-Host " Pass:$passed Fail:$failed Skip:$skipped ($([math]::Round($stopwatch.ElapsedMilliseconds/1000, 1))s)"
    Write-Host ""
    Write-Host "  ---------------------------------------------" -ForegroundColor DarkGray
    
    $results += @{ Name = $testName; Status = $status; Passed = $passed; Failed = $failed; Skipped = $skipped }
    
    Start-Sleep -Milliseconds 500
}

# Final Summary
Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "                 TEST SUMMARY                  " -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""

foreach ($r in $results) {
    $color = switch ($r.Status) { "PASS" { "Green" } "FAIL" { "Red" } default { "DarkGray" } }
    Write-Host "  $($r.Name.PadRight(15)) " -NoNewline
    Write-Host "[$($r.Status)]" -ForegroundColor $color
}

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

Write-Host ""
Write-Host "  Overall: " -NoNewline
if ($failCount -eq 0) {
    Write-Host "[PASS]" -ForegroundColor Green
} else {
    Write-Host "[FAIL]" -ForegroundColor Red
}
Write-Host ""
