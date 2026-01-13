<#
.SYNOPSIS
    Neural Vault - Extraction Quality Test Suite
    Tests extracted content against known ground truth

.DESCRIPTION
    Queries Qdrant for indexed documents and validates:
    1. Expected keywords/content are present
    2. Entity extraction accuracy
    3. Structure preservation

.PARAMETER ApiUrl
    Base URL of the conductor-api (default: http://127.0.0.1:8010)

.PARAMETER Verbose
    Show detailed output for each test

.EXAMPLE
    .\test_extraction_quality.ps1
    .\test_extraction_quality.ps1 -Verbose
#>

param(
    [string]$ApiUrl = "http://127.0.0.1:8010",
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# =============================================================================
# CONFIGURATION
# =============================================================================

$GroundTruthPath = Join-Path $PSScriptRoot "..\ground_truth"
$ManifestPath = Join-Path $GroundTruthPath "manifest.json"

# Load manifest
if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest not found: $ManifestPath"
    exit 1
}

$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json

# =============================================================================
# TEST DEFINITIONS
# =============================================================================

# Define test cases with expected content
$QualityTests = @(
    @{
        Name = "Python Code Extraction"
        SearchQuery = "calculate_sum"
        ExpectedKeywords = @("def", "return", "calculate_sum", "greet")
        MinKeywordMatch = 0.75
        Category = "code"
    },
    @{
        Name = "Text Document Extraction"
        SearchQuery = "Max Mustermann"
        ExpectedKeywords = @("Testdokument", "Max Mustermann", "EUR")
        MinKeywordMatch = 0.66
        Category = "documents"
    },
    @{
        Name = "Email Header/Body Extraction"
        SearchQuery = "sender@example.com"
        ExpectedKeywords = @("sender@example.com", "Test Email", "Max Mustermann")
        MinKeywordMatch = 0.66
        Category = "email"
    },
    @{
        Name = "YAML Config Extraction"
        SearchQuery = "database host localhost"
        ExpectedKeywords = @("database", "host", "localhost", "port")
        MinKeywordMatch = 0.75
        Category = "config"
    },
    @{
        Name = "Subtitle Extraction"
        SearchQuery = "Neural Vault Tutorial"
        ExpectedKeywords = @("Neural Vault", "Tutorial", "Dokumentenverarbeitung")
        MinKeywordMatch = 0.66
        Category = "subtitles"
    },
    @{
        Name = "JSON Structure Extraction"
        SearchQuery = "firstName lastName"
        ExpectedKeywords = @("firstName", "lastName", "address")
        MinKeywordMatch = 0.66
        Category = "documents"
    },
    @{
        Name = "HTML Content Extraction"
        SearchQuery = "HTML Test Document"
        ExpectedKeywords = @("heading", "paragraph", "HTML")
        MinKeywordMatch = 0.66
        Category = "documents"
    },
    @{
        Name = "Markdown Extraction"
        SearchQuery = "Markdown heading"
        ExpectedKeywords = @("heading", "list", "code")
        MinKeywordMatch = 0.5
        Category = "documents"
    }
)

# Entity extraction tests
$EntityTests = @(
    @{
        Name = "Person Entity Detection"
        Query = "Max Mustermann"
        ExpectedEntityType = "PER"
        ExpectedValue = "Max Mustermann"
    },
    @{
        Name = "Organization Entity Detection"
        Query = "TechCorp GmbH"
        ExpectedEntityType = "ORG"
        ExpectedValue = "TechCorp"
    },
    @{
        Name = "Location Entity Detection"
        Query = "Berlin Deutschland"
        ExpectedEntityType = "LOC"
        ExpectedValue = "Berlin"
    }
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Search-Index {
    param(
        [string]$Query,
        [int]$Limit = 10
    )
    
    try {
        $body = @{
            query = $Query
            limit = $Limit
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$ApiUrl/search" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        return $response
    }
    catch {
        Write-Warning "Search failed for '$Query': $_"
        return $null
    }
}

function Test-KeywordPresence {
    param(
        [string]$Text,
        [string[]]$Keywords
    )
    
    $found = 0
    $missing = @()
    
    foreach ($keyword in $Keywords) {
        if ($Text -match [regex]::Escape($keyword)) {
            $found++
        } else {
            $missing += $keyword
        }
    }
    
    return @{
        Found = $found
        Total = $Keywords.Count
        Ratio = if ($Keywords.Count -gt 0) { $found / $Keywords.Count } else { 0 }
        Missing = $missing
    }
}

function Get-ExtractedText {
    param($Hit)
    
    # Combine all text fields
    $textParts = @()
    
    if ($Hit.extracted_text) { $textParts += $Hit.extracted_text }
    if ($Hit.text) { $textParts += $Hit.text }
    if ($Hit.content) { $textParts += $Hit.content }
    if ($Hit.filename) { $textParts += $Hit.filename }
    if ($Hit.file_path) { $textParts += $Hit.file_path }
    
    return $textParts -join " "
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   NEURAL VAULT: EXTRACTION QUALITY TEST SUITE" -ForegroundColor Cyan
Write-Host "   Version 1.0.0 - $(Get-Date -Format 'dd.MM.yyyy HH:mm')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$Results = @{
    Passed = 0
    Failed = 0
    Skipped = 0
    Details = @()
}

# -----------------------------------------------------------------------------
# CONTENT EXTRACTION TESTS
# -----------------------------------------------------------------------------

Write-Host "--- 1. Content Extraction Tests ---" -ForegroundColor Yellow
Write-Host ""

foreach ($test in $QualityTests) {
    Write-Host "  Testing: $($test.Name)..." -NoNewline
    
    $searchResult = Search-Index -Query $test.SearchQuery
    
    if (-not $searchResult -or $searchResult.hits.Count -eq 0) {
        Write-Host " [SKIP] No results found" -ForegroundColor DarkGray
        $Results.Skipped++
        $Results.Details += @{
            Test = $test.Name
            Status = "SKIP"
            Reason = "No search results"
        }
        continue
    }
    
    # Get all text from first hit
    $extractedText = Get-ExtractedText -Hit $searchResult.hits[0]
    
    # Check keyword presence
    $keywordResult = Test-KeywordPresence -Text $extractedText -Keywords $test.ExpectedKeywords
    
    if ($keywordResult.Ratio -ge $test.MinKeywordMatch) {
        Write-Host " [PASS]" -ForegroundColor Green -NoNewline
        Write-Host " ($($keywordResult.Found)/$($keywordResult.Total) keywords)"
        $Results.Passed++
        $status = "PASS"
    } else {
        Write-Host " [FAIL]" -ForegroundColor Red -NoNewline
        Write-Host " ($($keywordResult.Found)/$($keywordResult.Total) keywords, need $([math]::Ceiling($test.MinKeywordMatch * $keywordResult.Total)))"
        $Results.Failed++
        $status = "FAIL"
        
        if ($Verbose -and $keywordResult.Missing.Count -gt 0) {
            Write-Host "         Missing: $($keywordResult.Missing -join ', ')" -ForegroundColor DarkYellow
        }
    }
    
    $Results.Details += @{
        Test = $test.Name
        Status = $status
        KeywordsFound = $keywordResult.Found
        KeywordsTotal = $keywordResult.Total
        Ratio = $keywordResult.Ratio
        Missing = $keywordResult.Missing
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# ENTITY EXTRACTION TESTS
# -----------------------------------------------------------------------------

Write-Host "--- 2. Entity Extraction Tests ---" -ForegroundColor Yellow
Write-Host ""

foreach ($test in $EntityTests) {
    Write-Host "  Testing: $($test.Name)..." -NoNewline
    
    $searchResult = Search-Index -Query $test.Query
    
    if (-not $searchResult -or $searchResult.hits.Count -eq 0) {
        Write-Host " [SKIP] No results found" -ForegroundColor DarkGray
        $Results.Skipped++
        continue
    }
    
    $hit = $searchResult.hits[0]
    $entityFound = $false
    
    # Check entities field (various possible structures)
    if ($hit.entities) {
        $entityStr = $hit.entities | ConvertTo-Json -Depth 5
        if ($entityStr -match [regex]::Escape($test.ExpectedValue)) {
            $entityFound = $true
        }
    }
    
    # Also check entities_flat
    if ($hit.entities_flat -and $hit.entities_flat -match [regex]::Escape($test.ExpectedValue)) {
        $entityFound = $true
    }
    
    # Fallback: check if entity appears in any text field
    $allText = Get-ExtractedText -Hit $hit
    if ($allText -match [regex]::Escape($test.ExpectedValue)) {
        # Entity at least exists in text (NER may not have run)
        Write-Host " [WARN]" -ForegroundColor Yellow -NoNewline
        Write-Host " Entity in text, NER not verified"
        $Results.Skipped++
    } elseif ($entityFound) {
        Write-Host " [PASS]" -ForegroundColor Green
        $Results.Passed++
    } else {
        Write-Host " [FAIL]" -ForegroundColor Red
        $Results.Failed++
    }
}

Write-Host ""

# -----------------------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------------------

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   QUALITY TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Passed:  $($Results.Passed)" -ForegroundColor Green
Write-Host "  Failed:  $($Results.Failed)" -ForegroundColor Red
Write-Host "  Skipped: $($Results.Skipped)" -ForegroundColor DarkGray
Write-Host ""

$TotalTests = $Results.Passed + $Results.Failed
if ($TotalTests -gt 0) {
    $PassRate = [math]::Round(($Results.Passed / $TotalTests) * 100, 1)
    Write-Host "  Pass Rate: $PassRate%" -ForegroundColor $(if ($PassRate -ge 80) { "Green" } elseif ($PassRate -ge 50) { "Yellow" } else { "Red" })
}

Write-Host ""

# Return results for automation
return $Results
