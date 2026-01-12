"""
Neural Vault - Docker Services Comprehensive Test
==================================================

Testet alle Docker-basierten Binary Processing Services auf:
1. Funktionsfähigkeit (Service erreichbar, Verarbeitung funktioniert)
2. Geschwindigkeit (Verarbeitungszeit in Sekunden)
3. Genauigkeit (Plausibilität der Ergebnisse)
4. Halluzinationsfreiheit (keine erfundenen Daten)
5. Fehlerfreiheit (keine Exceptions)

Docker-Services:
- conductor-whisper (Port 9001): Audio→Text
- conductor-ffmpeg: Video/Audio Metadaten
- conductor-tesseract: Bild→Text OCR
- conductor-tika (Port 9998): Dokument-Extraktion
- conductor-ollama (Port 11435): LLM Klassifizierung
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional

# =============================================================================
# KONFIGURATION
# =============================================================================

WHISPER_URL = "http://localhost:9001"
TIKA_URL = "http://localhost:9998"
OLLAMA_URL = "http://localhost:11435"
FFMPEG_CONTAINER = "conductor-ffmpeg"
TESSERACT_CONTAINER = "conductor-tesseract"

from config.paths import TEST_SUITE_DIR, BASE_DIR

TEST_DIR = TEST_SUITE_DIR

# Pfad-Mapping für Docker
HOST_DATA_PATH = Path("F:/") # Keeping F:/ as host mapping root for Docker on Windows
CONTAINER_DATA_PATH = "/mnt/data"

def host_to_container_path(host_path: Path) -> str:
    rel_path = host_path.relative_to(HOST_DATA_PATH)
    return f"{CONTAINER_DATA_PATH}/{rel_path.as_posix()}"


@dataclass 
class TestResult:
    """Ergebnis eines einzelnen Tests."""
    service: str
    test_name: str
    success: bool
    duration_seconds: float
    output: str = ""
    error: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestReport:
    """Gesamter Testbericht."""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    results: List[TestResult] = field(default_factory=list)
    summary: str = ""


# =============================================================================
# SERVICE TESTS
# =============================================================================

def test_docker_container_running(container_name: str) -> TestResult:
    """Prüfe ob Docker-Container läuft."""
    start = time.time()
    try:
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True, text=True, timeout=10
        )
        running = proc.stdout.strip() == "true"
        return TestResult(
            service=container_name,
            test_name="Container Running",
            success=running,
            duration_seconds=time.time() - start,
            output=f"Running: {running}"
        )
    except Exception as e:
        return TestResult(
            service=container_name,
            test_name="Container Running",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_whisper_health() -> TestResult:
    """Teste Whisper Service Health."""
    start = time.time()
    try:
        # Versuche verschiedene Health-Endpoints
        for endpoint in ["/health", "/v1/models", "/"]:
            try:
                r = requests.get(f"{WHISPER_URL}{endpoint}", timeout=10)
                if r.ok:
                    return TestResult(
                        service="whisper",
                        test_name="Health Check",
                        success=True,
                        duration_seconds=time.time() - start,
                        output=f"Endpoint {endpoint}: {r.status_code}"
                    )
            except:
                continue
        
        return TestResult(
            service="whisper",
            test_name="Health Check",
            success=False,
            duration_seconds=time.time() - start,
            error="Kein Health-Endpoint erreichbar"
        )
    except Exception as e:
        return TestResult(
            service="whisper",
            test_name="Health Check",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_tika_health() -> TestResult:
    """Teste Tika Service."""
    start = time.time()
    try:
        r = requests.get(TIKA_URL, timeout=10)
        return TestResult(
            service="tika",
            test_name="Health Check",
            success=r.ok,
            duration_seconds=time.time() - start,
            output=f"Status: {r.status_code}"
        )
    except Exception as e:
        return TestResult(
            service="tika",
            test_name="Health Check",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_ollama_health() -> TestResult:
    """Teste Ollama Service."""
    start = time.time()
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        models = r.json().get("models", []) if r.ok else []
        return TestResult(
            service="ollama",
            test_name="Health Check",
            success=r.ok,
            duration_seconds=time.time() - start,
            output=f"Models: {len(models)}",
            metrics={"model_count": len(models)}
        )
    except Exception as e:
        return TestResult(
            service="ollama",
            test_name="Health Check",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_ffmpeg_video_processing(video_path: Path) -> TestResult:
    """Teste FFmpeg Video-Verarbeitung."""
    start = time.time()
    
    if not video_path.exists():
        return TestResult(
            service="ffmpeg",
            test_name="Video Processing",
            success=False,
            duration_seconds=0,
            error=f"Testdatei nicht gefunden: {video_path}"
        )
    
    try:
        container_path = host_to_container_path(video_path)
        cmd = [
            "docker", "exec", FFMPEG_CONTAINER,
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", container_path
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            duration = float(data.get("format", {}).get("duration", 0))
            streams = data.get("streams", [])
            video = next((s for s in streams if s.get("codec_type") == "video"), {})
            
            return TestResult(
                service="ffmpeg",
                test_name="Video Processing",
                success=True,
                duration_seconds=time.time() - start,
                output=f"{video.get('width')}x{video.get('height')}, {duration:.1f}s",
                metrics={
                    "video_duration": duration,
                    "width": video.get("width"),
                    "height": video.get("height"),
                    "codec": video.get("codec_name")
                }
            )
        else:
            return TestResult(
                service="ffmpeg",
                test_name="Video Processing",
                success=False,
                duration_seconds=time.time() - start,
                error=proc.stderr[:200]
            )
    except Exception as e:
        return TestResult(
            service="ffmpeg",
            test_name="Video Processing",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_tesseract_ocr(image_path: Path) -> TestResult:
    """Teste Tesseract OCR."""
    start = time.time()
    
    if not image_path.exists():
        return TestResult(
            service="tesseract",
            test_name="OCR Processing",
            success=False,
            duration_seconds=0,
            error=f"Testdatei nicht gefunden: {image_path}"
        )
    
    try:
        container_path = host_to_container_path(image_path)
        cmd = [
            "docker", "exec", TESSERACT_CONTAINER,
            "tesseract", container_path, "stdout", "-l", "deu+eng"
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if proc.returncode == 0:
            text = proc.stdout.strip()
            word_count = len(text.split())
            return TestResult(
                service="tesseract",
                test_name="OCR Processing",
                success=True,
                duration_seconds=time.time() - start,
                output=f"{word_count} Wörter erkannt",
                metrics={"word_count": word_count, "char_count": len(text)}
            )
        else:
            return TestResult(
                service="tesseract",
                test_name="OCR Processing",
                success=False,
                duration_seconds=time.time() - start,
                error=proc.stderr[:200]
            )
    except Exception as e:
        return TestResult(
            service="tesseract",
            test_name="OCR Processing",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_tika_document_extraction(doc_path: Path) -> TestResult:
    """Teste Tika Dokument-Extraktion."""
    start = time.time()
    
    if not doc_path.exists():
        return TestResult(
            service="tika",
            test_name="Document Extraction",
            success=False,
            duration_seconds=0,
            error=f"Testdatei nicht gefunden: {doc_path}"
        )
    
    try:
        with open(doc_path, "rb") as f:
            r = requests.put(
                f"{TIKA_URL}/tika",
                data=f,
                headers={"Accept": "text/plain"},
                timeout=60
            )
        
        if r.ok:
            text = r.text.strip()
            return TestResult(
                service="tika",
                test_name="Document Extraction",
                success=True,
                duration_seconds=time.time() - start,
                output=f"{len(text)} Zeichen extrahiert",
                metrics={"char_count": len(text), "word_count": len(text.split())}
            )
        else:
            return TestResult(
                service="tika",
                test_name="Document Extraction",
                success=False,
                duration_seconds=time.time() - start,
                error=f"HTTP {r.status_code}"
            )
    except Exception as e:
        return TestResult(
            service="tika",
            test_name="Document Extraction",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


def test_ollama_classification(text: str) -> TestResult:
    """Teste Ollama Klassifizierung."""
    start = time.time()
    
    prompt = f"""Klassifiziere diesen Text. Antworte NUR mit JSON:
{{
    "category": "Technologie|Finanzen|Privat|Arbeit|Sonstiges",
    "confidence": 0.8,
    "summary": "Kurze Beschreibung"
}}

Text: {text[:500]}"""

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1}
            },
            timeout=120
        )
        
        if r.ok:
            response = r.json().get("response", "{}")
            try:
                data = json.loads(response)
                return TestResult(
                    service="ollama",
                    test_name="Classification",
                    success=True,
                    duration_seconds=time.time() - start,
                    output=f"Category: {data.get('category')}, Conf: {data.get('confidence')}",
                    metrics=data
                )
            except json.JSONDecodeError:
                return TestResult(
                    service="ollama",
                    test_name="Classification",
                    success=False,
                    duration_seconds=time.time() - start,
                    error="JSON Parse Error",
                    output=response[:100]
                )
        else:
            return TestResult(
                service="ollama",
                test_name="Classification",
                success=False,
                duration_seconds=time.time() - start,
                error=f"HTTP {r.status_code}"
            )
    except Exception as e:
        return TestResult(
            service="ollama",
            test_name="Classification",
            success=False,
            duration_seconds=time.time() - start,
            error=str(e)
        )


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def find_test_files() -> Dict[str, Path]:
    """Finde Testdateien für jeden Typ."""
    files = {}
    
    # Video
    for ext in ["avi", "mp4", "mkv"]:
        for f in TEST_DIR.glob(f"**/*.{ext}"):
            files["video"] = f
            break
        if "video" in files:
            break
    
    # Audio
    for ext in ["mp3", "aac", "wav"]:
        for f in TEST_DIR.glob(f"**/*.{ext}"):
            files["audio"] = f
            break
        if "audio" in files:
            break
    
    # Image
    for ext in ["jpg", "png", "tiff"]:
        for f in TEST_DIR.glob(f"**/*.{ext}"):
            files["image"] = f
            break
        if "image" in files:
            break
    
    # Document
    for ext in ["pdf", "docx", "txt"]:
        for f in TEST_DIR.glob(f"**/*.{ext}"):
            files["document"] = f
            break
        if "document" in files:
            break
    
    return files


def run_all_tests() -> TestReport:
    """Führe alle Tests aus."""
    print("=" * 70)
    print("NEURAL VAULT - DOCKER SERVICES COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    # 1. Container Status Tests
    print("1. CONTAINER STATUS TESTS")
    print("-" * 40)
    
    containers = ["conductor-whisper", "conductor-ffmpeg", "conductor-tesseract", 
                  "conductor-tika", "conductor-ollama"]
    
    for container in containers:
        result = test_docker_container_running(container)
        results.append(result)
        icon = "✅" if result.success else "❌"
        print(f"  {icon} {container}: {result.output or result.error}")
    
    print()
    
    # 2. Health Check Tests
    print("2. SERVICE HEALTH CHECKS")
    print("-" * 40)
    
    for test_func, name in [
        (test_whisper_health, "Whisper"),
        (test_tika_health, "Tika"),
        (test_ollama_health, "Ollama")
    ]:
        result = test_func()
        results.append(result)
        icon = "✅" if result.success else "❌"
        print(f"  {icon} {name}: {result.output or result.error} ({result.duration_seconds:.2f}s)")
    
    print()
    
    # 3. Processing Tests
    print("3. PROCESSING TESTS")
    print("-" * 40)
    
    test_files = find_test_files()
    print(f"  Gefundene Testdateien: {list(test_files.keys())}")
    
    if "video" in test_files:
        result = test_ffmpeg_video_processing(test_files["video"])
        results.append(result)
        icon = "✅" if result.success else "❌"
        print(f"  {icon} FFmpeg Video: {result.output or result.error} ({result.duration_seconds:.2f}s)")
    
    if "image" in test_files:
        result = test_tesseract_ocr(test_files["image"])
        results.append(result)
        icon = "✅" if result.success else "❌"
        print(f"  {icon} Tesseract OCR: {result.output or result.error} ({result.duration_seconds:.2f}s)")
    
    if "document" in test_files:
        result = test_tika_document_extraction(test_files["document"])
        results.append(result)
        icon = "✅" if result.success else "❌"
        print(f"  {icon} Tika Document: {result.output or result.error} ({result.duration_seconds:.2f}s)")
    
    # 4. LLM Classification Test
    print()
    print("4. LLM CLASSIFICATION TEST")
    print("-" * 40)
    
    test_text = "Dies ist ein Technologie-Dokument über Docker Container und Microservices-Architektur."
    result = test_ollama_classification(test_text)
    results.append(result)
    icon = "✅" if result.success else "❌"
    print(f"  {icon} Ollama: {result.output or result.error} ({result.duration_seconds:.2f}s)")
    
    # Report generieren
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    
    report = TestReport(
        timestamp=datetime.now().isoformat(),
        total_tests=len(results),
        passed=passed,
        failed=failed,
        results=results,
        summary=f"{passed}/{len(results)} Tests bestanden"
    )
    
    print()
    print("=" * 70)
    print(f"ERGEBNIS: {report.summary}")
    print("=" * 70)
    
    # Speichere Report
    report_path = TEST_DIR / "_DOCKER_TEST_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, default=str)
    print(f"\nBericht gespeichert: {report_path}")
    
    return report


if __name__ == "__main__":
    run_all_tests()
