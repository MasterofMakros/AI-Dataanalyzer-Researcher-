<#
.SYNOPSIS
    Neural Vault - CI/CD Test Runner
    Pester-compatible test wrapper for all test suites

.DESCRIPTION
    Orchestrates all test suites and generates CI/CD-compatible output:
    - JUnit XML report for CI systems
    - Summary JSON for dashboards
    - Exit codes for pipeline gates

.PARAMETER Suite
    Specific test suite to run: All, Routing, Quality, Benchmark, Transcription, OCR, Archive, Error, Stress

.PARAMETER OutputDir
    Directory for test reports

.EXAMPLE
    .\run_all_tests.ps1 -Suite All
    .\run_all_tests.ps1 -Suite Routing -OutputDir "./reports"
#>

param(
    [ValidateSet("All", "Routing", "Quality", "Benchmark", "Transcription", "OCR", "Archive", "Error", "Stress")]
    [string]$Suite = "All",
    [string]$OutputDir = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Continue"
$ScriptDir = $PSScriptRoot

if (-not $OutputDir) {
    $OutputDir = Join-Path $ScriptDir "reports"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# =============================================================================
# TEST SUITE DEFINITIONS
# =============================================================================

$TestSuites = @{
    "Routing" = @{
        Script = "test_all_formats.ps1"
        Description = "Format routing validation"
        Priority = 1
    }
    "Quality" = @{
        Script = "test_extraction_quality.ps1"
        Description = "Content extraction quality"
        Priority = 2
    }
    "Benchmark" = @{
        Script = "benchmark_formats.ps1"
        Args = @("-SampleSize", "2", "-WaitSeconds", "10")
        Description = "Performance benchmarks"
        Priority = 3
    }
    "Transcription" = @{
        Script = "test_transcription.ps1"
        Description = "Audio/Video transcription (WhisperX)"
        Priority = 4
    }
    "OCR" = @{
        Script = "test_ocr_accuracy.ps1"
        Description = "OCR accuracy (Surya)"
        Priority = 5
    }
    "Archive" = @{
        Script = "test_archive_extraction.ps1"
        Description = "Archive extraction (7zip)"
        Priority = 6
    }
    "Error" = @{
        Script = "test_error_handling.ps1"
        Description = "Error handling and DLQ"
        Priority = 7
    }
    "Stress" = @{
        Script = "test_stress_load.ps1"
        Args = @("-ConcurrentFiles", "20", "-Rounds", "2")
        Description = "Stress/load testing"
        Priority = 8
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Run-TestSuite {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    $scriptPath = Join-Path $ScriptDir $Config.Script
    
    if (-not (Test-Path $scriptPath)) {
        return @{
            Name = $Name
            Status = "SKIP"
            Reason = "Script not found: $($Config.Script)"
            Duration = 0
            Passed = 0
            Failed = 0
            Skipped = 1
        }
    }
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $args = if ($Config.Args) { $Config.Args } else { @() }
        
        # Capture output
        $output = & $scriptPath @args 2>&1
        $exitCode = $LASTEXITCODE
        
        $stopwatch.Stop()
        
        # Parse results from output (look for standard result patterns)
        $passed = 0
        $failed = 0
        $skipped = 0
        
        if ($output -is [hashtable]) {
            if ($output.Passed) { $passed = $output.Passed }
            if ($output.Failed) { $failed = $output.Failed }
            if ($output.Skipped) { $skipped = $output.Skipped }
        } else {
            $outputStr = $output -join "`n"
            if ($outputStr -match "Passed:\s*(\d+)") { $passed = [int]$Matches[1] }
            if ($outputStr -match "Failed:\s*(\d+)") { $failed = [int]$Matches[1] }
            if ($outputStr -match "Skipped:\s*(\d+)") { $skipped = [int]$Matches[1] }
        }
        
        $status = if ($failed -gt 0) { "FAIL" } elseif ($passed -gt 0) { "PASS" } else { "SKIP" }
        
        return @{
            Name = $Name
            Status = $status
            Duration = $stopwatch.ElapsedMilliseconds
            Passed = $passed
            Failed = $failed
            Skipped = $skipped
            ExitCode = $exitCode
        }
    }
    catch {
        $stopwatch.Stop()
        return @{
            Name = $Name
            Status = "ERROR"
            Error = $_.Exception.Message
            Duration = $stopwatch.ElapsedMilliseconds
            Passed = 0
            Failed = 1
            Skipped = 0
        }
    }
}

function Generate-JUnitXml {
    param(
        [array]$Results,
        [string]$OutputPath
    )
    
    $totalTests = ($Results | ForEach-Object { $_.Passed + $_.Failed + $_.Skipped } | Measure-Object -Sum).Sum
    $totalFailures = ($Results | ForEach-Object { $_.Failed } | Measure-Object -Sum).Sum
    $totalSkipped = ($Results | ForEach-Object { $_.Skipped } | Measure-Object -Sum).Sum
    $totalTime = ($Results | ForEach-Object { $_.Duration } | Measure-Object -Sum).Sum / 1000
    
    $xml = @"
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Neural Vault Test Suite" tests="$totalTests" failures="$totalFailures" skipped="$totalSkipped" time="$totalTime">
"@
    
    foreach ($result in $Results) {
        $suiteTests = $result.Passed + $result.Failed + $result.Skipped
        $suiteTime = $result.Duration / 1000
        
        $xml += "`n  <testsuite name=`"$($result.Name)`" tests=`"$suiteTests`" failures=`"$($result.Failed)`" skipped=`"$($result.Skipped)`" time=`"$suiteTime`">"
        
        # Add test case for the suite
        $xml += "`n    <testcase name=`"$($result.Name)`" classname=`"NeuralVault.$($result.Name)`" time=`"$suiteTime`">"
        
        if ($result.Status -eq "FAIL" -or $result.Status -eq "ERROR") {
            $errorMsg = if ($result.Error) { $result.Error } else { "Test failed" }
            $xml += "`n      <failure message=`"$errorMsg`">$errorMsg</failure>"
        }
        elseif ($result.Status -eq "SKIP") {
            $xml += "`n      <skipped/>"
        }
        
        $xml += "`n    </testcase>"
        $xml += "`n  </testsuite>"
    }
    
    $xml += "`n</testsuites>"
    
    $xml | Out-File -FilePath $OutputPath -Encoding UTF8
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if (-not $Quiet) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "   NEURAL VAULT: CI/CD TEST RUNNER" -ForegroundColor Cyan
    Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Suite: $Suite" -ForegroundColor White
    Write-Host "  Output: $OutputDir" -ForegroundColor DarkGray
    Write-Host ""
}

# Determine which suites to run
$suitesToRun = if ($Suite -eq "All") {
    $TestSuites.Keys | Sort-Object { $TestSuites[$_].Priority }
} else {
    @($Suite)
}

$AllResults = @()
$overallStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

foreach ($suiteName in $suitesToRun) {
    if (-not $TestSuites.ContainsKey($suiteName)) {
        Write-Host "  [WARN] Unknown suite: $suiteName" -ForegroundColor Yellow
        continue
    }
    
    $config = $TestSuites[$suiteName]
    
    if (-not $Quiet) {
        Write-Host "  Running: $suiteName ($($config.Description))..." -NoNewline
    }
    
    $result = Run-TestSuite -Name $suiteName -Config $config
    $AllResults += $result
    
    if (-not $Quiet) {
        $statusColor = switch ($result.Status) {
            "PASS" { "Green" }
            "FAIL" { "Red" }
            "ERROR" { "Red" }
            "SKIP" { "DarkGray" }
            default { "White" }
        }
        Write-Host " [$($result.Status)]" -ForegroundColor $statusColor -NoNewline
        Write-Host " ($($result.Duration)ms, P:$($result.Passed) F:$($result.Failed) S:$($result.Skipped))"
    }
}

$overallStopwatch.Stop()

# Generate reports
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

# JUnit XML
$junitPath = Join-Path $OutputDir "junit_results_$timestamp.xml"
Generate-JUnitXml -Results $AllResults -OutputPath $junitPath

# JSON Summary
$summaryPath = Join-Path $OutputDir "summary_$timestamp.json"
$summary = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    TotalDurationMs = $overallStopwatch.ElapsedMilliseconds
    Suites = $AllResults
    Totals = @{
        Passed = ($AllResults | ForEach-Object { $_.Passed } | Measure-Object -Sum).Sum
        Failed = ($AllResults | ForEach-Object { $_.Failed } | Measure-Object -Sum).Sum
        Skipped = ($AllResults | ForEach-Object { $_.Skipped } | Measure-Object -Sum).Sum
    }
    OverallStatus = if (($AllResults | Where-Object { $_.Status -eq "FAIL" -or $_.Status -eq "ERROR" }).Count -gt 0) { "FAIL" } else { "PASS" }
}
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryPath -Encoding UTF8

# =============================================================================
# SUMMARY
# =============================================================================

if (-not $Quiet) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "   TEST RUN SUMMARY" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Suites Run:    $($AllResults.Count)" -ForegroundColor White
    Write-Host "  Total Passed:  $($summary.Totals.Passed)" -ForegroundColor Green
    Write-Host "  Total Failed:  $($summary.Totals.Failed)" -ForegroundColor $(if ($summary.Totals.Failed -gt 0) { "Red" } else { "Green" })
    Write-Host "  Total Skipped: $($summary.Totals.Skipped)" -ForegroundColor DarkGray
    Write-Host "  Duration:      $($overallStopwatch.ElapsedMilliseconds)ms" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Reports:" -ForegroundColor White
    Write-Host "    JUnit XML: $junitPath" -ForegroundColor DarkGray
    Write-Host "    JSON:      $summaryPath" -ForegroundColor DarkGray
    Write-Host ""
    
    $overallColor = if ($summary.OverallStatus -eq "PASS") { "Green" } else { "Red" }
    Write-Host "  Overall: [$($summary.OverallStatus)]" -ForegroundColor $overallColor
    Write-Host ""
}

# Exit with appropriate code for CI/CD
$exitCode = if ($summary.OverallStatus -eq "PASS") { 0 } else { 1 }
exit $exitCode

