<#
.SYNOPSIS
    Neural Vault - Format Processing Benchmark Suite
    Measures performance metrics for file processing pipeline

.DESCRIPTION
    Benchmarks the complete processing pipeline:
    1. Submission latency (time to queue)
    2. Processing time per format category
    3. Throughput (files/minute)
    4. Queue drain rates
    5. Index growth rates

.PARAMETER SampleSize
    Number of files per format to test (default: 3)

.PARAMETER WaitSeconds
    Seconds to wait for processing before measuring (default: 30)

.PARAMETER OutputReport
    Path to save JSON benchmark report

.EXAMPLE
    .\benchmark_formats.ps1
    .\benchmark_formats.ps1 -SampleSize 5 -WaitSeconds 60 -OutputReport "benchmark_results.json"
#>

param(
    [int]$SampleSize = 3,
    [int]$WaitSeconds = 30,
    [string]$RouterUrl = "http://127.0.0.1:8030",
    [string]$ApiUrl = "http://127.0.0.1:8010",
    [string]$OutputReport = ""
)

$ErrorActionPreference = "Continue"

# =============================================================================
# CONFIGURATION
# =============================================================================

$GroundTruthPath = Join-Path $PSScriptRoot "..\ground_truth"
$ManifestPath = Join-Path $GroundTruthPath "manifest.json"

# Format categories with expected processing characteristics
$FormatCategories = @{
    "documents" = @{
        Extensions = @("pdf", "docx", "xlsx", "txt", "html", "json", "csv", "md")
        ExpectedQueue = "extract:documents"
        Processor = "Tika/Docling"
    }
    "code" = @{
        Extensions = @("py", "js", "ts", "java", "go", "rs", "sql", "sh")
        ExpectedQueue = "extract:documents"
        Processor = "Text Extraction"
    }
    "images" = @{
        Extensions = @("jpg", "png", "gif", "bmp", "webp", "tiff")
        ExpectedQueue = "extract:images"
        Processor = "Surya OCR"
    }
    "audio" = @{
        Extensions = @("mp3", "wav", "flac", "ogg", "m4a")
        ExpectedQueue = "extract:audio"
        Processor = "WhisperX"
    }
    "video" = @{
        Extensions = @("mp4", "mkv", "avi", "mov", "webm")
        ExpectedQueue = "extract:video"
        Processor = "FFmpeg + WhisperX"
    }
    "email" = @{
        Extensions = @("eml", "msg")
        ExpectedQueue = "extract:email"
        Processor = "Email Parser"
    }
    "archive" = @{
        Extensions = @("zip", "7z", "rar", "tar", "gz")
        ExpectedQueue = "extract:archive"
        Processor = "7zip"
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Get-QueueStats {
    param([string]$Queue)
    
    try {
        # Use docker exec to query Redis
        $result = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $Queue 2>$null
        if ($result -match "^\d+$") {
            return [int]$result
        }
    }
    catch {}
    return 0
}

function Get-IndexStats {
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/index/stats" -Method GET -TimeoutSec 10
        return $response
    }
    catch {
        return $null
    }
}

function Submit-File {
    param([string]$FilePath)
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $body = @{ filepath = $FilePath } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$RouterUrl/route" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        $stopwatch.Stop()
        
        return @{
            Success = $true
            LatencyMs = $stopwatch.ElapsedMilliseconds
            Queue = $response.queue
            MessageId = $response.message_id
        }
    }
    catch {
        $stopwatch.Stop()
        return @{
            Success = $false
            LatencyMs = $stopwatch.ElapsedMilliseconds
            Error = $_.Exception.Message
        }
    }
}

function Find-TestFiles {
    param(
        [string]$Extension,
        [int]$MaxCount = 3
    )
    
    $files = @()
    
    # Search in ground_truth directories
    $searchDirs = @(
        (Join-Path $GroundTruthPath "documents"),
        (Join-Path $GroundTruthPath "code"),
        (Join-Path $GroundTruthPath "images"),
        (Join-Path $GroundTruthPath "audio"),
        (Join-Path $GroundTruthPath "video"),
        (Join-Path $GroundTruthPath "email"),
        (Join-Path $GroundTruthPath "archive"),
        (Join-Path $GroundTruthPath "config"),
        (Join-Path $GroundTruthPath "subtitles"),
        (Join-Path $GroundTruthPath "latex"),
        (Join-Path $GroundTruthPath "ebooks"),
        (Join-Path $GroundTruthPath "fonts"),
        (Join-Path $GroundTruthPath "binary"),
        (Join-Path $GroundTruthPath "apps"),
        (Join-Path $GroundTruthPath "misc")
    )
    
    foreach ($dir in $searchDirs) {
        if (Test-Path $dir) {
            $found = Get-ChildItem -Path $dir -Filter "*.$Extension" -File -ErrorAction SilentlyContinue | Select-Object -First $MaxCount
            if ($found) {
                $files += $found.FullName
            }
        }
        if ($files.Count -ge $MaxCount) { break }
    }
    
    return $files | Select-Object -First $MaxCount
}

# =============================================================================
# MAIN BENCHMARK EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: FORMAT PROCESSING BENCHMARK" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$BenchmarkResults = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Configuration = @{
        SampleSize = $SampleSize
        WaitSeconds = $WaitSeconds
    }
    Categories = @{}
    Summary = @{
        TotalFilesSubmitted = 0
        TotalSuccessful = 0
        TotalFailed = 0
        AverageLatencyMs = 0
        TotalProcessingTimeMs = 0
    }
}

# -----------------------------------------------------------------------------
# PRE-BENCHMARK: CAPTURE BASELINE
# -----------------------------------------------------------------------------

Write-Host "--- Pre-Benchmark Baseline ---" -ForegroundColor Yellow
Write-Host ""

$InitialIndexStats = Get-IndexStats
$InitialIndexCount = if ($InitialIndexStats) { $InitialIndexStats.numberOfDocuments } else { 0 }
Write-Host "  Initial Index Size: $InitialIndexCount documents" -ForegroundColor DarkGray

$InitialQueueStates = @{}
foreach ($category in $FormatCategories.Keys) {
    $queue = $FormatCategories[$category].ExpectedQueue
    if (-not $InitialQueueStates.ContainsKey($queue)) {
        $InitialQueueStates[$queue] = Get-QueueStats -Queue $queue
    }
}

Write-Host "  Queue Baseline Captured" -ForegroundColor DarkGray
Write-Host ""

# -----------------------------------------------------------------------------
# SUBMISSION BENCHMARK
# -----------------------------------------------------------------------------

Write-Host "--- Submission Latency Benchmark ---" -ForegroundColor Yellow
Write-Host ""

$AllLatencies = @()

foreach ($category in $FormatCategories.Keys) {
    $config = $FormatCategories[$category]
    $categoryResults = @{
        Extensions = @{}
        TotalFiles = 0
        SuccessfulSubmissions = 0
        FailedSubmissions = 0
        AverageLatencyMs = 0
        Processor = $config.Processor
    }
    
    Write-Host "  Category: $category ($($config.Processor))" -ForegroundColor White
    
    $categoryLatencies = @()
    
    foreach ($ext in $config.Extensions) {
        $testFiles = Find-TestFiles -Extension $ext -MaxCount $SampleSize
        
        if ($testFiles.Count -eq 0) {
            Write-Host "    .$ext : No test files found" -ForegroundColor DarkGray
            continue
        }
        
        $extResults = @{
            FilesFound = $testFiles.Count
            Submitted = 0
            Failed = 0
            Latencies = @()
        }
        
        foreach ($file in $testFiles) {
            $result = Submit-File -FilePath $file
            
            if ($result.Success) {
                $extResults.Submitted++
                $extResults.Latencies += $result.LatencyMs
                $categoryLatencies += $result.LatencyMs
                $AllLatencies += $result.LatencyMs
                $BenchmarkResults.Summary.TotalSuccessful++
            } else {
                $extResults.Failed++
                $BenchmarkResults.Summary.TotalFailed++
            }
            
            $categoryResults.TotalFiles++
            $BenchmarkResults.Summary.TotalFilesSubmitted++
        }
        
        $avgLatency = if ($extResults.Latencies.Count -gt 0) { 
            [math]::Round(($extResults.Latencies | Measure-Object -Average).Average, 1)
        } else { 0 }
        
        $extResults.AverageLatencyMs = $avgLatency
        $categoryResults.Extensions[$ext] = $extResults
        
        $status = if ($extResults.Failed -gt 0) { "[WARN]" } else { "[OK]" }
        $statusColor = if ($extResults.Failed -gt 0) { "Yellow" } else { "Green" }
        Write-Host "    .$ext : $($extResults.Submitted)/$($extResults.FilesFound) submitted, avg ${avgLatency}ms $status" -ForegroundColor $statusColor
        
        $categoryResults.SuccessfulSubmissions += $extResults.Submitted
        $categoryResults.FailedSubmissions += $extResults.Failed
    }
    
    $categoryResults.AverageLatencyMs = if ($categoryLatencies.Count -gt 0) {
        [math]::Round(($categoryLatencies | Measure-Object -Average).Average, 1)
    } else { 0 }
    
    $BenchmarkResults.Categories[$category] = $categoryResults
    Write-Host ""
}

# Calculate overall average latency
$BenchmarkResults.Summary.AverageLatencyMs = if ($AllLatencies.Count -gt 0) {
    [math]::Round(($AllLatencies | Measure-Object -Average).Average, 1)
} else { 0 }

# -----------------------------------------------------------------------------
# WAIT FOR PROCESSING
# -----------------------------------------------------------------------------

Write-Host "--- Waiting for Processing ($WaitSeconds seconds) ---" -ForegroundColor Yellow
Write-Host ""

$progressInterval = 5
for ($i = 0; $i -lt $WaitSeconds; $i += $progressInterval) {
    $remaining = $WaitSeconds - $i
    Write-Host "  Waiting... ${remaining}s remaining" -ForegroundColor DarkGray
    Start-Sleep -Seconds ([math]::Min($progressInterval, $remaining))
}

Write-Host ""

# -----------------------------------------------------------------------------
# POST-BENCHMARK: MEASURE RESULTS
# -----------------------------------------------------------------------------

Write-Host "--- Post-Benchmark Measurements ---" -ForegroundColor Yellow
Write-Host ""

$FinalIndexStats = Get-IndexStats
$FinalIndexCount = if ($FinalIndexStats) { $FinalIndexStats.numberOfDocuments } else { 0 }
$DocsIndexed = $FinalIndexCount - $InitialIndexCount

Write-Host "  Final Index Size: $FinalIndexCount documents (+$DocsIndexed)" -ForegroundColor White

$FinalQueueStates = @{}
foreach ($category in $FormatCategories.Keys) {
    $queue = $FormatCategories[$category].ExpectedQueue
    if (-not $FinalQueueStates.ContainsKey($queue)) {
        $FinalQueueStates[$queue] = Get-QueueStats -Queue $queue
    }
}

Write-Host ""
Write-Host "  Queue Changes:" -ForegroundColor White

foreach ($queue in $InitialQueueStates.Keys) {
    $initial = $InitialQueueStates[$queue]
    $final = $FinalQueueStates[$queue]
    $change = $final - $initial
    $changeStr = if ($change -ge 0) { "+$change" } else { "$change" }
    Write-Host "    $queue : $initial -> $final ($changeStr)" -ForegroundColor DarkGray
}

Write-Host ""

# Calculate throughput
$ElapsedMinutes = $WaitSeconds / 60.0
$Throughput = if ($ElapsedMinutes -gt 0) { [math]::Round($DocsIndexed / $ElapsedMinutes, 1) } else { 0 }

$BenchmarkResults.Summary.DocumentsIndexed = $DocsIndexed
$BenchmarkResults.Summary.ThroughputPerMinute = $Throughput
$BenchmarkResults.Summary.ElapsedSeconds = $WaitSeconds

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   BENCHMARK SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Files Submitted: $($BenchmarkResults.Summary.TotalFilesSubmitted)" -ForegroundColor White
Write-Host "  Successful:      $($BenchmarkResults.Summary.TotalSuccessful)" -ForegroundColor Green
Write-Host "  Failed:          $($BenchmarkResults.Summary.TotalFailed)" -ForegroundColor $(if ($BenchmarkResults.Summary.TotalFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "  Avg Submission Latency: $($BenchmarkResults.Summary.AverageLatencyMs) ms" -ForegroundColor Yellow
Write-Host "  Documents Indexed:      $DocsIndexed (in ${WaitSeconds}s)" -ForegroundColor Yellow
Write-Host "  Throughput:             $Throughput docs/min" -ForegroundColor Yellow
Write-Host ""

# Per-category summary
Write-Host "  Per-Category Performance:" -ForegroundColor White
foreach ($category in $BenchmarkResults.Categories.Keys) {
    $cat = $BenchmarkResults.Categories[$category]
    Write-Host "    $category : avg $($cat.AverageLatencyMs)ms, $($cat.SuccessfulSubmissions) files" -ForegroundColor DarkGray
}

Write-Host ""

# -----------------------------------------------------------------------------
# SAVE REPORT
# -----------------------------------------------------------------------------

if ($OutputReport) {
    $reportPath = if ([System.IO.Path]::IsPathRooted($OutputReport)) {
        $OutputReport
    } else {
        Join-Path $PSScriptRoot $OutputReport
    }
    
    $BenchmarkResults | ConvertTo-Json -Depth 10 | Set-Content -Path $reportPath -Encoding UTF8
    Write-Host "  Report saved to: $reportPath" -ForegroundColor Green
    Write-Host ""
}

# Return results for automation
return $BenchmarkResults

