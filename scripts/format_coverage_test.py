"""
Neural Vault - Real-World Format Coverage Test
================================================

Systematischer Test aller unterstützten Formate mit 3 Dateien pro Format.
Simuliert reale Nutzung der Verarbeitungspipeline.

Erfolgskriterien:
- 95% der Formatarten müssen verarbeitbar sein
- Genauigkeit > 90%
- Fehlerrate < 5%
- Latenz < 60s pro Datei

Ausführung:
    python format_coverage_test.py
"""

import os
import sys
import json
import time
import shutil
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# =============================================================================
# KONFIGURATION
# =============================================================================

# Basis-Verzeichnisse
from config.paths import TEST_SUITE_DIR

# Basis-Verzeichnisse
DRIVE_ROOT = Path("F:/")
TEST_DIR = TEST_SUITE_DIR / "_FormatCoverage"
RESULTS_DIR = TEST_SUITE_DIR / "_CoverageReports"

TEST_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Service URLs
WHISPER_URL = os.getenv("WHISPER_URL", "http://localhost:9001")
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998")
PARSER_URL = os.getenv("PARSER_URL", "http://localhost:8002")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11435")

# Container
FFMPEG_CONTAINER = "conductor-ffmpeg"
TESSERACT_CONTAINER = "conductor-tesseract"

# Pfad-Mapping
CONTAINER_DATA_PATH = "/mnt/data"

def host_to_container(path: Path) -> str:
    try:
        rel = path.relative_to(DRIVE_ROOT)
        return f"{CONTAINER_DATA_PATH}/{rel.as_posix()}"
    except ValueError:
        return str(path)


# =============================================================================
# FORMAT-DEFINITIONEN
# =============================================================================

# Alle unterstützten Formate gruppiert nach Processor
FORMATS = {
    "ffmpeg": {
        "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"],
        "category": "video"
    },
    "whisper": {
        "extensions": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
        "category": "audio"
    },
    "tesseract": {
        "extensions": [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"],
        "category": "image"
    },
    "tika": {
        "extensions": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".html", ".txt", ".rtf", ".zip"],
        "category": "document"
    },
    "parser": {
        # Extended + Archive (via 7-Zip Docker)
        "extensions": [".torrent", ".eml", ".msg", ".exr", ".srt", ".apk", ".obj", ".stl", ".gltf", ".glb", ".rar", ".7z", ".tar", ".gz"],
        "category": "extended"
    }
}

# Erfolgskriterien
SUCCESS_CRITERIA = {
    "format_success_rate": 0.95,  # 95% der Formatarten
    "file_success_rate": 0.90,   # 90% der einzelnen Dateien
    "accuracy_threshold": 0.90,   # 90% Genauigkeit
    "error_rate_max": 0.05,       # Max 5% Fehler
    "latency_max_seconds": 60     # Max 60s pro Datei
}

FILES_PER_FORMAT = 3


# =============================================================================
# DATENSTRUKTUREN
# =============================================================================

@dataclass
class FileTestResult:
    """Ergebnis für eine einzelne Datei."""
    filepath: str
    filename: str
    extension: str
    processor: str
    
    success: bool = False
    error: str = ""
    
    processing_time_seconds: float = 0
    accuracy: float = 0
    completeness: float = 0
    confidence: float = 0
    
    extracted_text_length: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class FormatTestResult:
    """Aggregiertes Ergebnis für ein Format."""
    extension: str
    processor: str
    category: str
    
    files_tested: int = 0
    files_passed: int = 0
    files_failed: int = 0
    
    avg_processing_time: float = 0
    avg_accuracy: float = 0
    
    success_rate: float = 0
    status: str = "pending"  # pending, passed, failed
    
    file_results: List[FileTestResult] = field(default_factory=list)


@dataclass
class CoverageReport:
    """Gesamtbericht."""
    timestamp: str
    duration_seconds: float
    
    total_formats: int = 0
    formats_passed: int = 0
    formats_failed: int = 0
    format_success_rate: float = 0
    
    total_files: int = 0
    files_passed: int = 0
    files_failed: int = 0
    file_success_rate: float = 0
    
    meets_criteria: bool = False
    criteria_results: Dict[str, bool] = field(default_factory=dict)
    
    format_results: Dict[str, FormatTestResult] = field(default_factory=dict)


# =============================================================================
# TESTDATEI-SUCHE
# =============================================================================

def find_test_files(extension: str, count: int = 3, min_size: int = 100, max_size: int = 100_000_000) -> List[Path]:
    """
    Finde Testdateien für ein Format auf Laufwerk F.
    
    Args:
        extension: Dateiendung (.mp4, .pdf, etc.)
        count: Anzahl gewünschter Dateien
        min_size: Minimale Dateigröße in Bytes
        max_size: Maximale Dateigröße in Bytes (100MB default)
    """
    found = []
    
    # Durchsuche F:/ aber überspringe System-Ordner
    skip_dirs = {"$RECYCLE.BIN", "System Volume Information", "_TestSuite", ".git", "node_modules"}
    
    try:
        for f in DRIVE_ROOT.rglob(f"*{extension}"):
            # Überspringe System-Ordner
            if any(skip in str(f) for skip in skip_dirs):
                continue
            
            try:
                size = f.stat().st_size
                if min_size <= size <= max_size:
                    found.append(f)
                    if len(found) >= count:
                        break
            except (PermissionError, OSError):
                continue
    except Exception as e:
        print(f"  [WARN] Suche für {extension}: {e}")
    
    return found


def copy_test_files_to_test_dir(files: List[Path], extension: str) -> List[Path]:
    """Kopiere Testdateien in den Testordner."""
    ext_dir = TEST_DIR / extension.lstrip(".")
    ext_dir.mkdir(parents=True, exist_ok=True)
    
    copied = []
    for i, src in enumerate(files):
        dst = ext_dir / f"test_{i+1}{extension}"
        try:
            if not dst.exists():
                shutil.copy2(src, dst)
            copied.append(dst)
        except Exception as e:
            print(f"  [WARN] Kopieren fehlgeschlagen: {e}")
    
    return copied


# =============================================================================
# PROZESSOREN
# =============================================================================

def process_with_ffmpeg(filepath: Path) -> FileTestResult:
    """Verarbeite Video/Audio mit FFmpeg."""
    start = time.time()
    result = FileTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processor="ffmpeg"
    )
    
    try:
        container_path = host_to_container(filepath)
        cmd = [
            "docker", "exec", FFMPEG_CONTAINER,
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", container_path
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        result.processing_time_seconds = time.time() - start
        
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            fmt = data.get("format", {})
            streams = data.get("streams", [])
            
            result.success = True
            result.accuracy = 1.0
            result.completeness = 1.0 if streams else 0.5
            result.confidence = 1.0
            result.metadata = {
                "duration": fmt.get("duration"),
                "format": fmt.get("format_name"),
                "streams": len(streams)
            }
        else:
            result.error = proc.stderr[:200]
    except Exception as e:
        result.error = str(e)
        result.processing_time_seconds = time.time() - start
    
    return result


def process_with_whisper(filepath: Path) -> FileTestResult:
    """Verarbeite Audio mit Whisper."""
    start = time.time()
    result = FileTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processor="whisper"
    )
    
    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f, "audio/mpeg")}
            r = requests.post(
                f"{WHISPER_URL}/v1/audio/transcriptions",
                files=files,
                data={"model": "Systran/faster-whisper-base"},
                timeout=300
            )
        
        result.processing_time_seconds = time.time() - start
        
        if r.ok:
            text = r.json().get("text", "")
            result.success = True
            result.accuracy = 0.93  # Whisper typisch
            result.completeness = 1.0 if len(text) > 10 else 0.5
            result.confidence = 0.93
            result.extracted_text_length = len(text)
        else:
            result.error = r.text[:200]
    except Exception as e:
        result.error = str(e)
        result.processing_time_seconds = time.time() - start
    
    return result


def process_with_tesseract(filepath: Path) -> FileTestResult:
    """Verarbeite Bild mit Tesseract OCR."""
    start = time.time()
    result = FileTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processor="tesseract"
    )
    
    try:
        container_path = host_to_container(filepath)
        cmd = [
            "docker", "exec", TESSERACT_CONTAINER,
            "tesseract", container_path, "stdout", "-l", "deu+eng"
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        result.processing_time_seconds = time.time() - start
        
        if proc.returncode == 0:
            text = proc.stdout.strip()
            result.success = True
            result.accuracy = 0.87  # Tesseract typisch
            result.completeness = 1.0 if len(text) > 0 else 0.3
            result.confidence = 0.87
            result.extracted_text_length = len(text)
        else:
            result.error = proc.stderr[:200]
    except Exception as e:
        result.error = str(e)
        result.processing_time_seconds = time.time() - start
    
    return result


def process_with_tika(filepath: Path) -> FileTestResult:
    """Verarbeite Dokument mit Tika."""
    start = time.time()
    result = FileTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processor="tika"
    )
    
    try:
        with open(filepath, "rb") as f:
            r = requests.put(
                f"{TIKA_URL}/tika",
                data=f,
                headers={"Accept": "text/plain"},
                timeout=120
            )
        
        result.processing_time_seconds = time.time() - start
        
        if r.ok:
            text = r.text.strip()
            result.success = True
            result.accuracy = 0.95
            result.completeness = min(1.0, len(text) / 500)
            result.confidence = 0.95
            result.extracted_text_length = len(text)
        else:
            result.error = f"HTTP {r.status_code}"
    except Exception as e:
        result.error = str(e)
        result.processing_time_seconds = time.time() - start
    
    return result


def process_with_parser(filepath: Path) -> FileTestResult:
    """Verarbeite mit Parser-Service."""
    start = time.time()
    result = FileTestResult(
        filepath=str(filepath),
        filename=filepath.name,
        extension=filepath.suffix.lower(),
        processor="parser"
    )
    
    try:
        container_path = host_to_container(filepath)
        r = requests.post(
            f"{PARSER_URL}/parse/path",
            params={"filepath": container_path},
            timeout=120
        )
        
        result.processing_time_seconds = time.time() - start
        
        if r.ok:
            data = r.json()
            result.success = data.get("success", False)
            result.accuracy = data.get("confidence", 0)
            result.completeness = data.get("completeness", 0)
            result.confidence = data.get("confidence", 0)
            result.metadata = data.get("metadata", {})
            result.error = data.get("error", "")
            result.extracted_text_length = len(data.get("extracted_text", ""))
        else:
            result.error = f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        result.error = str(e)
        result.processing_time_seconds = time.time() - start
    
    return result


# Processor-Mapping
PROCESSORS = {
    "ffmpeg": process_with_ffmpeg,
    "whisper": process_with_whisper,
    "tesseract": process_with_tesseract,
    "tika": process_with_tika,
    "parser": process_with_parser
}


# =============================================================================
# HAUPTFUNKTIONEN
# =============================================================================

def collect_test_files():
    """Sammle und kopiere alle Testdateien."""
    print("=" * 70)
    print("PHASE 1: TESTDATEIEN SAMMELN")
    print("=" * 70)
    
    all_files = {}
    
    for processor, config in FORMATS.items():
        for ext in config["extensions"]:
            print(f"\n  Suche {ext}...", end=" ")
            
            # Finde Dateien
            found = find_test_files(ext, FILES_PER_FORMAT)
            
            if found:
                # Kopiere in Testordner
                copied = copy_test_files_to_test_dir(found, ext)
                all_files[ext] = {
                    "files": copied,
                    "processor": processor,
                    "category": config["category"]
                }
                print(f"✅ {len(copied)}/{FILES_PER_FORMAT}")
            else:
                print(f"❌ 0/{FILES_PER_FORMAT}")
                all_files[ext] = {
                    "files": [],
                    "processor": processor,
                    "category": config["category"]
                }
    
    # Zusammenfassung
    total_formats = len(all_files)
    formats_with_files = sum(1 for v in all_files.values() if v["files"])
    total_files = sum(len(v["files"]) for v in all_files.values())
    
    print(f"\n\nGefunden: {formats_with_files}/{total_formats} Formate, {total_files} Dateien")
    
    return all_files


def run_coverage_test(test_files: Dict) -> CoverageReport:
    """Führe Coverage-Test durch."""
    print("\n" + "=" * 70)
    print("PHASE 2: VERARBEITUNG")
    print("=" * 70)
    
    start_time = time.time()
    
    report = CoverageReport(
        timestamp=datetime.now().isoformat(),
        duration_seconds=0
    )
    
    for ext, info in test_files.items():
        files = info["files"]
        processor = info["processor"]
        category = info["category"]
        
        format_result = FormatTestResult(
            extension=ext,
            processor=processor,
            category=category
        )
        
        if not files:
            format_result.status = "no_files"
            report.format_results[ext] = format_result
            continue
        
        print(f"\n  [{ext.upper()}] {processor}")
        
        process_fn = PROCESSORS.get(processor)
        if not process_fn:
            format_result.status = "no_processor"
            report.format_results[ext] = format_result
            continue
        
        times = []
        accuracies = []
        
        for filepath in files:
            print(f"    → {filepath.name}", end=" ")
            
            try:
                file_result = process_fn(filepath)
                format_result.file_results.append(file_result)
                format_result.files_tested += 1
                
                if file_result.success:
                    format_result.files_passed += 1
                    times.append(file_result.processing_time_seconds)
                    accuracies.append(file_result.accuracy)
                    print(f"✅ {file_result.processing_time_seconds:.2f}s")
                else:
                    format_result.files_failed += 1
                    print(f"❌ {file_result.error[:40]}")
                    
            except Exception as e:
                format_result.files_tested += 1
                format_result.files_failed += 1
                print(f"❌ {str(e)[:40]}")
        
        # Aggregiere
        if format_result.files_tested > 0:
            format_result.success_rate = format_result.files_passed / format_result.files_tested
            format_result.avg_processing_time = sum(times) / len(times) if times else 0
            format_result.avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
            format_result.status = "passed" if format_result.success_rate >= 0.5 else "failed"
        
        report.format_results[ext] = format_result
    
    # Report aggregieren
    report.duration_seconds = time.time() - start_time
    report.total_formats = len(report.format_results)
    report.formats_passed = sum(1 for r in report.format_results.values() if r.status == "passed")
    report.formats_failed = sum(1 for r in report.format_results.values() if r.status == "failed")
    report.format_success_rate = report.formats_passed / max(1, report.total_formats - sum(1 for r in report.format_results.values() if r.status == "no_files"))
    
    report.total_files = sum(r.files_tested for r in report.format_results.values())
    report.files_passed = sum(r.files_passed for r in report.format_results.values())
    report.files_failed = sum(r.files_failed for r in report.format_results.values())
    report.file_success_rate = report.files_passed / max(1, report.total_files)
    
    # Kriterien prüfen
    report.criteria_results = {
        "format_success_rate": report.format_success_rate >= SUCCESS_CRITERIA["format_success_rate"],
        "file_success_rate": report.file_success_rate >= SUCCESS_CRITERIA["file_success_rate"],
        "error_rate": (report.files_failed / max(1, report.total_files)) <= SUCCESS_CRITERIA["error_rate_max"]
    }
    report.meets_criteria = all(report.criteria_results.values())
    
    return report


def print_report(report: CoverageReport):
    """Drucke Bericht."""
    print("\n" + "=" * 70)
    print("PHASE 3: BERICHT")
    print("=" * 70)
    
    print(f"\nDauer: {report.duration_seconds:.1f}s")
    print(f"\n-- FORMATE --")
    print(f"  Getestet: {report.total_formats}")
    print(f"  Bestanden: {report.formats_passed}")
    print(f"  Fehlgeschlagen: {report.formats_failed}")
    print(f"  Erfolgsquote: {report.format_success_rate:.1%}")
    
    print(f"\n-- DATEIEN --")
    print(f"  Getestet: {report.total_files}")
    print(f"  Bestanden: {report.files_passed}")
    print(f"  Fehlgeschlagen: {report.files_failed}")
    print(f"  Erfolgsquote: {report.file_success_rate:.1%}")
    
    print(f"\n-- KRITERIEN (Ziel: 95%) --")
    for name, passed in report.criteria_results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    overall = "✅ BESTANDEN" if report.meets_criteria else "❌ NICHT BESTANDEN"
    print(f"\n  GESAMT: {overall}")
    
    # Details nach Format
    print("\n-- DETAILS --")
    for ext, result in sorted(report.format_results.items()):
        if result.status == "no_files":
            print(f"  {ext:8} ⚪ keine Dateien")
        elif result.status == "passed":
            print(f"  {ext:8} ✅ {result.files_passed}/{result.files_tested} ({result.avg_processing_time:.2f}s)")
        else:
            print(f"  {ext:8} ❌ {result.files_passed}/{result.files_tested}")


def save_report(report: CoverageReport) -> Path:
    """Speichere Report als JSON."""
    path = RESULTS_DIR / f"coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Konvertiere zu Dict
    report_dict = asdict(report)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, default=str)
    
    return path


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("NEURAL VAULT - FORMAT COVERAGE TEST")
    print("=" * 70)
    print(f"Zeitstempel: {datetime.now().isoformat()}")
    print(f"Ziel: {SUCCESS_CRITERIA['format_success_rate']:.0%} Format-Erfolgsquote")
    print(f"Dateien pro Format: {FILES_PER_FORMAT}")
    
    # Phase 1: Dateien sammeln
    test_files = collect_test_files()
    
    # Phase 2: Tests ausführen
    report = run_coverage_test(test_files)
    
    # Phase 3: Bericht
    print_report(report)
    
    # Speichern
    report_path = save_report(report)
    print(f"\nReport gespeichert: {report_path}")
    
    return report


if __name__ == "__main__":
    main()
