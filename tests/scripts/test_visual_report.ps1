<#
.SYNOPSIS
    Neural Vault - Visual Test Report Generator
    Creates interactive HTML report with architecture visualization

.DESCRIPTION
    Generates HTML report with:
    - Interactive Mermaid architecture diagram
    - Highlighted components per test
    - Real-time test results
    - Opens in browser for visual feedback

.EXAMPLE
    .\test_visual_report.ps1
#>

param(
    [string]$OutputDir = "",
    [string]$RouterUrl = "http://127.0.0.1:8030",
    [string]$ApiUrl = "http://127.0.0.1:8010",
    [switch]$OpenBrowser
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
# TEST SUITE CONFIGURATION
# =============================================================================

$TestSuites = [ordered]@{
    "Routing" = @{
        Script = "test_all_formats.ps1"
        Description = "Format routing validation"
        Component = "Universal Router"
        HighlightNodes = @("A", "B", "C")
        Color = "#4CAF50"
    }
    "Extraction" = @{
        Script = "test_extraction_quality.ps1"
        Description = "Content extraction quality"
        Component = "Tika/Docling Workers"
        HighlightNodes = @("D", "J")
        Color = "#2196F3"
    }
    "Transcription" = @{
        Script = "test_transcription.ps1"
        Description = "Audio/Video transcription"
        Component = "WhisperX"
        HighlightNodes = @("F", "G", "L", "M")
        Color = "#FF9800"
    }
    "OCR" = @{
        Script = "test_ocr_accuracy.ps1"
        Description = "Image OCR accuracy"
        Component = "Surya OCR"
        HighlightNodes = @("E", "K")
        Color = "#9C27B0"
    }
    "Archive" = @{
        Script = "test_archive_extraction.ps1"
        Description = "Archive unpacking"
        Component = "7zip Worker"
        HighlightNodes = @("H", "N")
        Color = "#795548"
    }
    "ErrorHandling" = @{
        Script = "test_error_handling.ps1"
        Description = "Error resilience"
        Component = "DLQ System"
        HighlightNodes = @("C")
        Color = "#F44336"
    }
}

# =============================================================================
# HTML TEMPLATE
# =============================================================================

function Get-HtmlTemplate {
    param([array]$Results)
    
    $testRows = ""
    $diagramStyles = ""
    
    foreach ($result in $Results) {
        $statusClass = switch ($result.Status) {
            "PASS" { "pass" }
            "FAIL" { "fail" }
            "SKIP" { "skip" }
            default { "pending" }
        }
        
        $testRows += @"
        <tr class="$statusClass" onclick="highlightComponent('$($result.Name)')">
            <td>$($result.Name)</td>
            <td><span class="status-badge $statusClass">$($result.Status)</span></td>
            <td>$($result.Component)</td>
            <td>$($result.Passed)</td>
            <td>$($result.Failed)</td>
            <td>$($result.Skipped)</td>
            <td>$([math]::Round($result.DurationMs / 1000, 1))s</td>
        </tr>
"@
    }

    return @"
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Vault - Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            color: #00d4ff;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        .card h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 10px;
        }
        .mermaid {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 20px;
            min-height: 400px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        th {
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
        }
        tr:hover {
            background: rgba(0, 212, 255, 0.1);
            cursor: pointer;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .pass { background: rgba(76, 175, 80, 0.3); color: #4CAF50; }
        .fail { background: rgba(244, 67, 54, 0.3); color: #F44336; }
        .skip { background: rgba(158, 158, 158, 0.3); color: #9E9E9E; }
        .pending { background: rgba(255, 193, 7, 0.3); color: #FFC107; }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .summary-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .summary-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .summary-card .label { color: #888; margin-top: 5px; }
        .summary-card.pass .value { color: #4CAF50; }
        .summary-card.fail .value { color: #F44336; }
        .summary-card.skip .value { color: #9E9E9E; }
        .summary-card.total .value { color: #00d4ff; }
        .legend {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        .active-test {
            background: rgba(0, 212, 255, 0.2) !important;
            border-left: 4px solid #00d4ff;
        }
        .timestamp {
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Neural Vault Test Report</h1>
        <p class="subtitle">Pipeline Verification Results</p>
        
        <div class="summary-grid">
            <div class="summary-card total">
                <div class="value">$($Results.Count)</div>
                <div class="label">Test Suites</div>
            </div>
            <div class="summary-card pass">
                <div class="value">$(($Results | Where-Object { `$_.Status -eq 'PASS' }).Count)</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card fail">
                <div class="value">$(($Results | Where-Object { `$_.Status -eq 'FAIL' }).Count)</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card skip">
                <div class="value">$(($Results | Where-Object { `$_.Status -eq 'SKIP' }).Count)</div>
                <div class="label">Skipped</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Architecture Diagram</h2>
                <div class="mermaid" id="architecture">
graph TB
    subgraph INTAKE["INTAKE"]
        A[File Upload] --> B[Universal Router]
        B --> C{Format Detection}
    end

    subgraph QUEUES["QUEUES"]
        C --> D[extract:documents]
        C --> E[extract:images]
        C --> F[extract:audio]
        C --> G[extract:video]
        C --> H[extract:archive]
        C --> I[extract:email]
    end

    subgraph WORKERS["WORKERS"]
        D --> J[Tika/Docling]
        E --> K[Surya OCR]
        F --> L[WhisperX]
        G --> M[FFmpeg + WhisperX]
        H --> N[7zip]
        I --> O[Email Parser]
    end

    subgraph ENRICHMENT["ENRICHMENT"]
        J --> P[enrich:ner]
        K --> P
        L --> P
        M --> P
        N --> P
        O --> P
        P --> Q[GLiNER NER]
    end

    subgraph INDEX["INDEX"]
        Q --> R[Meilisearch]
        R --> S[Qdrant Vectors]
    end

    subgraph SEARCH["SEARCH"]
        T[Search Query] --> R
        R --> U[Results]
    end

    style A fill:#4CAF50
    style R fill:#2196F3
    style U fill:#9C27B0
                </div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-color" style="background:#4CAF50"></div>Routing</div>
                    <div class="legend-item"><div class="legend-color" style="background:#2196F3"></div>Extraction</div>
                    <div class="legend-item"><div class="legend-color" style="background:#FF9800"></div>Transcription</div>
                    <div class="legend-item"><div class="legend-color" style="background:#9C27B0"></div>OCR</div>
                    <div class="legend-item"><div class="legend-color" style="background:#795548"></div>Archive</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Test Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Suite</th>
                            <th>Status</th>
                            <th>Component</th>
                            <th>Pass</th>
                            <th>Fail</th>
                            <th>Skip</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        $testRows
                    </tbody>
                </table>
            </div>
        </div>
        
        <p class="timestamp">Generated: $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')</p>
    </div>
    
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
</body>
</html>
"@
}

# =============================================================================
# TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT - VISUAL TEST REPORT GENERATOR" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$AllResults = @()
$currentTest = 0
$totalTests = $TestSuites.Count

foreach ($suiteName in $TestSuites.Keys) {
    $currentTest++
    $config = $TestSuites[$suiteName]
    
    Write-Host "  [$currentTest/$totalTests] Testing: $suiteName" -NoNewline
    Write-Host " ($($config.Component))" -ForegroundColor DarkGray
    
    # Show which part of architecture is being tested
    Write-Host "           Highlight: " -NoNewline -ForegroundColor DarkGray
    Write-Host "$($config.HighlightNodes -join ' -> ')" -ForegroundColor $config.Color.Replace('#', '')
    
    $scriptPath = Join-Path $ScriptDir $config.Script
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    $passed = 0
    $failed = 0
    $skipped = 0
    $status = "SKIP"
    
    if (Test-Path $scriptPath) {
        try {
            $output = & $scriptPath 2>&1
            $outputStr = $output -join "`n"
            
            if ($outputStr -match "Passed:\s*(\d+)") { $passed = [int]$Matches[1] }
            if ($outputStr -match "Failed:\s*(\d+)") { $failed = [int]$Matches[1] }
            if ($outputStr -match "Skipped:\s*(\d+)") { $skipped = [int]$Matches[1] }
            
            if ($failed -gt 0) { $status = "FAIL" }
            elseif ($passed -gt 0) { $status = "PASS" }
        }
        catch {
            $status = "ERROR"
            $failed = 1
        }
    }
    
    $stopwatch.Stop()
    
    $statusColor = switch ($status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "DarkGray" }
        default { "Yellow" }
    }
    
    Write-Host "           Result: " -NoNewline
    Write-Host "[$status]" -ForegroundColor $statusColor
    Write-Host ""
    
    $AllResults += @{
        Name = $suiteName
        Status = $status
        Component = $config.Component
        Passed = $passed
        Failed = $failed
        Skipped = $skipped
        DurationMs = $stopwatch.ElapsedMilliseconds
        HighlightNodes = $config.HighlightNodes
        Color = $config.Color
    }
}

# Generate HTML report
$htmlContent = Get-HtmlTemplate -Results $AllResults
$reportPath = Join-Path $OutputDir "test_report.html"
$htmlContent | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   REPORT GENERATED" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  HTML Report: $reportPath" -ForegroundColor Green
Write-Host ""

# Open in browser
if ($OpenBrowser -or $true) {
    Write-Host "  Opening in browser..." -ForegroundColor DarkGray
    Start-Process $reportPath
}

return $AllResults
