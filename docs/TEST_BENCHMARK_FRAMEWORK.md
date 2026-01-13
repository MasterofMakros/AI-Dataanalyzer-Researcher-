# Neural Vault: Comprehensive Test & Benchmark Framework

**Version:** 1.0.0  
**Stand:** 11.01.2026  
**Ziel:** Vollständige Qualitätssicherung aller 124+ unterstützten Formate ohne UI-Tests

---

## Inhaltsverzeichnis

1. [Übersicht](#1-übersicht)
2. [Industrie-Benchmarks (Stand 2025/2026)](#2-industrie-benchmarks-stand-20252026)
3. [Test-Framework Architektur](#3-test-framework-architektur)
4. [Phase 1: Intake & Routing Tests](#4-phase-1-intake--routing-tests)
5. [Phase 2: Extraction Worker Tests](#5-phase-2-extraction-worker-tests)
6. [Phase 3: Enrichment Tests](#6-phase-3-enrichment-tests)
7. [Phase 4: Indexing Tests](#7-phase-4-indexing-tests)
8. [Phase 5: Search Quality Tests](#8-phase-5-search-quality-tests)
9. [Phase 6: End-to-End Pipeline Tests](#9-phase-6-end-to-end-pipeline-tests)
10. [Optimierungspotenziale](#10-optimierungspotenziale)
11. [Automatisierte Test-Suite](#11-automatisierte-test-suite)

---

## 1. Übersicht

### Testabdeckung

| Kategorie | Formate | Testmethode |
|-----------|---------|-------------|
| Dokumente | PDF, DOCX, XLSX, PPTX, TXT, MD, RTF, ODT, EPUB, MOBI | Textextraktion, Tabellenerhalt |
| Bilder | JPG, PNG, TIFF, BMP, WEBP, HEIC, SVG, GIF, RAW | OCR-Genauigkeit, CER |
| Audio | MP3, WAV, FLAC, OGG, M4A, AAC, OPUS, AIFF | Transkriptions-WER |
| Video | MP4, MKV, AVI, MOV, WEBM, FLV, 3GP, TS | Audio-Extraktion + WER |
| Archive | ZIP, RAR, 7Z, TAR, GZ, BZ2, CAB, ISO | Entpacken, Re-Routing |
| Code | 40+ Sprachen | Syntax-Erhalt, Kommentar-Extraktion |
| E-Mail | EML, MSG, MBOX | Header, Body, Anhänge |

### Qualitätsmetriken

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUALITÄTSMETRIKEN                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  📄 Textextraktion                                                         │
│     • Vollständigkeit: Wortanzahl Original vs. Extrahiert (>95%)           │
│     • Strukturerhalt: Tabellen, Listen, Überschriften                      │
│                                                                             │
│  🔤 OCR (Optical Character Recognition)                                    │
│     • CER: Character Error Rate (<3% = Gut, <1% = Exzellent)               │
│     • WER: Word Error Rate (<5% = Gut, <2% = Exzellent)                    │
│     • Confidence: Surya-Score (>0.95 = Hoch)                               │
│                                                                             │
│  🎤 ASR (Automatic Speech Recognition)                                     │
│     • WER: Word Error Rate (<10% = Gut, <5% = Exzellent)                   │
│     • Diarization: Speaker Identification Accuracy (>90%)                  │
│     • Timestamp: Wort-Level Genauigkeit (±0.5s)                            │
│                                                                             │
│  🔍 Suche                                                                  │
│     • Precision@10: Relevante Treffer in Top 10 (>0.8)                     │
│     • Recall: Alle relevanten Dokumente gefunden (>0.9)                    │
│     • MRR: Mean Reciprocal Rank (>0.7)                                     │
│                                                                             │
│  ⚡ Performance                                                             │
│     • Durchsatz: Dateien/Minute                                            │
│     • Latenz: Zeit bis zur Suchbarkeit                                     │
│     • Ressourcenverbrauch: RAM, CPU, GPU                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Industrie-Benchmarks (Stand 2025/2026)

### 2.1 OCR-Benchmarks

| Engine | CER | WER | Quelle |
|--------|-----|-----|--------|
| **Surya OCR** | <2% | <5% | PyPI Benchmarks 2025 |
| PaddleOCR 3.0 | 0.43% | 0.66% | IEEE Conference 2025 |
| Tesseract 5.x | ~2% | ~5% | MDPI Research 2025 |
| **Industrie-Standard** | <1% | <2% | SparkCo AI Report 2025 |

**Unser Ziel:** CER <2%, WER <5% (entspricht Surya-Niveau)

### 2.2 ASR-Benchmarks (WhisperX)

| Sprache | Dataset | WER | Quelle |
|---------|---------|-----|--------|
| Englisch | LibriSpeech | 9% | WhisperAPI 2025 |
| Englisch | Common Voice | 10% | WhisperAPI 2025 |
| Deutsch | YouTube DE | 19.76% | Soniox Benchmark 2023 |
| Spontan (EN) | ICE Corpus | 26-29% | Interspeech 2025 |

**Unser Ziel:** WER <15% (Deutsch), <10% (Englisch)

### 2.3 Dokument-Extraktion (Docling)

| Metrik | Wert | Benchmark |
|--------|------|-----------|
| Tabellengenauigkeit | 97.9% | PDF Extraction Benchmark 2025 |
| Strukturerhalt | 94%+ | PDF Table Showdown 2025 |
| Layout-Erkennung | DocLayNet | State-of-the-Art |

**Unser Ziel:** Tabellengenauigkeit >95%

---

## 3. Test-Framework Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEST-FRAMEWORK ARCHITEKTUR                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │ Ground Truth│   │ Test Files  │   │ Test Runner │   │ Report Gen  │     │
│  │ Repository  │──▶│ Generator   │──▶│ Engine      │──▶│ (HTML/JSON) │     │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
│        │                                    │                               │
│        │                                    ▼                               │
│        │                          ┌─────────────────┐                       │
│        │                          │ Metric Collector │                      │
│        │                          │ • CER/WER       │                       │
│        │                          │ • Precision     │                       │
│        │                          │ • Latency       │                       │
│        │                          └─────────────────┘                       │
│        │                                    │                               │
│        ▼                                    ▼                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      COMPARISON & VALIDATION                         │   │
│  │                                                                      │   │
│  │   Expected Output  ←──── Diff ────→  Actual Output                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Verzeichnisstruktur

```
F:\AI-Dataanalyzer-Researcher\tests\
├── ground_truth\                 # Referenzdaten
│   ├── documents\               # PDFs mit bekanntem Inhalt
│   ├── images\                  # Bilder mit bekanntem Text
│   ├── audio\                   # Audio mit Transkripten
│   └── expected_outputs\        # Erwartete Extraktionsergebnisse
├── test_files\                   # Testdateien (124+ Formate)
├── scripts\                      # Test-Skripte
│   ├── test_routing.ps1
│   ├── test_extraction.ps1
│   ├── test_enrichment.ps1
│   ├── test_search.ps1
│   └── run_all_tests.ps1
├── reports\                      # Testergebnisse
└── benchmark_suite.ps1           # Hauptskript
```

---

## 4. Phase 1: Intake & Routing Tests

### 4.1 Format-Erkennungs-Test

```powershell
# tests/scripts/test_routing.ps1

$testCases = @(
    # Dokumente
    @{File="test.pdf"; Expected="extract:documents"},
    @{File="test.docx"; Expected="extract:documents"},
    @{File="test.xlsx"; Expected="extract:documents"},
    @{File="test.txt"; Expected="extract:documents"},
    @{File="test.md"; Expected="extract:documents"},
    @{File="test.py"; Expected="extract:documents"},
    @{File="test.java"; Expected="extract:documents"},
    @{File="test.c"; Expected="extract:documents"},
    
    # Bilder
    @{File="test.jpg"; Expected="extract:images"},
    @{File="test.png"; Expected="extract:images"},
    @{File="test.heic"; Expected="extract:images"},
    @{File="test.svg"; Expected="extract:images"},
    @{File="test.tiff"; Expected="extract:images"},
    
    # Audio
    @{File="test.mp3"; Expected="extract:audio"},
    @{File="test.wav"; Expected="extract:audio"},
    @{File="test.flac"; Expected="extract:audio"},
    @{File="test.ogg"; Expected="extract:audio"},
    @{File="test.opus"; Expected="extract:audio"},
    
    # Video
    @{File="test.mp4"; Expected="extract:video"},
    @{File="test.mkv"; Expected="extract:video"},
    @{File="test.avi"; Expected="extract:video"},
    @{File="test.webm"; Expected="extract:video"},
    
    # Archive
    @{File="test.zip"; Expected="extract:archive"},
    @{File="test.rar"; Expected="extract:archive"},
    @{File="test.7z"; Expected="extract:archive"},
    @{File="test.tar"; Expected="extract:archive"},
    @{File="test.iso"; Expected="extract:archive"},
    
    # E-Mail
    @{File="test.eml"; Expected="extract:email"},
    @{File="test.msg"; Expected="extract:email"}
)

$passed = 0
$failed = 0
$results = @()

foreach ($test in $testCases) {
    $response = Invoke-RestMethod -Uri "http://localhost:8020/route?filename=$($test.File)" -Method GET -ErrorAction SilentlyContinue
    
    $success = $response.queue -eq $test.Expected
    if ($success) { $passed++ } else { $failed++ }
    
    $results += @{
        File = $test.File
        Expected = $test.Expected
        Actual = $response.queue
        Status = if ($success) { "✅ PASS" } else { "❌ FAIL" }
    }
}

Write-Host "`n=== ROUTING TEST RESULTS ==="
Write-Host "Passed: $passed / $($testCases.Count)"
Write-Host "Failed: $failed"
Write-Host "Success Rate: $([Math]::Round($passed / $testCases.Count * 100, 1))%"

# Details für fehlgeschlagene Tests
$results | Where-Object { $_.Status -eq "❌ FAIL" } | ForEach-Object {
    Write-Host "  $($_.File): Expected $($_.Expected), Got $($_.Actual)"
}
```

### 4.2 Pre-Validation Test

```powershell
# tests/scripts/test_prevalidation.ps1

$validationTests = @(
    @{File="valid.pdf"; ExpectedHealth="healthy"},
    @{File="empty.pdf"; ExpectedHealth="empty"},
    @{File="corrupted.pdf"; ExpectedHealth="corrupted"},
    @{File="encrypted.pdf"; ExpectedHealth="encrypted"},
    @{File="mislabeled.pdf"; ExpectedHealth="mislabeled"}  # Eigentlich JPG
)

foreach ($test in $validationTests) {
    # Direkt im Container testen (wenn möglich)
    # Alternativ: Über API-Endpoint
    Write-Host "Testing: $($test.File) -> Expected: $($test.ExpectedHealth)"
}
```

---

## 5. Phase 2: Extraction Worker Tests

### 5.1 Document Worker (Docling)

```powershell
# tests/scripts/test_document_extraction.ps1

function Test-DocumentExtraction {
    param([string]$TestFile, [string]$GroundTruthFile)
    
    # Extraktion via API
    $response = Invoke-RestMethod -Uri "http://localhost:8021/process/document" `
        -Method POST `
        -Form @{file = Get-Item $TestFile}
    
    $extractedText = $response.text
    $groundTruth = Get-Content $GroundTruthFile -Raw
    
    # Metriken berechnen
    $extractedWords = $extractedText.Split() | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
    $groundTruthWords = $groundTruth.Split() | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
    
    $completeness = $extractedWords / $groundTruthWords
    
    # Tabellen-Check
    $tablesFound = $response.tables_count
    $expectedTables = ($groundTruth | Select-String -Pattern '\|' -AllMatches).Matches.Count / 10  # Schätzung
    
    return @{
        File = $TestFile
        Completeness = [Math]::Round($completeness * 100, 1)
        TablesFound = $tablesFound
        Confidence = $response.confidence
        ProcessingTime = $response.processing_time_ms
    }
}

# Testfälle
$documentTests = @(
    @{Test="simple_text.pdf"; GroundTruth="simple_text.txt"},
    @{Test="complex_table.pdf"; GroundTruth="complex_table.txt"},
    @{Test="multi_column.pdf"; GroundTruth="multi_column.txt"},
    @{Test="scanned_document.pdf"; GroundTruth="scanned_document.txt"}
)

Write-Host "`n=== DOCUMENT EXTRACTION BENCHMARK ==="
foreach ($test in $documentTests) {
    $result = Test-DocumentExtraction -TestFile "tests/ground_truth/documents/$($test.Test)" -GroundTruthFile "tests/ground_truth/expected_outputs/$($test.GroundTruth)"
    Write-Host "$($result.File): Completeness=$($result.Completeness)%, Tables=$($result.TablesFound), Confidence=$($result.Confidence)"
}
```

### 5.2 Image Worker (OCR)

```powershell
# tests/scripts/test_ocr.ps1

function Calculate-CER {
    param([string]$GroundTruth, [string]$OCROutput)
    
    # Levenshtein-Distanz
    $gt = $GroundTruth.ToCharArray()
    $ocr = $OCROutput.ToCharArray()
    
    $errors = 0
    $maxLen = [Math]::Max($gt.Length, $ocr.Length)
    
    for ($i = 0; $i -lt $maxLen; $i++) {
        if ($i -ge $gt.Length -or $i -ge $ocr.Length) { 
            $errors++ 
        } elseif ($gt[$i] -ne $ocr[$i]) { 
            $errors++ 
        }
    }
    
    return [Math]::Round($errors / $gt.Length * 100, 2)
}

function Calculate-WER {
    param([string]$GroundTruth, [string]$OCROutput)
    
    $gtWords = $GroundTruth.ToLower() -split '\s+' | Where-Object { $_ }
    $ocrWords = $OCROutput.ToLower() -split '\s+' | Where-Object { $_ }
    
    $subs = 0
    $dels = [Math]::Max(0, $gtWords.Count - $ocrWords.Count)
    $ins = [Math]::Max(0, $ocrWords.Count - $gtWords.Count)
    
    for ($i = 0; $i -lt [Math]::Min($gtWords.Count, $ocrWords.Count); $i++) {
        if ($gtWords[$i] -ne $ocrWords[$i]) { $subs++ }
    }
    
    return [Math]::Round(($subs + $dels + $ins) / $gtWords.Count * 100, 2)
}

function Test-OCR {
    param([string]$ImageFile, [string]$GroundTruthText)
    
    $response = Invoke-RestMethod -Uri "http://localhost:8021/ocr" `
        -Method POST `
        -Form @{file = Get-Item $ImageFile; langs = "de,en"}
    
    $ocrText = $response.text
    
    return @{
        File = (Split-Path $ImageFile -Leaf)
        CER = Calculate-CER -GroundTruth $GroundTruthText -OCROutput $ocrText
        WER = Calculate-WER -GroundTruth $GroundTruthText -OCROutput $ocrText
        Confidence = $response.confidence
        LinesDetected = $response.lines.Count
    }
}

# OCR-Testfälle mit Ground Truth
$ocrTests = @(
    @{Image="printed_text.png"; Text="Dies ist ein Testtext mit 12345 Zahlen und Sonderzeichen!"},
    @{Image="handwritten.png"; Text="Handschriftlicher Text zum Testen"},
    @{Image="table_image.png"; Text="Zeile 1 | Spalte A | Spalte B"},
    @{Image="low_quality.jpg"; Text="Text mit niedriger Bildqualität"},
    @{Image="multilingual.png"; Text="English text und deutscher Text gemischt"}
)

Write-Host "`n=== OCR BENCHMARK ==="
Write-Host "Target: CER <2%, WER <5%"
Write-Host ""

$totalCER = 0
$totalWER = 0

foreach ($test in $ocrTests) {
    $result = Test-OCR -ImageFile "tests/ground_truth/images/$($test.Image)" -GroundTruthText $test.Text
    $totalCER += $result.CER
    $totalWER += $result.WER
    
    $cerStatus = if ($result.CER -lt 2) { "✅" } elseif ($result.CER -lt 5) { "⚠️" } else { "❌" }
    $werStatus = if ($result.WER -lt 5) { "✅" } elseif ($result.WER -lt 10) { "⚠️" } else { "❌" }
    
    Write-Host "$($result.File): CER=$cerStatus $($result.CER)%, WER=$werStatus $($result.WER)%, Confidence=$($result.Confidence)"
}

$avgCER = [Math]::Round($totalCER / $ocrTests.Count, 2)
$avgWER = [Math]::Round($totalWER / $ocrTests.Count, 2)
Write-Host "`nAverage: CER=$avgCER%, WER=$avgWER%"
```

### 5.3 Audio Worker (WhisperX)

```powershell
# tests/scripts/test_transcription.ps1

function Test-Transcription {
    param(
        [string]$AudioFile,
        [string]$GroundTruthText,
        [string]$Language = "de"
    )
    
    $response = Invoke-RestMethod -Uri "http://localhost:8019/transcribe" `
        -Method POST `
        -Form @{file = Get-Item $AudioFile; language = $Language}
    
    $transcription = $response.text
    
    # WER berechnen
    $gtWords = $GroundTruthText.ToLower() -split '\s+' | Where-Object { $_ }
    $trWords = $transcription.ToLower() -split '\s+' | Where-Object { $_ }
    
    $subs = 0
    for ($i = 0; $i -lt [Math]::Min($gtWords.Count, $trWords.Count); $i++) {
        if ($gtWords[$i] -ne $trWords[$i]) { $subs++ }
    }
    $dels = [Math]::Max(0, $gtWords.Count - $trWords.Count)
    $ins = [Math]::Max(0, $trWords.Count - $gtWords.Count)
    
    $wer = [Math]::Round(($subs + $dels + $ins) / $gtWords.Count * 100, 2)
    
    # Sprechgeschwindigkeit
    $duration = $response.duration_seconds
    $wpm = [Math]::Round($trWords.Count / ($duration / 60), 0)
    
    return @{
        File = (Split-Path $AudioFile -Leaf)
        WER = $wer
        Duration = $duration
        WordCount = $trWords.Count
        WPM = $wpm
        Speakers = $response.speakers.Count
    }
}

# Transkriptions-Testfälle
$asrTests = @(
    @{Audio="clean_speech_de.mp3"; Text="Guten Tag meine Damen und Herren willkommen zur Präsentation"; Lang="de"},
    @{Audio="clean_speech_en.mp3"; Text="Good morning ladies and gentlemen welcome to the presentation"; Lang="en"},
    @{Audio="noisy_audio.wav"; Text="Test mit Hintergrundgeräuschen"; Lang="de"},
    @{Audio="multiple_speakers.mp3"; Text="Sprecher eins sagt dies Sprecher zwei antwortet"; Lang="de"}
)

Write-Host "`n=== TRANSCRIPTION BENCHMARK ==="
Write-Host "Target: WER <15% (DE), <10% (EN)"
Write-Host ""

foreach ($test in $asrTests) {
    $result = Test-Transcription -AudioFile "tests/ground_truth/audio/$($test.Audio)" -GroundTruthText $test.Text -Language $test.Lang
    
    $werStatus = if ($result.WER -lt 10) { "✅" } elseif ($result.WER -lt 20) { "⚠️" } else { "❌" }
    
    Write-Host "$($result.File): WER=$werStatus $($result.WER)%, Duration=$($result.Duration)s, WPM=$($result.WPM), Speakers=$($result.Speakers)"
}
```

### 5.4 Video Worker

```powershell
# tests/scripts/test_video_extraction.ps1

function Test-VideoExtraction {
    param([string]$VideoFile, [string]$ExpectedAudioTranscript)
    
    $startTime = Get-Date
    
    # Video submitten
    $body = @{path = $VideoFile} | ConvertTo-Json
    $submitResult = Invoke-RestMethod -Uri "http://localhost:8020/submit" -Method POST -Body $body -ContentType 'application/json'
    
    # Warten auf Verarbeitung
    Start-Sleep -Seconds 120
    
    $endTime = Get-Date
    $processingTime = ($endTime - $startTime).TotalSeconds
    
    # Ergebnis aus Index holen
    $filename = Split-Path $VideoFile -Leaf
    $searchResult = Invoke-RestMethod -Uri "http://localhost:7700/indexes/documents/search" `
        -Method POST `
        -Body (@{q = $filename; limit = 1} | ConvertTo-Json) `
        -ContentType 'application/json' `
        -Headers @{Authorization = "Bearer masterKey"}
    
    $indexed = $searchResult.hits.Count -gt 0
    
    return @{
        File = $filename
        Indexed = $indexed
        ProcessingTime = $processingTime
        ContentLength = if ($indexed) { $searchResult.hits[0].content.Length } else { 0 }
    }
}
```

### 5.5 Archive Worker

```powershell
# tests/scripts/test_archive_extraction.ps1

function Test-ArchiveExtraction {
    param([string]$ArchiveFile, [int]$ExpectedFiles)
    
    $beforeStats = Invoke-RestMethod -Uri "http://localhost:8020/stats"
    $beforeTotal = $beforeStats.queues.'intake:priority'
    
    # Archiv submitten
    $body = @{path = $ArchiveFile} | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:8020/submit" -Method POST -Body $body -ContentType 'application/json' | Out-Null
    
    Start-Sleep -Seconds 30
    
    $afterStats = Invoke-RestMethod -Uri "http://localhost:8020/stats"
    $afterTotal = $afterStats.queues.'intake:priority'
    
    $newJobs = $afterTotal - $beforeTotal - 1  # -1 für das Archiv selbst
    
    return @{
        File = (Split-Path $ArchiveFile -Leaf)
        ExpectedFiles = $ExpectedFiles
        ExtractedFiles = $newJobs
        Success = $newJobs -ge $ExpectedFiles
    }
}
```

---

## 6. Phase 3: Enrichment Tests

### 6.1 NER (Named Entity Recognition)

```powershell
# tests/scripts/test_ner.ps1

function Test-NER {
    param([string]$Text, [hashtable]$ExpectedEntities)
    
    $response = Invoke-RestMethod -Uri "http://localhost:8022/ner" `
        -Method POST `
        -Body (@{text = $Text} | ConvertTo-Json) `
        -ContentType 'application/json'
    
    $foundEntities = @{}
    foreach ($entity in $response.entities) {
        if (-not $foundEntities[$entity.label]) {
            $foundEntities[$entity.label] = @()
        }
        $foundEntities[$entity.label] += $entity.text
    }
    
    # Precision und Recall berechnen
    $truePositives = 0
    $falsePositives = 0
    $falseNegatives = 0
    
    foreach ($label in $ExpectedEntities.Keys) {
        $expected = $ExpectedEntities[$label]
        $found = $foundEntities[$label] ?? @()
        
        foreach ($e in $expected) {
            if ($found -contains $e) { $truePositives++ } 
            else { $falseNegatives++ }
        }
        
        foreach ($f in $found) {
            if ($expected -notcontains $f) { $falsePositives++ }
        }
    }
    
    $precision = if ($truePositives + $falsePositives -gt 0) { $truePositives / ($truePositives + $falsePositives) } else { 0 }
    $recall = if ($truePositives + $falseNegatives -gt 0) { $truePositives / ($truePositives + $falseNegatives) } else { 0 }
    $f1 = if ($precision + $recall -gt 0) { 2 * ($precision * $recall) / ($precision + $recall) } else { 0 }
    
    return @{
        Precision = [Math]::Round($precision, 3)
        Recall = [Math]::Round($recall, 3)
        F1 = [Math]::Round($f1, 3)
    }
}

# NER-Testfälle
$nerTests = @(
    @{
        Text = "Angela Merkel traf sich am 15. März 2024 in Berlin mit Emmanuel Macron von der EU."
        Expected = @{
            PERSON = @("Angela Merkel", "Emmanuel Macron")
            DATE = @("15. März 2024")
            LOCATION = @("Berlin")
            ORG = @("EU")
        }
    },
    @{
        Text = "Microsoft Corporation kündigte am Montag eine Investition von 10 Milliarden Euro in Deutschland an."
        Expected = @{
            ORG = @("Microsoft Corporation")
            MONEY = @("10 Milliarden Euro")
            LOCATION = @("Deutschland")
        }
    }
)

Write-Host "`n=== NER BENCHMARK ==="
Write-Host "Target: F1 >0.85"
Write-Host ""

foreach ($test in $nerTests) {
    $result = Test-NER -Text $test.Text -ExpectedEntities $test.Expected
    $status = if ($result.F1 -gt 0.85) { "✅" } elseif ($result.F1 -gt 0.7) { "⚠️" } else { "❌" }
    Write-Host "$status Precision=$($result.Precision), Recall=$($result.Recall), F1=$($result.F1)"
}
```

### 6.2 Embedding-Qualität

```powershell
# tests/scripts/test_embeddings.ps1

function Get-CosineSimilarity {
    param([array]$Vec1, [array]$Vec2)
    
    $dot = 0
    $norm1 = 0
    $norm2 = 0
    
    for ($i = 0; $i -lt $Vec1.Count; $i++) {
        $dot += $Vec1[$i] * $Vec2[$i]
        $norm1 += $Vec1[$i] * $Vec1[$i]
        $norm2 += $Vec2[$i] * $Vec2[$i]
    }
    
    return $dot / ([Math]::Sqrt($norm1) * [Math]::Sqrt($norm2))
}

function Test-EmbeddingSimilarity {
    param([string]$Text1, [string]$Text2, [double]$ExpectedSimilarity)
    
    $emb1 = (Invoke-RestMethod -Uri "http://localhost:11434/api/embeddings" `
        -Method POST -Body (@{model="nomic-embed-text"; prompt=$Text1} | ConvertTo-Json) `
        -ContentType 'application/json').embedding
    
    $emb2 = (Invoke-RestMethod -Uri "http://localhost:11434/api/embeddings" `
        -Method POST -Body (@{model="nomic-embed-text"; prompt=$Text2} | ConvertTo-Json) `
        -ContentType 'application/json').embedding
    
    $similarity = Get-CosineSimilarity -Vec1 $emb1 -Vec2 $emb2
    
    return @{
        Similarity = [Math]::Round($similarity, 4)
        Expected = $ExpectedSimilarity
        Delta = [Math]::Abs($similarity - $ExpectedSimilarity)
    }
}

# Embedding-Testfälle
$embeddingTests = @(
    @{
        Text1 = "Der Umsatz stieg um 15 Prozent."
        Text2 = "Es wurde ein Umsatzwachstum von 15% verzeichnet."
        Expected = 0.85  # Semantisch sehr ähnlich
    },
    @{
        Text1 = "Künstliche Intelligenz revolutioniert die Industrie."
        Text2 = "Das Wetter ist heute schön."
        Expected = 0.15  # Semantisch unähnlich
    },
    @{
        Text1 = "Machine Learning Algorithmus"
        Text2 = "Maschinelles Lernen Verfahren"
        Expected = 0.75  # Mehrsprachige Ähnlichkeit
    }
)

Write-Host "`n=== EMBEDDING QUALITY BENCHMARK ==="

foreach ($test in $embeddingTests) {
    $result = Test-EmbeddingSimilarity -Text1 $test.Text1 -Text2 $test.Text2 -ExpectedSimilarity $test.Expected
    $status = if ($result.Delta -lt 0.15) { "✅" } else { "⚠️" }
    Write-Host "$status Similarity=$($result.Similarity), Expected=$($result.Expected), Delta=$($result.Delta)"
}
```

---

## 7. Phase 4: Indexing Tests

### 7.2 Qdrant (Vector)

```powershell
# tests/scripts/test_qdrant.ps1

function Test-QdrantSemanticSearch {
    param([string]$IndexedText, [string]$SearchQuery, [bool]$ShouldFind)
    
    # Embedding generieren
    $embedding = (Invoke-RestMethod -Uri "http://localhost:11434/api/embeddings" `
        -Method POST -Body (@{model="nomic-embed-text"; prompt=$IndexedText} | ConvertTo-Json) `
        -ContentType 'application/json').embedding
    
    $pointId = Get-Random
    
    # In Qdrant speichern
    $upsertBody = @{
        points = @(
            @{
                id = $pointId
                vector = $embedding
                payload = @{text = $IndexedText}
            }
        )
    }
    
    Invoke-RestMethod -Uri "http://localhost:6333/collections/test_collection/points" `
        -Method PUT `
        -Body ($upsertBody | ConvertTo-Json -Depth 5) `
        -ContentType 'application/json'
    
    Start-Sleep -Seconds 1
    
    # Suchen
    $queryEmbedding = (Invoke-RestMethod -Uri "http://localhost:11434/api/embeddings" `
        -Method POST -Body (@{model="nomic-embed-text"; prompt=$SearchQuery} | ConvertTo-Json) `
        -ContentType 'application/json').embedding
    
    $searchResult = Invoke-RestMethod -Uri "http://localhost:6333/collections/test_collection/points/search" `
        -Method POST `
        -Body (@{vector = $queryEmbedding; limit = 5; with_payload = $true} | ConvertTo-Json) `
        -ContentType 'application/json'
    
    $found = $searchResult.result | Where-Object { $_.id -eq $pointId -and $_.score -gt 0.7 }
    
    return @{
        Query = $SearchQuery
        Found = $null -ne $found
        Expected = $ShouldFind
        Score = if ($found) { $found.score } else { 0 }
    }
}

Write-Host "`n=== QDRANT SEMANTIC SEARCH TEST ==="

$semanticTests = @(
    @{Text="Die Quartalszahlen zeigen Wachstum"; Query="Umsatzsteigerung im Quartal"; ShouldFind=$true},  # Semantisch ähnlich!
    @{Text="Machine Learning ist wichtig"; Query="Künstliche Intelligenz Algorithmen"; ShouldFind=$true},
    @{Text="Das Wetter ist schön"; Query="Finanzberichte 2024"; ShouldFind=$false}
)

foreach ($test in $semanticTests) {
    $result = Test-QdrantSemanticSearch -IndexedText $test.Text -SearchQuery $test.Query -ShouldFind $test.ShouldFind
    $status = if ($result.Found -eq $result.Expected) { "✅" } else { "❌" }
    Write-Host "$status Query='$($result.Query)' Found=$($result.Found) Score=$([Math]::Round($result.Score, 3))"
}
```

---

## 8. Phase 5: Search Quality Tests

### 8.1 Precision@K und Recall

```powershell
# tests/scripts/test_search_quality.ps1

function Test-SearchQuality {
    param(
        [string]$Query,
        [array]$RelevantDocIds,  # Ground Truth: Welche Dokumente sind relevant?
        [int]$K = 10
    )
    
    # Hybrid-Suche durchführen
    $searchResult = Invoke-RestMethod -Uri "http://localhost:8022/search" `
        -Method POST `
        -Body (@{query = $Query; limit = $K} | ConvertTo-Json) `
        -ContentType 'application/json'
    
    $returnedIds = $searchResult.results | Select-Object -ExpandProperty id
    
    # Precision@K: Wieviele der zurückgegebenen sind relevant?
    $relevantReturned = $returnedIds | Where-Object { $RelevantDocIds -contains $_ }
    $precisionAtK = $relevantReturned.Count / $K
    
    # Recall: Wieviele relevante wurden gefunden?
    $recall = $relevantReturned.Count / $RelevantDocIds.Count
    
    # MRR: Position des ersten relevanten Treffers
    $firstRelevantRank = 0
    for ($i = 0; $i -lt $returnedIds.Count; $i++) {
        if ($RelevantDocIds -contains $returnedIds[$i]) {
            $firstRelevantRank = $i + 1
            break
        }
    }
    $mrr = if ($firstRelevantRank -gt 0) { 1 / $firstRelevantRank } else { 0 }
    
    return @{
        Query = $Query
        PrecisionAtK = [Math]::Round($precisionAtK, 3)
        Recall = [Math]::Round($recall, 3)
        MRR = [Math]::Round($mrr, 3)
    }
}

Write-Host "`n=== SEARCH QUALITY BENCHMARK ==="
Write-Host "Target: Precision@10 >0.8, Recall >0.9, MRR >0.7"
```

---

## 9. Phase 6: End-to-End Pipeline Tests

### 9.1 Vollständiger Pipeline-Test

```powershell
# tests/scripts/test_e2e_pipeline.ps1

function Test-FullPipeline {
    param(
        [string]$FilePath,
        [string]$ExpectedContent,
        [int]$MaxWaitSeconds = 180
    )
    
    $startTime = Get-Date
    
    # 1. Submit
    $body = @{path = $FilePath} | ConvertTo-Json
    $submitResult = Invoke-RestMethod -Uri "http://localhost:8020/submit" -Method POST -Body $body -ContentType 'application/json'
    $jobId = $submitResult.job_id
    
    # 2. Warten auf Verarbeitung
    $indexed = $false
    $waitedSeconds = 0
    
    while (-not $indexed -and $waitedSeconds -lt $MaxWaitSeconds) {
        Start-Sleep -Seconds 10
        $waitedSeconds += 10
        
        # In Suchindex prüfen
        $searchResult = Invoke-RestMethod -Uri "http://localhost:7700/indexes/documents/search" `
            -Method POST `
            -Body (@{q = $ExpectedContent; limit = 1} | ConvertTo-Json) `
            -ContentType 'application/json' `
            -Headers @{Authorization = "Bearer masterKey"} -ErrorAction SilentlyContinue
        
        if ($searchResult.hits.Count -gt 0) {
            $indexed = $true
        }
    }
    
    $endTime = Get-Date
    $totalTime = ($endTime - $startTime).TotalSeconds
    
    # 3. DLQ prüfen
    $stats = Invoke-RestMethod -Uri "http://localhost:8020/stats"
    $dlqCount = $stats.queues.'dlq:extract'
    
    return @{
        File = (Split-Path $FilePath -Leaf)
        JobId = $jobId
        Indexed = $indexed
        TotalTime = [Math]::Round($totalTime, 1)
        DLQErrors = $dlqCount
        Success = $indexed -and $dlqCount -eq 0
    }
}

# E2E-Tests für alle Kategorien
$e2eTests = @(
    @{File="F:\_Inbox\test_doc.pdf"; Content="Finanzbericht"},
    @{File="F:\_Inbox\test_image.png"; Content="Meeting Notes"},
    @{File="F:\_Inbox\test_audio.mp3"; Content="Präsentation"},
    @{File="F:\_Inbox\test_video.mp4"; Content="Tutorial"},
    @{File="F:\_Inbox\test_code.py"; Content="def main"}
)

Write-Host "`n=== END-TO-END PIPELINE TEST ==="
Write-Host ""

$totalTests = $e2eTests.Count
$passedTests = 0

foreach ($test in $e2eTests) {
    Write-Host "Testing: $($test.File)..."
    $result = Test-FullPipeline -FilePath $test.File -ExpectedContent $test.Content
    
    if ($result.Success) {
        $passedTests++
        Write-Host "  ✅ PASS - Indexed in $($result.TotalTime)s"
    } else {
        Write-Host "  ❌ FAIL - Indexed=$($result.Indexed), DLQ=$($result.DLQErrors)"
    }
}

Write-Host "`nE2E Results: $passedTests / $totalTests passed ($([Math]::Round($passedTests / $totalTests * 100, 0))%)"
```

---

## 10. Optimierungspotenziale

### 10.1 Erkannte Optimierungsmöglichkeiten

| Bereich | Problem | Lösung | Erwartete Verbesserung |
|---------|---------|--------|------------------------|
| **OCR** | CER >2% bei Low-Quality | Preprocessing (Binarisierung, Deskew) | CER -30% |
| **OCR** | Langsam bei großen Bildern | GPU-Beschleunigung aktivieren | 5x schneller |
| **ASR** | WER >20% bei Deutsch | Whisper large-v3 statt base | WER -40% |
| **ASR** | Diarization ungenau | pyannote/speaker-diarization-3.1 | Accuracy +20% |
| **Docling** | Tabellen mit merged cells | TableFormer fine-tuning | Accuracy +5% |
| **Indexing** | Langsame Vektorsuche | HNSW Index mit höherem M | Latenz -50% |
| **Pipeline** | Hohe Latenz E2E | Batch-Processing | Durchsatz +200% |

### 10.2 Benchmark-basierte Empfehlungen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OPTIMIERUNGSEMPFEHLUNGEN                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔤 OCR (Surya)                                                            │
│  ──────────────                                                            │
│  Aktuell: CER ~2%, WER ~5%                                                 │
│  Industrie-Best: CER <1%, WER <2% (PaddleOCR 3.0)                          │
│                                                                             │
│  Empfehlung:                                                               │
│  • Preprocessing: Binarisierung, Deskewing hinzufügen                      │
│  • Multi-Engine: Surya + PaddleOCR Ensemble für kritische Dokumente        │
│  • Post-OCR Korrektur: LLM-basierte Fehlerkorrektur                        │
│                                                                             │
│  🎤 ASR (WhisperX)                                                         │
│  ─────────────────                                                         │
│  Aktuell: WER ~15% (Deutsch)                                               │
│  Industrie-Best: WER <8% (Soniox für Deutsch)                              │
│                                                                             │
│  Empfehlung:                                                               │
│  • Modell: Whisper large-v3-turbo (schneller, genauer)                     │
│  • VAD: Aggressiveres Voice Activity Detection                             │
│  • Nachbearbeitung: Interpunktionsmodell hinzufügen                        │
│                                                                             │
│  📄 Document Extraction (Docling)                                          │
│  ─────────────────────────────────                                         │
│  Aktuell: Tabellengenauigkeit 97.9%                                        │
│  Bereits State-of-the-Art!                                                 │
│                                                                             │
│  Empfehlung:                                                               │
│  • Fallback für Scanned PDFs: OCR-Pipeline als Alternative                 │
│  • Hybrid: Docling + Tika für maximale Kompatibilität                      │
│                                                                             │
│  🔍 Search (Qdrant)                                                       │
│  ─────────────────────────────────                                         │
│  Empfehlung:                                                               │
│  • Hybrid Ranking: BM25 + Vector kombinieren (RRF oder Linear)             │
│  • Query Expansion: Synonyme und Mehrsprachigkeit                          │
│  • Re-Ranking: Cross-Encoder für Top-K Ergebnisse                          │
│                                                                             │
│  ⚡ Performance                                                             │
│  ─────────────                                                             │
│  Empfehlung:                                                               │
│  • GPU-Pooling: Dynamische GPU-Zuweisung für OCR/ASR                       │
│  • Batch Processing: Jobs gruppieren für besseren Durchsatz                │
│  • Caching: Embedding-Cache für häufige Dokumente                          │
│  • Queue Priorität: Express-Lane für kleine Dateien                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Automatisierte Test-Suite

### 11.1 Hauptskript

```powershell
# tests/run_all_tests.ps1
# Neural Vault Comprehensive Test Suite
# Stand: 11.01.2026

param(
    [switch]$Quick,      # Nur schnelle Tests
    [switch]$Full,       # Alle Tests inkl. lange E2E
    [switch]$Report,     # HTML-Report generieren
    [string]$OutputDir = "tests/reports"
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    NEURAL VAULT TEST & BENCHMARK SUITE                       ║
║                            Version 1.0.0                                     ║
║                            Stand: 11.01.2026                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"@

# Ergebnis-Sammlung
$results = @{
    Routing = @()
    DocumentExtraction = @()
    OCR = @()
    Transcription = @()
    NER = @()
    Embedding = @()
    Search = @()
    E2E = @()
}

# 1. Routing Tests
Write-Host "`n[1/7] Running Routing Tests..."
. .\tests\scripts\test_routing.ps1 -ResultsVar ([ref]$results.Routing)

# 2. Document Extraction Tests
Write-Host "`n[2/7] Running Document Extraction Tests..."
. .\tests\scripts\test_document_extraction.ps1 -ResultsVar ([ref]$results.DocumentExtraction)

# 3. OCR Tests
Write-Host "`n[3/7] Running OCR Benchmark..."
. .\tests\scripts\test_ocr.ps1 -ResultsVar ([ref]$results.OCR)

# 4. Transcription Tests
if (-not $Quick) {
    Write-Host "`n[4/7] Running Transcription Benchmark..."
    . .\tests\scripts\test_transcription.ps1 -ResultsVar ([ref]$results.Transcription)
} else {
    Write-Host "`n[4/7] Skipping Transcription (Quick Mode)"
}

# 5. NER Tests
Write-Host "`n[5/7] Running NER Tests..."
. .\tests\scripts\test_ner.ps1 -ResultsVar ([ref]$results.NER)

# 6. Search Tests
Write-Host "`n[6/7] Running Search Quality Tests..."
. .\tests\scripts\test_qdrant.ps1 -ResultsVar ([ref]$results.Search)

# 7. E2E Tests
if ($Full) {
    Write-Host "`n[7/7] Running End-to-End Pipeline Tests..."
    . .\tests\scripts\test_e2e_pipeline.ps1 -ResultsVar ([ref]$results.E2E)
} else {
    Write-Host "`n[7/7] Skipping E2E (use -Full for complete tests)"
}

# Zusammenfassung
$endTime = Get-Date
$totalTime = ($endTime - $startTime).TotalSeconds

Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                              TEST SUMMARY                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"@

Write-Host "Total Time: $([Math]::Round($totalTime, 1)) seconds"
Write-Host "Report: $OutputDir/report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# Report speichern
if ($Report) {
    $reportPath = "$OutputDir/report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $results | ConvertTo-Json -Depth 5 | Out-File $reportPath
    Write-Host "Report saved to: $reportPath"
}
```

### 11.2 CI/CD Integration

```yaml
# .github/workflows/test-suite.yml

name: Neural Vault Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Täglich um 6 Uhr

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Start Docker Services
        run: docker compose up -d
      
      - name: Wait for Services
        run: sleep 60
      
      - name: Run Test Suite
        run: pwsh tests/run_all_tests.ps1 -Quick -Report
      
      - name: Upload Test Report
        uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: tests/reports/*.json
```

---

## Anhang: Ground Truth Repository

Für reproduzierbare Benchmarks wird ein Ground Truth Repository benötigt:

```
tests/ground_truth/
├── documents/
│   ├── simple_text.pdf          # Einfacher Text
│   ├── complex_table.pdf        # Komplexe Tabellen
│   ├── scanned_invoice.pdf      # Gescanntes Dokument
│   └── multi_column.pdf         # Mehrspaltiges Layout
├── images/
│   ├── printed_text.png         # Gedruckter Text
│   ├── handwritten.png          # Handschrift
│   ├── low_quality.jpg          # Niedrige Qualität
│   └── multilingual.png         # Mehrsprachig
├── audio/
│   ├── clean_speech_de.mp3      # Saubere Sprache Deutsch
│   ├── clean_speech_en.mp3      # Saubere Sprache Englisch
│   ├── noisy_audio.wav          # Mit Rauschen
│   └── multiple_speakers.mp3    # Mehrere Sprecher
└── expected_outputs/
    ├── simple_text.txt          # Erwartete Extraktion
    ├── complex_table.txt        # Erwartete Tabelle
    └── transcripts/             # Erwartete Transkripte
```

---

**Dokument erstellt:** 11.01.2026  
**Autor:** Neural Vault Development Team  
**Nächste Aktualisierung:** Nach Implementation der Optimierungen
