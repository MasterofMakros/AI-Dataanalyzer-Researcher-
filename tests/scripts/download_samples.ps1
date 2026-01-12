# Binary Format Sample Downloader
# Downloads sample files for images, audio, video, archive formats
# Stand: 11.01.2026

param(
    [switch]$Force
)

$baseDir = "F:\AI-Dataanalyzer-Researcher\tests\ground_truth"

# ============================================================================
# SAMPLE SOURCES (Ã–ffentliche Test-Repositories)
# ============================================================================

$samples = @{
    # Images
    images = @{
        directory = "$baseDir\images"
        files = @(
            @{Name="test_photo.jpg"; Url="https://www.w3schools.com/css/img_5terre.jpg"; Description="Landscape photo with text overlay"},
            @{Name="test_diagram.png"; Url="https://www.w3schools.com/css/img_forest.jpg"; Description="Forest image"},
            @{Name="test_icon.gif"; Url="https://upload.wikimedia.org/wikipedia/commons/2/2c/Rotating_earth_%28large%29.gif"; Description="Animated GIF"},
            @{Name="test_logo.bmp"; Url="https://filesamples.com/samples/image/bmp/sample_640%C3%97426.bmp"; Description="BMP sample"},
            @{Name="test_webp.webp"; Url="https://www.gstatic.com/webp/gallery/1.webp"; Description="WebP sample from Google"}
        )
    }
    
    # Audio
    audio = @{
        directory = "$baseDir\audio"
        files = @(
            @{Name="test_speech.mp3"; Url="https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav"; Description="Sample audio"},
            @{Name="test_music.wav"; Url="https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav"; Description="Star Wars theme"},
            @{Name="test_voice.ogg"; Url="https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"; Description="Voice sample from Wikipedia"}
        )
    }
    # Rare Audio
    rare_audio = @{
        directory = "$baseDir\audio"
        files = @(
            @{Name="test.wma"; Url="https://filesamples.com/samples/audio/wma/sample1.wma"; Description="WMA sample"},
            @{Name="test.aac"; Url="https://filesamples.com/samples/audio/aac/sample1.aac"; Description="AAC sample"},
            @{Name="test.m4a"; Url="https://filesamples.com/samples/audio/m4a/sample1.m4a"; Description="M4A sample"},
            @{Name="test.flac"; Url="https://filesamples.com/samples/audio/flac/sample1.flac"; Description="FLAC sample"}
        )
    }

    # Rare Video
    rare_video = @{
        directory = "$baseDir\video"
        files = @(
            @{Name="test.wmv"; Url="https://filesamples.com/samples/video/wmv/sample_640x360.wmv"; Description="WMV sample"},
            @{Name="test.avi"; Url="https://filesamples.com/samples/video/avi/sample_640x360.avi"; Description="AVI sample"},
            @{Name="test.mov"; Url="https://filesamples.com/samples/video/mov/sample_640x360.mov"; Description="MOV sample"},
            @{Name="test.flv"; Url="https://filesamples.com/samples/video/flv/sample_640x360.flv"; Description="FLV sample"},
            @{Name="test.mkv"; Url="https://filesamples.com/samples/video/mkv/sample_640x360.mkv"; Description="MKV sample"},
            @{Name="test.webm"; Url="https://filesamples.com/samples/video/webm/sample_640x360.webm"; Description="WebM sample"}
        )
    }

    # Images (Rare)
    rare_images = @{
        directory = "$baseDir\images"
        files = @(
            @{Name="test.psd"; Url="https://filesamples.com/samples/image/psd/sample.psd"; Description="PSD sample"},
            @{Name="test.tiff"; Url="https://filesamples.com/samples/image/tiff/sample_640x426.tiff"; Description="TIFF sample"},
            @{Name="test.cr2"; Url="https://filesamples.com/samples/image/cr2/sample_640x426.cr2"; Description="Canon Raw"},
            @{Name="test.nef"; Url="https://filesamples.com/samples/image/nef/sample_640x426.nef"; Description="Nikon Raw"},
            @{Name="test.ico"; Url="https://filesamples.com/samples/image/ico/sample_640x426.ico"; Description="Icon sample"}
        )
    }

    # eBooks
    ebooks = @{
        directory = "$baseDir\ebooks"
        files = @(
            @{Name="test.epub"; Url="https://filesamples.com/samples/ebook/epub/A%20Midsummer%20Night's%20Dream.epub"; Description="EPUB sample"},
            @{Name="test.mobi"; Url="https://filesamples.com/samples/ebook/mobi/A%20Midsummer%20Night's%20Dream.mobi"; Description="MOBI sample"},
            @{Name="test.azw3"; Url="https://filesamples.com/samples/ebook/azw3/A%20Midsummer%20Night's%20Dream.azw3"; Description="AZW3 sample"},
            @{Name="test.djvu"; Url="https://file-examples.com/storage/fe1f7d92f2189e0c4c7b0c5/2017/10/file_example_DJVU_1.djvu"; Description="DjVu sample"}
        )
    }

    # Apps (Android/iOS)
    apps = @{
        directory = "$baseDir\apps"
        files = @(
            @{Name="test.apk"; Url="https://github.com/appium/sample-code/blob/master/sample-code/apps/ApiDemos/bin/ApiDemos-debug.apk?raw=true"; Description="Android APK"},
            @{Name="test.ipa"; Url="https://github.com/appium/sample-code/blob/master/sample-code/apps/TestApp/TestApp.ipa?raw=true"; Description="iOS IPA"}
        )
    }

    # Documents (Common)
    docs = @{
        directory = "$baseDir\documents"
        files = @(
            @{Name="test.pdf"; Url="https://filesamples.com/samples/document/pdf/sample1.pdf"; Description="PDF sample"},
            @{Name="test.docx"; Url="https://filesamples.com/samples/document/docx/sample1.docx"; Description="DOCX sample"},
            @{Name="test.pptx"; Url="https://filesamples.com/samples/document/pptx/sample1.pptx"; Description="PPTX sample"},
            @{Name="test.xlsx"; Url="https://filesamples.com/samples/document/xlsx/sample1.xlsx"; Description="XLSX sample"},
            @{Name="test.odt"; Url="https://filesamples.com/samples/document/odt/sample1.odt"; Description="ODT sample"},
            @{Name="test.ods"; Url="https://filesamples.com/samples/document/ods/sample1.ods"; Description="ODS sample"}
        )
    }
}

Write-Host "Downloading sample files for all categories..."
Write-Host ""

foreach ($category in $samples.Keys) {
    $categoryData = $samples[$category]
    $dir = $categoryData.directory
    
    Write-Host "[$category]"
    
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    foreach ($file in $categoryData.files) {
        $targetPath = Join-Path $dir $file.Name
        
        # Helper to create x3 copies if needed for full coverage
        for ($i=1; $i -le 3; $i++) {
            $finalPath = if ($i -eq 1) { $targetPath } else { $targetPath.Replace("test.", "test_$i.") }
            
            if ((Test-Path $finalPath) -and -not $Force) {
                Write-Host "  SKIP: $(Split-Path $finalPath -Leaf) (already exists)"
                continue
            }
            
            # Download only once to temp, then copy
            if ($i -gt 1 -and (Test-Path $targetPath)) {
                Copy-Item $targetPath $finalPath
                continue
            }
            
            try {
                Write-Host "  Downloading: $(Split-Path $finalPath -Leaf)..."
                # Use standard User-Agent to avoid blocking
                Invoke-WebRequest -Uri $file.Url -OutFile $finalPath -TimeoutSec 30 -ErrorAction Stop -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                Write-Host "    OK: $($file.Description)"
            } catch {
                Write-Host "    ERROR: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# ============================================================================
# CREATE DUMMY FILES FOR HARD-TO-DOWNLOAD FORMATS
# Uses correct Magic Bytes where possible
# ============================================================================

Write-Host ""
Write-Host "Creating dummy files with specific Magic Bytes..."

function Create-DummyFile {
    param($Path, $HexBytes, $Size=1024)
    $bytes = [byte[]]::new($Size)
    $header = $HexBytes -split ' ' | ForEach-Object { [Convert]::ToByte($_, 16) }
    [Array]::Copy($header, $bytes, $header.Length)
    [System.IO.File]::WriteAllBytes($Path, $bytes)
    Write-Host "  Created: $(Split-Path $Path -Leaf)"
}

# Binary Formats
$binDir = "$baseDir\binary"
New-Item -ItemType Directory -Path $binDir -Force | Out-Null

# EXE (MZ header)
Create-DummyFile "$binDir\test.exe" "4D 5A 90 00 03 00 00 00"
Create-DummyFile "$binDir\test_2.exe" "4D 5A 90 00 03 00 00 00"
Create-DummyFile "$binDir\test_3.exe" "4D 5A 90 00 03 00 00 00"

# DLL (MZ header same as EXE)
Create-DummyFile "$binDir\test.dll" "4D 5A 90 00 03 00 00 00"
Create-DummyFile "$binDir\test_2.dll" "4D 5A 90 00 03 00 00 00"
Create-DummyFile "$binDir\test_3.dll" "4D 5A 90 00 03 00 00 00"

# ELF (Linux Binary: .ELF)
Create-DummyFile "$binDir\test.elf" "7F 45 4C 46"
Create-DummyFile "$binDir\test_2.elf" "7F 45 4C 46"
Create-DummyFile "$binDir\test_3.elf" "7F 45 4C 46"

# SYS (Often MZ or raw, use MZ for Windows drivers)
Create-DummyFile "$binDir\test.sys" "4D 5A 90 00"
Create-DummyFile "$binDir\test_2.sys" "4D 5A 90 00"
Create-DummyFile "$binDir\test_3.sys" "4D 5A 90 00"

# BIN (Generic, no strict magic, but often binary data)
Create-DummyFile "$binDir\test.bin" "00 01 02 03"
Create-DummyFile "$binDir\test_2.bin" "00 01 02 03"
Create-DummyFile "$binDir\test_3.bin" "00 01 02 03"

# Apps Categories (create dummies if downloads fail or for extras)
$appDir = "$baseDir\apps"
New-Item -ItemType Directory -Path $appDir -Force | Out-Null

# APK (PK zip header)
Create-DummyFile "$appDir\test_dummy.apk" "50 4B 03 04"
Create-DummyFile "$appDir\test_dummy_2.apk" "50 4B 03 04"
Create-DummyFile "$appDir\test_dummy_3.apk" "50 4B 03 04"

# XAPK (PK zip header)
Create-DummyFile "$appDir\test.xapk" "50 4B 03 04"
Create-DummyFile "$appDir\test_2.xapk" "50 4B 03 04"
Create-DummyFile "$appDir\test_3.xapk" "50 4B 03 04"

# IPA (PK zip header)
Create-DummyFile "$appDir\test_dummy.ipa" "50 4B 03 04"
Create-DummyFile "$appDir\test_dummy_2.ipa" "50 4B 03 04"

# Rar (Rar! header)
$archiveDir = "$baseDir\archive"
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
Create-DummyFile "$archiveDir\test.rar" "52 61 72 21 1A 07 00"
Create-DummyFile "$archiveDir\test_2.rar" "52 61 72 21 1A 07 00"
Create-DummyFile "$archiveDir\test_3.rar" "52 61 72 21 1A 07 00"

# 7z (7z header)
Create-DummyFile "$archiveDir\test.7z" "37 7A BC AF 27 1C"
Create-DummyFile "$archiveDir\test_2.7z" "37 7A BC AF 27 1C"
Create-DummyFile "$archiveDir\test_3.7z" "37 7A BC AF 27 1C"

# Tar (USTAR tar header at offset 257, but often starts cleanly. 
# Simple file write is enough for routing test if magic check is loose, 
# but for robust check let's assume extension routing or loose magic)
Create-DummyFile "$archiveDir\test.tar" "75 73 74 61 72" # ustar
Create-DummyFile "$archiveDir\test_2.tar" "75 73 74 61 72"
Create-DummyFile "$archiveDir\test_3.tar" "75 73 74 61 72"

# DMG (koly block or just generic binary for test)
Create-DummyFile "$archiveDir\test.dmg" "78 01 73 0D 62 62 60"
Create-DummyFile "$archiveDir\test_2.dmg" "78 01 73 0D 62 62 60"
Create-DummyFile "$archiveDir\test_3.dmg" "78 01 73 0D 62 62 60"

# ISO
Create-DummyFile "$archiveDir\test.iso" "43 44 30 30 31" # CD001 at offset (usually 0x8000, simplified here)

Write-Host "Dummy files created!"
exit

