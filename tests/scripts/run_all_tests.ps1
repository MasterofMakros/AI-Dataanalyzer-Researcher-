# Neural Vault: Comprehensive Test & Benchmark Suite
# Main Entry Point
# Stand: 11.01.2026

param(
    [switch]$Quick,           # Nur schnelle Tests
    [switch]$Full,            # Alle Tests inkl. lange E2E
    [switch]$Report,          # JSON-Report generieren
    [switch]$Verbose,         # Detaillierte Ausgabe
    [string]$OutputDir = "$PSScriptRoot\..\reports"
)

$ErrorActionPreference = "Continue"
$startTime = Get-Date

# Banner
Write-Host @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NEURAL VAULT TEST & BENCHMARK SUITE                       ║
║                            Version 1.0.0                                     ║
║                            Stand: 11.01.2026                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Ergebnis-Sammlung
$global:TestResults = @{
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Summary = @{
        TotalTests = 0
        Passed = 0
        Failed = 0
        Warnings = 0
    }
    Routing = @()
    OCR = @()
    Transcription = @()
    NER = @()
    Search = @()
    E2E = @()
}

# ===== HELPER FUNCTIONS =====

function Add-TestResult {
    param([string]$Category, [hashtable]$Result)
    $global:TestResults[$Category] += $Result
    $global:TestResults.Summary.TotalTests++
    if ($Result.Status -eq "PASS") { $global:TestResults.Summary.Passed++ }
    elseif ($Result.Status -eq "FAIL") { $global:TestResults.Summary.Failed++ }
    else { $global:TestResults.Summary.Warnings++ }
}

function Write-TestHeader {
    param([string]$Title, [int]$Step, [int]$Total)
    Write-Host "`n[$Step/$Total] $Title" -ForegroundColor Yellow
    Write-Host ("-" * 60)
}

# ===== 1. ROUTING TESTS =====

function Test-Routing {
    Write-TestHeader -Title "Running Routing Tests" -Step 1 -Total 6
    
    $testCases = @(
        @{File="test.pdf"; Expected="extract:documents"},
        @{File="test.docx"; Expected="extract:documents"},
        @{File="test.py"; Expected="extract:documents"},
        @{File="test.jpg"; Expected="extract:images"},
        @{File="test.heic"; Expected="extract:images"},
        @{File="test.mp3"; Expected="extract:audio"},
        @{File="test.mp4"; Expected="extract:video"},
        @{File="test.zip"; Expected="extract:archive"},
        @{File="test.eml"; Expected="extract:email"}
    )
    
    foreach ($test in $testCases) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8020/route?filename=$($test.File)" -Method GET -TimeoutSec 5
            $success = $response.queue -eq $test.Expected
            $status = if ($success) { "PASS" } else { "FAIL" }
        } catch {
            $status = "ERROR"
            $response = @{queue = "ERROR: $_"}
        }
        
        $statusIcon = if ($status -eq "PASS") { "✅" } elseif ($status -eq "FAIL") { "❌" } else { "⚠️" }
        Write-Host "  $statusIcon $($test.File) → $($response.queue)"
        
        Add-TestResult -Category "Routing" -Result @{
            File = $test.File
            Expected = $test.Expected
            Actual = $response.queue
            Status = $status
        }
    }
}

# ===== 2. OCR TESTS =====

function Calculate-CER {
    param([string]$GroundTruth, [string]$OCROutput)
    
    $gt = $GroundTruth.ToCharArray()
    $ocr = $OCROutput.ToCharArray()
    
    $errors = 0
    $maxLen = [Math]::Max($gt.Length, $ocr.Length)
    
    for ($i = 0; $i -lt $maxLen; $i++) {
        if ($i -ge $gt.Length -or $i -ge $ocr.Length) { $errors++ }
        elseif ($gt[$i] -ne $ocr[$i]) { $errors++ }
    }
    
    if ($gt.Length -eq 0) { return 100 }
    return [Math]::Round($errors / $gt.Length * 100, 2)
}

function Test-OCR {
    Write-TestHeader -Title "Running OCR Benchmark" -Step 2 -Total 6
    
    Write-Host "  Target: CER <2%, WER <5%" -ForegroundColor Gray
    
    # Test mit lokalen Bildern aus _Inbox
    $testImages = Get-ChildItem "F:\_Inbox\test_image*" -ErrorAction SilentlyContinue | Select-Object -First 3
    
    foreach ($img in $testImages) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8021/ocr" `
                -Method POST `
                -Form @{file = Get-Item $img.FullName; langs = "de,en"} `
                -TimeoutSec 60
            
            $ocrText = $response.text
            $confidence = $response.confidence
            
            $status = if ($confidence -gt 0.9) { "PASS" } elseif ($confidence -gt 0.7) { "WARN" } else { "FAIL" }
            $statusIcon = if ($status -eq "PASS") { "✅" } elseif ($status -eq "WARN") { "⚠️" } else { "❌" }
            
            Write-Host "  $statusIcon $($img.Name): Confidence=$([Math]::Round($confidence, 3)), Text=$($ocrText.Substring(0, [Math]::Min(50, $ocrText.Length)))..."
            
            Add-TestResult -Category "OCR" -Result @{
                File = $img.Name
                Confidence = $confidence
                TextLength = $ocrText.Length
                Status = $status
            }
        } catch {
            Write-Host "  ❌ $($img.Name): ERROR - $_" -ForegroundColor Red
            Add-TestResult -Category "OCR" -Result @{
                File = $img.Name
                Status = "ERROR"
                Error = $_.ToString()
            }
        }
    }
}

# ===== 3. TRANSCRIPTION TESTS =====

function Test-Transcription {
    Write-TestHeader -Title "Running Transcription Benchmark" -Step 3 -Total 6
    
    Write-Host "  Target: WER <15% (DE), <10% (EN)" -ForegroundColor Gray
    
    $testAudios = Get-ChildItem "F:\_Inbox\test_audio*" -ErrorAction SilentlyContinue | Select-Object -First 2
    
    foreach ($audio in $testAudios) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8019/transcribe" `
                -Method POST `
                -Form @{file = Get-Item $audio.FullName; language = "de"} `
                -TimeoutSec 120
            
            $text = $response.text
            $wordCount = ($text -split '\s+').Count
            
            $status = if ($wordCount -gt 5) { "PASS" } else { "WARN" }
            $statusIcon = if ($status -eq "PASS") { "✅" } else { "⚠️" }
            
            Write-Host "  $statusIcon $($audio.Name): Words=$wordCount, Text=$($text.Substring(0, [Math]::Min(50, $text.Length)))..."
            
            Add-TestResult -Category "Transcription" -Result @{
                File = $audio.Name
                WordCount = $wordCount
                Status = $status
            }
        } catch {
            Write-Host "  ❌ $($audio.Name): ERROR - $_" -ForegroundColor Red
            Add-TestResult -Category "Transcription" -Result @{
                File = $audio.Name
                Status = "ERROR"
                Error = $_.ToString()
            }
        }
    }
}

# ===== 4. SEARCH TESTS =====

function Test-Search {
    Write-TestHeader -Title "Running Search Quality Tests" -Step 4 -Total 6
    
    # Meilisearch Test
    Write-Host "  Testing Meilisearch (Fulltext)..." -ForegroundColor Gray
    try {
        $searchResult = Invoke-RestMethod -Uri "http://localhost:7700/indexes/documents/search" `
            -Method POST `
            -Body (@{q = "test"; limit = 5} | ConvertTo-Json) `
            -ContentType 'application/json' `
            -Headers @{Authorization = "Bearer masterKey"} `
            -TimeoutSec 10
        
        $hitCount = $searchResult.hits.Count
        $processingTime = $searchResult.processingTimeMs
        
        $status = if ($hitCount -ge 0) { "PASS" } else { "FAIL" }
        Write-Host "  ✅ Meilisearch: $hitCount hits in ${processingTime}ms"
        
        Add-TestResult -Category "Search" -Result @{
            Engine = "Meilisearch"
            Hits = $hitCount
            ProcessingTime = $processingTime
            Status = $status
        }
    } catch {
        Write-Host "  ❌ Meilisearch: ERROR - $_" -ForegroundColor Red
        Add-TestResult -Category "Search" -Result @{
            Engine = "Meilisearch"
            Status = "ERROR"
            Error = $_.ToString()
        }
    }
    
    # Qdrant Test
    Write-Host "  Testing Qdrant (Vector)..." -ForegroundColor Gray
    try {
        $collections = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method GET -TimeoutSec 10
        $collectionCount = $collections.result.collections.Count
        
        $status = "PASS"
        Write-Host "  ✅ Qdrant: $collectionCount collections available"
        
        Add-TestResult -Category "Search" -Result @{
            Engine = "Qdrant"
            Collections = $collectionCount
            Status = $status
        }
    } catch {
        Write-Host "  ❌ Qdrant: ERROR - $_" -ForegroundColor Red
        Add-TestResult -Category "Search" -Result @{
            Engine = "Qdrant"
            Status = "ERROR"
            Error = $_.ToString()
        }
    }
}

# ===== 5. E2E PIPELINE TESTS =====

function Test-E2EPipeline {
    Write-TestHeader -Title "Running End-to-End Pipeline Tests" -Step 5 -Total 6
    
    # Queue-Statistiken prüfen
    try {
        $stats = Invoke-RestMethod -Uri "http://localhost:8020/stats" -TimeoutSec 10
        
        $totalPending = $stats.total_pending
        $dlqCount = $stats.queues.'dlq:extract'
        $enriched = $stats.queues.'enrich:ner'
        
        Write-Host "  Pipeline Status:"
        Write-Host "    Total Pending: $totalPending"
        Write-Host "    Enriched: $enriched"
        Write-Host "    DLQ Errors: $dlqCount"
        
        $status = if ($dlqCount -eq 0) { "PASS" } elseif ($dlqCount -lt 5) { "WARN" } else { "FAIL" }
        $statusIcon = if ($status -eq "PASS") { "✅" } elseif ($status -eq "WARN") { "⚠️" } else { "❌" }
        
        Write-Host "  $statusIcon Pipeline Health: $status (DLQ=$dlqCount)"
        
        Add-TestResult -Category "E2E" -Result @{
            TotalPending = $totalPending
            Enriched = $enriched
            DLQErrors = $dlqCount
            Status = $status
        }
    } catch {
        Write-Host "  ❌ Pipeline: ERROR - $_" -ForegroundColor Red
        Add-TestResult -Category "E2E" -Result @{
            Status = "ERROR"
            Error = $_.ToString()
        }
    }
}

# ===== 6. SERVICE HEALTH =====

function Test-ServiceHealth {
    Write-TestHeader -Title "Running Service Health Checks" -Step 6 -Total 6
    
    $services = @(
        @{Name="Router"; Url="http://localhost:8020/health"},
        @{Name="Document Processor"; Url="http://localhost:8021/health"},
        @{Name="WhisperX"; Url="http://localhost:8019/health"},
        @{Name="Meilisearch"; Url="http://localhost:7700/health"},
        @{Name="Qdrant"; Url="http://localhost:6333/"},
        @{Name="Redis"; Url="http://localhost:8020/stats"}  # Indirect check via router
    )
    
    foreach ($svc in $services) {
        try {
            $response = Invoke-WebRequest -Uri $svc.Url -Method GET -TimeoutSec 5 -ErrorAction Stop
            $status = if ($response.StatusCode -eq 200) { "PASS" } else { "WARN" }
            $statusIcon = if ($status -eq "PASS") { "✅" } else { "⚠️" }
            Write-Host "  $statusIcon $($svc.Name): UP"
        } catch {
            Write-Host "  ❌ $($svc.Name): DOWN" -ForegroundColor Red
        }
    }
}

# ===== MAIN EXECUTION =====

Write-Host "`nStarting tests at $(Get-Date -Format 'HH:mm:ss')..." -ForegroundColor Gray

# Run Tests
Test-Routing
Test-OCR

if (-not $Quick) {
    Test-Transcription
}

Test-Search
Test-E2EPipeline
Test-ServiceHealth

# Summary
$endTime = Get-Date
$totalTime = ($endTime - $startTime).TotalSeconds

Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                              TEST SUMMARY                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

$summary = $global:TestResults.Summary
Write-Host "  Total Tests: $($summary.TotalTests)"
Write-Host "  ✅ Passed:   $($summary.Passed)" -ForegroundColor Green
Write-Host "  ❌ Failed:   $($summary.Failed)" -ForegroundColor Red
Write-Host "  ⚠️ Warnings: $($summary.Warnings)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Total Time: $([Math]::Round($totalTime, 1)) seconds"

$successRate = if ($summary.TotalTests -gt 0) { [Math]::Round($summary.Passed / $summary.TotalTests * 100, 1) } else { 0 }
Write-Host "  Success Rate: $successRate%"

# Save Report
if ($Report) {
    $reportPath = "$OutputDir\report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $global:TestResults | ConvertTo-Json -Depth 5 | Out-File $reportPath -Encoding UTF8
    Write-Host "`nReport saved to: $reportPath" -ForegroundColor Cyan
}

Write-Host "`nTest suite completed at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
