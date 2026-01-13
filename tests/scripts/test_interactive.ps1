<#
.SYNOPSIS
    Neural Vault - Enhanced Interactive Test Suite
    Full-featured test runner with progress bars, ETA, and AI-agent compatibility

.DESCRIPTION
    Features:
    - Real-time progress bars with percentage completion
    - ETA time estimates for each test phase
    - Mermaid architecture diagram generation
    - AI-coding-agent compatible structured JSON output
    - End-user friendly console interface

.PARAMETER OutputDir
    Directory for reports and artifacts

.EXAMPLE
    .\test_interactive.ps1
#>

param(
    [string]$OutputDir = "",
    [string]$RouterUrl = "http://127.0.0.1:8030",
    [string]$ApiUrl = "http://127.0.0.1:8010"
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
# MERMAID ARCHITECTURE DIAGRAM
# =============================================================================

$MermaidDiagram = @'
graph TB
    subgraph INTAKE
        A[File Upload] --> B[Universal Router]
        B --> C{Format Detection}
    end

    subgraph QUEUES
        C --> D[extract:documents]
        C --> E[extract:images]
        C --> F[extract:audio]
        C --> G[extract:video]
        C --> H[extract:archive]
        C --> I[extract:email]
    end

    subgraph WORKERS
        D --> J[Tika/Docling]
        E --> K[Surya OCR]
        F --> L[WhisperX]
        G --> M[FFmpeg + WhisperX]
        H --> N[7zip]
        I --> O[Email Parser]
    end

    subgraph ENRICHMENT
        J --> P[enrich:ner]
        K --> P
        L --> P
        M --> P
        N --> P
        O --> P
        P --> Q[GLiNER NER]
    end

    subgraph INDEX
        Q --> R[Qdrant]
        R --> S[Qdrant Vectors]
    end

    subgraph SEARCH
        T[Search Query] --> R
        R --> U[Results]
    end

    style A fill:#4CAF50
    style R fill:#2196F3
    style U fill:#9C27B0
'@

# =============================================================================
# TEST SUITE CONFIGURATION
# =============================================================================

$TestSuites = [ordered]@{
    "Routing" = @{
        Script = "test_all_formats.ps1"
        Description = "Format routing validation"
        Component = "Universal Router"
        ExpectedDuration = 5
    }
    "Extraction" = @{
        Script = "test_extraction_quality.ps1"
        Description = "Content extraction quality"
        Component = "Tika/Docling Workers"
        ExpectedDuration = 10
    }
    "Transcription" = @{
        Script = "test_transcription.ps1"
        Description = "Audio/Video transcription"
        Component = "WhisperX"
        ExpectedDuration = 15
    }
    "OCR" = @{
        Script = "test_ocr_accuracy.ps1"
        Description = "Image OCR accuracy"
        Component = "Surya OCR"
        ExpectedDuration = 10
    }
    "Archive" = @{
        Script = "test_archive_extraction.ps1"
        Description = "Archive unpacking"
        Component = "7zip Worker"
        ExpectedDuration = 8
    }
    "ErrorHandling" = @{
        Script = "test_error_handling.ps1"
        Description = "Error resilience"
        Component = "DLQ System"
        ExpectedDuration = 12
    }
}

# =============================================================================
# PROGRESS BAR FUNCTIONS
# =============================================================================

function Show-ProgressBar {
    param(
        [string]$Status,
        [int]$PercentComplete,
        [int]$SecondsRemaining = -1
    )
    
    $barWidth = 40
    $filled = [math]::Floor($barWidth * $PercentComplete / 100)
    $empty = $barWidth - $filled
    
    $filledStr = "#" * $filled
    $emptyStr = "-" * $empty
    $bar = "[$filledStr$emptyStr]"
    
    $etaStr = ""
    if ($SecondsRemaining -gt 0) {
        $mins = [math]::Floor($SecondsRemaining / 60)
        $secs = $SecondsRemaining % 60
        $etaStr = " ETA: ${mins}m ${secs}s"
    }
    
    Write-Host "`r  $bar ${PercentComplete}%$etaStr - $Status                    " -NoNewline
}

function Show-TestHeader {
    param(
        [string]$TestName,
        [string]$Component,
        [int]$Index,
        [int]$Total
    )
    
    Write-Host ""
    Write-Host "+-------------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "| TEST ${Index}/${Total}: $TestName" -ForegroundColor Cyan
    Write-Host "| Component: $Component" -ForegroundColor Cyan
    Write-Host "+-------------------------------------------------------------+" -ForegroundColor Cyan
}

function Show-TestResult {
    param(
        [string]$Status,
        [int]$Passed,
        [int]$Failed,
        [int]$Skipped,
        [int]$DurationMs
    )
    
    $statusColor = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "DarkGray" }
        "ERROR" { "Magenta" }
        default { "White" }
    }
    
    $durationSec = [math]::Round($DurationMs / 1000, 1)
    
    Write-Host ""
    Write-Host "  Result: " -NoNewline
    Write-Host "[$Status]" -ForegroundColor $statusColor -NoNewline
    Write-Host " | Passed: $Passed | Failed: $Failed | Skipped: $Skipped | Duration: ${durationSec}s"
}

# =============================================================================
# AI-AGENT COMPATIBLE OUTPUT
# =============================================================================

function Get-QueueStatus {
    $queues = @{
        "extract_documents" = 0
        "extract_images" = 0
        "extract_audio" = 0
        "extract_video" = 0
        "extract_archive" = 0
        "extract_email" = 0
        "enrich_ner" = 0
    }
    
    $queueNames = @("extract:documents", "extract:images", "extract:audio", "extract:video", "extract:archive", "extract:email", "enrich:ner")
    $idx = 0
    foreach ($queue in $queueNames) {
        try {
            $result = docker exec conductor-redis redis-cli -a change_me_in_prod XLEN $queue 2>$null
            if ($result -match "^\d+$") {
                $key = $queues.Keys | Select-Object -Index $idx
                $queues[$key] = [int]$result
            }
        } catch {}
        $idx++
    }
    
    $total = 0
    foreach ($v in $queues.Values) { $total += $v }
    
    return @{
        queues = $queues
        total_pending = $total
    }
}

function Generate-AgentOutput {
    param(
        [hashtable]$Results,
        [string]$OutputPath
    )
    
    $agentOutput = @{
        schema_version = "1.0"
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        execution_summary = @{
            total_suites = $Results.Suites.Count
            passed = 0
            failed = 0
            skipped = 0
            overall_status = $Results.OverallStatus
        }
        architecture = @{
            mermaid_diagram = $MermaidDiagram
            components_tested = @()
        }
        test_results = @()
        ai_debugging_hints = @()
        recommended_actions = @()
    }
    
    foreach ($suite in $Results.Suites) {
        if ($suite.Status -eq "PASS") { $agentOutput.execution_summary.passed++ }
        elseif ($suite.Status -eq "FAIL" -or $suite.Status -eq "ERROR") { $agentOutput.execution_summary.failed++ }
        else { $agentOutput.execution_summary.skipped++ }
        
        $testResult = @{
            name = $suite.Name
            status = $suite.Status
            component = $suite.Component
            passed = $suite.Passed
            failed = $suite.Failed
            skipped = $suite.Skipped
            duration_ms = $suite.DurationMs
        }
        
        $agentOutput.test_results += $testResult
        $agentOutput.architecture.components_tested += $suite.Component
        
        if ($suite.Status -eq "FAIL" -or $suite.Status -eq "ERROR") {
            $hint = @{
                component = $suite.Component
                test_name = $suite.Name
                suggestion = "Check $($suite.Component) for errors"
            }
            $agentOutput.ai_debugging_hints += $hint
            $agentOutput.recommended_actions += "Fix $($suite.Name) test failures"
        }
    }
    
    $queueStatus = Get-QueueStatus
    $agentOutput.queue_status = $queueStatus
    
    if ($queueStatus.total_pending -gt 0) {
        $agentOutput.ai_debugging_hints += @{
            component = "Queue Processing"
            suggestion = "Run drain_and_index.py to process $($queueStatus.total_pending) pending items"
        }
    }
    
    $agentOutput | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8
    return $agentOutput
}

# =============================================================================
# TEST EXECUTION ENGINE
# =============================================================================

function Run-SingleTest {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    $scriptPath = Join-Path $ScriptDir $Config.Script
    
    if (-not (Test-Path $scriptPath)) {
        return @{
            Name = $Name
            Status = "SKIP"
            Component = $Config.Component
            Passed = 0
            Failed = 0
            Skipped = 1
            DurationMs = 0
        }
    }
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    Show-ProgressBar -Status "Initializing..." -PercentComplete 0
    
    try {
        Show-ProgressBar -Status "Running tests..." -PercentComplete 30
        
        $output = & $scriptPath 2>&1
        
        Show-ProgressBar -Status "Analyzing results..." -PercentComplete 80
        
        $stopwatch.Stop()
        
        $passed = 0
        $failed = 0
        $skipped = 0
        
        $outputStr = $output -join "`n"
        
        if ($outputStr -match "Passed:\s*(\d+)") { $passed = [int]$Matches[1] }
        if ($outputStr -match "Failed:\s*(\d+)") { $failed = [int]$Matches[1] }
        if ($outputStr -match "Skipped:\s*(\d+)") { $skipped = [int]$Matches[1] }
        
        $status = "SKIP"
        if ($failed -gt 0) { $status = "FAIL" }
        elseif ($passed -gt 0) { $status = "PASS" }
        
        Show-ProgressBar -Status "Complete" -PercentComplete 100
        
        return @{
            Name = $Name
            Status = $status
            Component = $Config.Component
            Passed = $passed
            Failed = $failed
            Skipped = $skipped
            DurationMs = $stopwatch.ElapsedMilliseconds
        }
    }
    catch {
        $stopwatch.Stop()
        return @{
            Name = $Name
            Status = "ERROR"
            Component = $Config.Component
            Passed = 0
            Failed = 1
            Skipped = 0
            DurationMs = $stopwatch.ElapsedMilliseconds
        }
    }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Clear-Host

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                                                                " -ForegroundColor Cyan
Write-Host "       NEURAL VAULT - INTERACTIVE TEST SUITE                   " -ForegroundColor Cyan
Write-Host "                                                                " -ForegroundColor Cyan
Write-Host "       Version 2.0.0 | $(Get-Date -Format 'dd.MM.yyyy HH:mm')                       " -ForegroundColor Cyan
Write-Host "                                                                " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$totalExpectedDuration = 0
foreach ($config in $TestSuites.Values) {
    $totalExpectedDuration += $config.ExpectedDuration
}

Write-Host "  Configuration:" -ForegroundColor White
Write-Host "     * Test Suites: $($TestSuites.Count)" -ForegroundColor DarkGray
Write-Host "     * Est. Duration: ~${totalExpectedDuration}s" -ForegroundColor DarkGray
Write-Host ""

$mermaidPath = Join-Path $OutputDir "architecture.mmd"
$MermaidDiagram | Out-File -FilePath $mermaidPath -Encoding UTF8
Write-Host "  Architecture diagram saved: architecture.mmd" -ForegroundColor DarkGray
Write-Host ""

$AllResults = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Suites = @()
    OverallStatus = "UNKNOWN"
}

$overallStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$currentTest = 0
$totalTests = $TestSuites.Count

foreach ($suiteName in $TestSuites.Keys) {
    $currentTest++
    $config = $TestSuites[$suiteName]
    
    $etaSeconds = [math]::Max(0, ($totalTests - $currentTest + 1) * 10)
    
    Show-TestHeader -TestName $suiteName -Component $config.Component -Index $currentTest -Total $totalTests
    
    $result = Run-SingleTest -Name $suiteName -Config $config
    $AllResults.Suites += $result
    
    Show-TestResult -Status $result.Status -Passed $result.Passed -Failed $result.Failed -Skipped $result.Skipped -DurationMs $result.DurationMs
}

$overallStopwatch.Stop()

$failedCount = 0
foreach ($suite in $AllResults.Suites) {
    if ($suite.Status -eq "FAIL" -or $suite.Status -eq "ERROR") {
        $failedCount++
    }
}
$AllResults.OverallStatus = if ($failedCount -eq 0) { "PASS" } else { "FAIL" }

# =============================================================================
# SUMMARY
# =============================================================================

Write-Host ""
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                      TEST SUMMARY                              " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "  +---------------+--------+--------+--------+---------+----------+" -ForegroundColor DarkGray
Write-Host "  | Suite         | Status | Passed | Failed | Skipped | Duration |" -ForegroundColor DarkGray
Write-Host "  +---------------+--------+--------+--------+---------+----------+" -ForegroundColor DarkGray

foreach ($suite in $AllResults.Suites) {
    $statusColor = switch ($suite.Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "DarkGray" }
        default { "White" }
    }
    
    $name = $suite.Name.PadRight(13).Substring(0, 13)
    $status = $suite.Status.PadRight(6)
    $dur = "$([math]::Round($suite.DurationMs / 1000, 1))s".PadLeft(8)
    
    Write-Host "  | $name | " -NoNewline -ForegroundColor DarkGray
    Write-Host "$status" -NoNewline -ForegroundColor $statusColor
    Write-Host " | $($suite.Passed.ToString().PadLeft(6)) | $($suite.Failed.ToString().PadLeft(6)) | $($suite.Skipped.ToString().PadLeft(7)) | $dur |" -ForegroundColor DarkGray
}

Write-Host "  +---------------+--------+--------+--------+---------+----------+" -ForegroundColor DarkGray
Write-Host ""

$totalPassed = 0
$totalFailed = 0
$totalSkipped = 0
foreach ($suite in $AllResults.Suites) {
    $totalPassed += $suite.Passed
    $totalFailed += $suite.Failed
    $totalSkipped += $suite.Skipped
}
$totalDuration = [math]::Round($overallStopwatch.Elapsed.TotalSeconds, 1)

Write-Host "  Totals: Passed: $totalPassed | Failed: $totalFailed | Skipped: $totalSkipped" -ForegroundColor White
Write-Host "  Duration: ${totalDuration}s" -ForegroundColor White
Write-Host ""

$overallColor = if ($AllResults.OverallStatus -eq "PASS") { "Green" } else { "Red" }
Write-Host "  Overall Result: [$($AllResults.OverallStatus)]" -ForegroundColor $overallColor
Write-Host ""

$agentOutputPath = Join-Path $OutputDir "ai_agent_report.json"
$agentOutput = Generate-AgentOutput -Results $AllResults -OutputPath $agentOutputPath

Write-Host "  Reports Generated:" -ForegroundColor White
Write-Host "     * Architecture: $mermaidPath" -ForegroundColor DarkGray
Write-Host "     * AI Agent Report: $agentOutputPath" -ForegroundColor DarkGray
Write-Host ""

$queueStatus = Get-QueueStatus
if ($queueStatus.total_pending -gt 0) {
    Write-Host "  Queue Status: $($queueStatus.total_pending) items pending processing" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

$exitCode = if ($AllResults.OverallStatus -eq "PASS") { 0 } else { 1 }
exit $exitCode
