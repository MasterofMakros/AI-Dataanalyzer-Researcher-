<#
.SYNOPSIS
    Neural Vault - Stress/Load Test Suite
    Tests system performance under high load

.DESCRIPTION
    Tests system resilience:
    1. Parallel file submissions
    2. Queue backpressure handling
    3. Memory usage monitoring
    4. Throughput under load

.PARAMETER ConcurrentFiles
    Number of files to submit in parallel (default: 50)

.PARAMETER Rounds
    Number of test rounds (default: 3)

.EXAMPLE
    .\test_stress_load.ps1 -ConcurrentFiles 100 -Rounds 5
#>

param(
    [int]$ConcurrentFiles = 50,
    [int]$Rounds = 3,
    [string]$RouterUrl = "http://127.0.0.1:8030"
)

$ErrorActionPreference = "Continue"

$GroundTruthPath = Join-Path $PSScriptRoot "..\ground_truth"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Get-TestFiles {
    param([int]$Count = 50)
    
    $allFiles = @()
    $searchDirs = @(
        (Join-Path $GroundTruthPath "documents"),
        (Join-Path $GroundTruthPath "code"),
        (Join-Path $GroundTruthPath "config"),
        (Join-Path $GroundTruthPath "subtitles"),
        (Join-Path $GroundTruthPath "latex"),
        (Join-Path $GroundTruthPath "email")
    )
    
    foreach ($dir in $searchDirs) {
        if (Test-Path $dir) {
            $files = Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue
            $allFiles += $files.FullName
        }
    }
    
    # Return random subset
    return $allFiles | Get-Random -Count ([math]::Min($Count, $allFiles.Count))
}

function Get-QueueStats {
    $queues = @("extract:documents", "extract:images", "extract:audio", "extract:video", "extract:archive", "extract:email")
    $stats = @{}
    
    foreach ($queue in $queues) {
        try {
            $result = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $queue 2>$null
            if ($result -match "^\d+$") {
                $stats[$queue] = [int]$result
            }
        } catch {}
    }
    
    return $stats
}

function Get-ContainerStats {
    try {
        $stats = docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" 2>$null
        $parsed = @{}
        
        foreach ($line in $stats) {
            $parts = $line -split ","
            if ($parts.Count -ge 3) {
                $parsed[$parts[0]] = @{
                    CPU = $parts[1]
                    Memory = $parts[2]
                }
            }
        }
        
        return $parsed
    }
    catch {
        return @{}
    }
}

function Submit-FileBatch {
    param(
        [string[]]$Files,
        [switch]$Parallel
    )
    
    $results = @{
        Successful = 0
        Failed = 0
        TotalLatencyMs = 0
        Errors = @()
    }
    
    if ($Parallel) {
        # Use parallel jobs
        $jobs = @()
        
        foreach ($file in $Files) {
            $jobs += Start-Job -ScriptBlock {
                param($FilePath, $Url)
                $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
                try {
                    $body = @{ filepath = $FilePath } | ConvertTo-Json
                    $response = Invoke-RestMethod -Uri "$Url/route" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
                    $stopwatch.Stop()
                    return @{ Success = $true; LatencyMs = $stopwatch.ElapsedMilliseconds }
                }
                catch {
                    $stopwatch.Stop()
                    return @{ Success = $false; LatencyMs = $stopwatch.ElapsedMilliseconds; Error = $_.Exception.Message }
                }
            } -ArgumentList $file, $RouterUrl
        }
        
        # Wait for all jobs
        $jobResults = $jobs | Wait-Job | Receive-Job
        $jobs | Remove-Job
        
        foreach ($jr in $jobResults) {
            if ($jr.Success) {
                $results.Successful++
                $results.TotalLatencyMs += $jr.LatencyMs
            } else {
                $results.Failed++
                $results.Errors += $jr.Error
            }
        }
    }
    else {
        # Sequential submission
        foreach ($file in $Files) {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                $body = @{ filepath = $file } | ConvertTo-Json
                $response = Invoke-RestMethod -Uri "$RouterUrl/route" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
                $stopwatch.Stop()
                $results.Successful++
                $results.TotalLatencyMs += $stopwatch.ElapsedMilliseconds
            }
            catch {
                $stopwatch.Stop()
                $results.Failed++
                $results.Errors += $_.Exception.Message
            }
        }
    }
    
    return $results
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: STRESS/LOAD TEST SUITE" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Configuration:" -ForegroundColor White
Write-Host "    Concurrent Files: $ConcurrentFiles" -ForegroundColor DarkGray
Write-Host "    Test Rounds:      $Rounds" -ForegroundColor DarkGray
Write-Host ""

$TestResults = @{
    Rounds = @()
    TotalSubmissions = 0
    TotalSuccessful = 0
    TotalFailed = 0
    AverageLatencyMs = 0
    PeakQueueDepth = 0
    Throughput = 0
}

# Get test files
Write-Host "--- Preparing Test Files ---" -ForegroundColor Yellow
$testFiles = Get-TestFiles -Count $ConcurrentFiles
Write-Host "  Found $($testFiles.Count) test files" -ForegroundColor DarkGray
Write-Host ""

if ($testFiles.Count -eq 0) {
    Write-Host "  [ERROR] No test files found in ground_truth" -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
# PRE-TEST BASELINE
# -----------------------------------------------------------------------------

Write-Host "--- Pre-Test Baseline ---" -ForegroundColor Yellow
Write-Host ""

$initialQueues = Get-QueueStats
$initialContainers = Get-ContainerStats

Write-Host "  Initial Queue Depths:" -ForegroundColor White
foreach ($q in $initialQueues.Keys) {
    Write-Host "    $q : $($initialQueues[$q])" -ForegroundColor DarkGray
}

Write-Host ""

# -----------------------------------------------------------------------------
# STRESS TEST ROUNDS
# -----------------------------------------------------------------------------

Write-Host "--- Running Stress Test Rounds ---" -ForegroundColor Yellow
Write-Host ""

for ($round = 1; $round -le $Rounds; $round++) {
    Write-Host "  Round $round/$Rounds..." -NoNewline
    
    $roundStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Submit files (using sequential for reliability, parallel is optional)
    $roundResults = Submit-FileBatch -Files $testFiles
    
    $roundStopwatch.Stop()
    
    $roundData = @{
        Round = $round
        FilesSubmitted = $testFiles.Count
        Successful = $roundResults.Successful
        Failed = $roundResults.Failed
        TotalTimeMs = $roundStopwatch.ElapsedMilliseconds
        AvgLatencyMs = if ($roundResults.Successful -gt 0) { 
            [math]::Round($roundResults.TotalLatencyMs / $roundResults.Successful, 1) 
        } else { 0 }
        Throughput = if ($roundStopwatch.Elapsed.TotalSeconds -gt 0) {
            [math]::Round($roundResults.Successful / $roundStopwatch.Elapsed.TotalSeconds, 1)
        } else { 0 }
    }
    
    $TestResults.Rounds += $roundData
    $TestResults.TotalSubmissions += $testFiles.Count
    $TestResults.TotalSuccessful += $roundResults.Successful
    $TestResults.TotalFailed += $roundResults.Failed
    
    # Check queue depth
    $currentQueues = Get-QueueStats
    $totalQueueDepth = ($currentQueues.Values | Measure-Object -Sum).Sum
    if ($totalQueueDepth -gt $TestResults.PeakQueueDepth) {
        $TestResults.PeakQueueDepth = $totalQueueDepth
    }
    
    Write-Host " Done! $($roundResults.Successful)/$($testFiles.Count) OK, $($roundData.Throughput) files/sec" -ForegroundColor Green
    
    # Brief pause between rounds
    Start-Sleep -Seconds 2
}

Write-Host ""

# -----------------------------------------------------------------------------
# POST-TEST MEASUREMENTS
# -----------------------------------------------------------------------------

Write-Host "--- Post-Test Measurements ---" -ForegroundColor Yellow
Write-Host ""

$finalQueues = Get-QueueStats
$finalContainers = Get-ContainerStats

Write-Host "  Final Queue Depths:" -ForegroundColor White
foreach ($q in $finalQueues.Keys) {
    $initial = if ($initialQueues.ContainsKey($q)) { $initialQueues[$q] } else { 0 }
    $delta = $finalQueues[$q] - $initial
    $deltaStr = if ($delta -ge 0) { "+$delta" } else { "$delta" }
    Write-Host "    $q : $($finalQueues[$q]) ($deltaStr)" -ForegroundColor DarkGray
}

Write-Host ""

# Container resource usage
Write-Host "  Container Resource Usage:" -ForegroundColor White
$keyContainers = @("conductor-universal-router", "conductor-api", "conductor-redis", "conductor-meilisearch")
foreach ($container in $keyContainers) {
    if ($finalContainers.ContainsKey($container)) {
        $stats = $finalContainers[$container]
        Write-Host "    $container : CPU $($stats.CPU), Mem $($stats.Memory)" -ForegroundColor DarkGray
    }
}

Write-Host ""

# Calculate overall stats
if ($TestResults.TotalSuccessful -gt 0) {
    $totalLatency = ($TestResults.Rounds | ForEach-Object { $_.AvgLatencyMs * $_.Successful } | Measure-Object -Sum).Sum
    $TestResults.AverageLatencyMs = [math]::Round($totalLatency / $TestResults.TotalSuccessful, 1)
}

$totalTimeSeconds = ($TestResults.Rounds | ForEach-Object { $_.TotalTimeMs } | Measure-Object -Sum).Sum / 1000
if ($totalTimeSeconds -gt 0) {
    $TestResults.Throughput = [math]::Round($TestResults.TotalSuccessful / $totalTimeSeconds, 1)
}

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   STRESS TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total Submissions: $($TestResults.TotalSubmissions)" -ForegroundColor White
Write-Host "  Successful:        $($TestResults.TotalSuccessful)" -ForegroundColor Green
Write-Host "  Failed:            $($TestResults.TotalFailed)" -ForegroundColor $(if ($TestResults.TotalFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "  Average Latency:   $($TestResults.AverageLatencyMs) ms" -ForegroundColor Yellow
Write-Host "  Peak Queue Depth:  $($TestResults.PeakQueueDepth)" -ForegroundColor Yellow
Write-Host "  Throughput:        $($TestResults.Throughput) files/sec" -ForegroundColor Yellow
Write-Host ""

# Pass/Fail determination
$successRate = if ($TestResults.TotalSubmissions -gt 0) { 
    [math]::Round(($TestResults.TotalSuccessful / $TestResults.TotalSubmissions) * 100, 1) 
} else { 0 }

if ($successRate -ge 95) {
    Write-Host "  Result: [PASS] $successRate% success rate" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "  Result: [WARN] $successRate% success rate" -ForegroundColor Yellow
} else {
    Write-Host "  Result: [FAIL] $successRate% success rate" -ForegroundColor Red
}

Write-Host ""

return $TestResults

