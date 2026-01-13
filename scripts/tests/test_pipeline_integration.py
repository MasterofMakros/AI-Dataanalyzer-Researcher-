"""
Neural Vault Pipeline Integration Tests
=======================================

Tests the full document processing pipeline end-to-end.

Usage:
    python scripts/tests/test_pipeline_integration.py
    python scripts/tests/test_pipeline_integration.py --verbose
    python scripts/tests/test_pipeline_integration.py --service document-processor

Requirements:
    - Docker services running (use scripts/start_pipeline.sh)
    - Test files in F:/_TestPool or specify --test-dir
"""

import os
import sys
import io
import json
import time
import argparse
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Fix Windows Unicode output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import httpx
    HTTP_CLIENT = httpx
except ImportError:
    import urllib.request
    import urllib.error
    HTTP_CLIENT = None


# =============================================================================
# CONFIGURATION
# =============================================================================

class ServiceConfig:
    """Service endpoints configuration."""
    DOCUMENT_PROCESSOR = os.getenv("DOCUMENT_PROCESSOR_URL", "http://localhost:8005")
    UNIVERSAL_ROUTER = os.getenv("UNIVERSAL_ROUTER_URL", "http://localhost:8030")
    ORCHESTRATOR = os.getenv("ORCHESTRATOR_URL", "http://localhost:8020")
    WHISPERX = os.getenv("WHISPERX_URL", "http://localhost:9000")
    TIKA = os.getenv("TIKA_URL", "http://localhost:9998")
    API = os.getenv("API_URL", "http://localhost:8000")


# =============================================================================
# TEST RESULT TYPES
# =============================================================================

class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str = ""
    duration_ms: float = 0
    details: Optional[Dict[str, Any]] = None


# =============================================================================
# HTTP HELPERS
# =============================================================================

def http_get(url: str, timeout: int = 10) -> tuple:
    """GET request returning (status_code, response_text)."""
    if HTTP_CLIENT:
        try:
            response = HTTP_CLIENT.get(url, timeout=timeout)
            return response.status_code, response.text
        except Exception as e:
            return 0, str(e)
    else:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, str(e)
        except Exception as e:
            return 0, str(e)


def http_post_file(url: str, filepath: Path, params: Dict = None, timeout: int = 60) -> tuple:
    """POST file upload returning (status_code, response_json)."""
    if not HTTP_CLIENT:
        return 0, {"error": "httpx not installed"}

    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f)}
            response = HTTP_CLIENT.post(url, files=files, params=params, timeout=timeout)
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {"text": response.text}
    except Exception as e:
        return 0, {"error": str(e)}


# =============================================================================
# SERVICE HEALTH CHECKS
# =============================================================================

def check_service_health(name: str, url: str) -> TestResult:
    """Check if a service is healthy."""
    start = time.time()
    health_url = f"{url}/health" if not url.endswith("/health") else url

    status_code, response = http_get(health_url, timeout=5)
    duration = (time.time() - start) * 1000

    if status_code == 200:
        return TestResult(
            name=f"Health: {name}",
            status=TestStatus.PASS,
            message="Service healthy",
            duration_ms=duration
        )
    elif status_code == 0:
        return TestResult(
            name=f"Health: {name}",
            status=TestStatus.ERROR,
            message=f"Connection failed: {response}",
            duration_ms=duration
        )
    else:
        return TestResult(
            name=f"Health: {name}",
            status=TestStatus.FAIL,
            message=f"HTTP {status_code}",
            duration_ms=duration
        )


# =============================================================================
# DOCUMENT PROCESSOR TESTS
# =============================================================================

def test_document_processor_pdf(test_dir: Path) -> TestResult:
    """Test PDF processing with Docling."""
    start = time.time()

    # Find a PDF file
    pdf_files = list(test_dir.glob("**/*.pdf"))
    if not pdf_files:
        return TestResult(
            name="Document Processor: PDF",
            status=TestStatus.SKIP,
            message="No PDF files found in test directory"
        )

    pdf_file = pdf_files[0]
    url = f"{ServiceConfig.DOCUMENT_PROCESSOR}/process/document"

    status_code, response = http_post_file(url, pdf_file, params={"processor": "auto"})
    duration = (time.time() - start) * 1000

    if status_code == 200:
        text = response.get("text", "")
        processor = response.get("processor", "unknown")
        confidence = response.get("confidence", 0)

        return TestResult(
            name="Document Processor: PDF",
            status=TestStatus.PASS,
            message=f"Extracted {len(text)} chars via {processor} (conf: {confidence:.2f})",
            duration_ms=duration,
            details={"file": pdf_file.name, "chars": len(text), "processor": processor}
        )
    else:
        return TestResult(
            name="Document Processor: PDF",
            status=TestStatus.FAIL,
            message=f"HTTP {status_code}: {response}",
            duration_ms=duration
        )


def test_document_processor_ocr(test_dir: Path) -> TestResult:
    """Test OCR with Surya."""
    start = time.time()

    # Find an image file
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.tiff"]:
        image_files.extend(test_dir.glob(f"**/{ext}"))

    if not image_files:
        return TestResult(
            name="Document Processor: OCR",
            status=TestStatus.SKIP,
            message="No image files found in test directory"
        )

    image_file = image_files[0]
    url = f"{ServiceConfig.DOCUMENT_PROCESSOR}/process/ocr"

    status_code, response = http_post_file(url, image_file, params={"langs": "de,en"})
    duration = (time.time() - start) * 1000

    if status_code == 200:
        text = response.get("text", "")
        confidence = response.get("confidence", 0)
        lines = response.get("lines", [])

        return TestResult(
            name="Document Processor: OCR",
            status=TestStatus.PASS,
            message=f"Extracted {len(lines)} lines, {len(text)} chars (conf: {confidence:.2f})",
            duration_ms=duration,
            details={"file": image_file.name, "lines": len(lines), "chars": len(text)}
        )
    else:
        return TestResult(
            name="Document Processor: OCR",
            status=TestStatus.FAIL,
            message=f"HTTP {status_code}: {response}",
            duration_ms=duration
        )


def test_document_processor_pii() -> TestResult:
    """Test PII detection with GLiNER."""
    start = time.time()

    url = f"{ServiceConfig.DOCUMENT_PROCESSOR}/process/pii"
    test_text = "Max Mustermann, geboren am 15.03.1985, IBAN: DE89370400440532013000, Tel: +49 170 1234567"

    if not HTTP_CLIENT:
        return TestResult(
            name="Document Processor: PII",
            status=TestStatus.SKIP,
            message="httpx not installed"
        )

    try:
        response = HTTP_CLIENT.post(
            url,
            json={
                "text": test_text,
                "labels": ["person", "iban", "date", "phone_number"]
            },
            timeout=30
        )
        duration = (time.time() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            entities = data.get("entities", [])
            masked = data.get("masked_text", "")

            return TestResult(
                name="Document Processor: PII",
                status=TestStatus.PASS,
                message=f"Found {len(entities)} PII entities",
                duration_ms=duration,
                details={"entities": [e.get("label") for e in entities]}
            )
        else:
            return TestResult(
                name="Document Processor: PII",
                status=TestStatus.FAIL,
                message=f"HTTP {response.status_code}",
                duration_ms=duration
            )
    except Exception as e:
        return TestResult(
            name="Document Processor: PII",
            status=TestStatus.ERROR,
            message=str(e),
            duration_ms=(time.time() - start) * 1000
        )


def test_document_processor_embedding() -> TestResult:
    """Test embedding generation."""
    start = time.time()

    url = f"{ServiceConfig.DOCUMENT_PROCESSOR}/vector/embed"

    if not HTTP_CLIENT:
        return TestResult(
            name="Document Processor: Embedding",
            status=TestStatus.SKIP,
            message="httpx not installed"
        )

    try:
        response = HTTP_CLIENT.post(
            url,
            json={
                "id": "test-001",
                "text": "Dies ist ein Testdokument fuer die Embedding-Generierung."
            },
            timeout=30
        )
        duration = (time.time() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            vector = data.get("vector", [])
            dim = data.get("dim", 0)

            return TestResult(
                name="Document Processor: Embedding",
                status=TestStatus.PASS,
                message=f"Generated {dim}-dimensional vector",
                duration_ms=duration
            )
        else:
            return TestResult(
                name="Document Processor: Embedding",
                status=TestStatus.FAIL,
                message=f"HTTP {response.status_code}",
                duration_ms=duration
            )
    except Exception as e:
        return TestResult(
            name="Document Processor: Embedding",
            status=TestStatus.ERROR,
            message=str(e),
            duration_ms=(time.time() - start) * 1000
        )


# =============================================================================
# UNIVERSAL ROUTER TESTS
# =============================================================================

def test_universal_router_detect(test_dir: Path) -> TestResult:
    """Test file type detection."""
    start = time.time()

    # Find any file
    all_files = list(test_dir.glob("**/*"))
    test_files = [f for f in all_files if f.is_file() and f.suffix.lower() in [".pdf", ".jpg", ".png", ".docx"]]

    if not test_files:
        return TestResult(
            name="Universal Router: Detect",
            status=TestStatus.SKIP,
            message="No suitable test files found"
        )

    test_file = test_files[0]
    url = f"{ServiceConfig.UNIVERSAL_ROUTER}/detect"

    status_code, response = http_post_file(url, test_file)
    duration = (time.time() - start) * 1000

    if status_code == 200:
        mime_type = response.get("mime_type", "unknown")
        category = response.get("category", "unknown")

        return TestResult(
            name="Universal Router: Detect",
            status=TestStatus.PASS,
            message=f"Detected {mime_type} ({category})",
            duration_ms=duration,
            details={"file": test_file.name, "mime": mime_type, "category": category}
        )
    elif status_code == 0:
        return TestResult(
            name="Universal Router: Detect",
            status=TestStatus.ERROR,
            message="Service not available",
            duration_ms=duration
        )
    else:
        return TestResult(
            name="Universal Router: Detect",
            status=TestStatus.FAIL,
            message=f"HTTP {status_code}",
            duration_ms=duration
        )


# =============================================================================
# WHISPERX TESTS
# =============================================================================

def test_whisperx_transcribe(test_dir: Path) -> TestResult:
    """Test audio transcription."""
    start = time.time()

    # Find audio file
    audio_files = []
    for ext in ["*.mp3", "*.wav", "*.m4a", "*.flac"]:
        audio_files.extend(test_dir.glob(f"**/{ext}"))

    if not audio_files:
        return TestResult(
            name="WhisperX: Transcribe",
            status=TestStatus.SKIP,
            message="No audio files found in test directory"
        )

    audio_file = audio_files[0]
    url = f"{ServiceConfig.WHISPERX}/transcribe"

    status_code, response = http_post_file(url, audio_file, timeout=120)
    duration = (time.time() - start) * 1000

    if status_code == 200:
        text = response.get("text", "")
        segments = response.get("segments", [])
        language = response.get("language", "unknown")

        return TestResult(
            name="WhisperX: Transcribe",
            status=TestStatus.PASS,
            message=f"Transcribed {len(segments)} segments, {len(text)} chars ({language})",
            duration_ms=duration,
            details={"file": audio_file.name, "language": language}
        )
    elif status_code == 0:
        return TestResult(
            name="WhisperX: Transcribe",
            status=TestStatus.ERROR,
            message="Service not available",
            duration_ms=duration
        )
    else:
        return TestResult(
            name="WhisperX: Transcribe",
            status=TestStatus.FAIL,
            message=f"HTTP {status_code}",
            duration_ms=duration
        )


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests(test_dir: Path, services: List[str] = None, verbose: bool = False) -> List[TestResult]:
    """Run all integration tests."""
    results = []

    # Health checks
    health_checks = [
        ("Document Processor", ServiceConfig.DOCUMENT_PROCESSOR),
        ("Universal Router", ServiceConfig.UNIVERSAL_ROUTER),
        ("Orchestrator", ServiceConfig.ORCHESTRATOR),
        ("WhisperX", ServiceConfig.WHISPERX),
        ("Tika", ServiceConfig.TIKA),
        ("API", ServiceConfig.API),
    ]

    print("\n=== Health Checks ===\n")
    for name, url in health_checks:
        if services and name.lower().replace(" ", "-") not in [s.lower() for s in services]:
            continue
        result = check_service_health(name, url)
        results.append(result)
        print_result(result, verbose)

    # Functional tests
    if not services or "document-processor" in [s.lower() for s in services]:
        print("\n=== Document Processor Tests ===\n")

        result = test_document_processor_pdf(test_dir)
        results.append(result)
        print_result(result, verbose)

        result = test_document_processor_ocr(test_dir)
        results.append(result)
        print_result(result, verbose)

        result = test_document_processor_pii()
        results.append(result)
        print_result(result, verbose)

        result = test_document_processor_embedding()
        results.append(result)
        print_result(result, verbose)

    if not services or "universal-router" in [s.lower() for s in services]:
        print("\n=== Universal Router Tests ===\n")

        result = test_universal_router_detect(test_dir)
        results.append(result)
        print_result(result, verbose)

    if not services or "whisperx" in [s.lower() for s in services]:
        print("\n=== WhisperX Tests ===\n")

        result = test_whisperx_transcribe(test_dir)
        results.append(result)
        print_result(result, verbose)

    return results


def print_result(result: TestResult, verbose: bool = False):
    """Print a test result."""
    status_icons = {
        TestStatus.PASS: "[PASS]",
        TestStatus.FAIL: "[FAIL]",
        TestStatus.SKIP: "[SKIP]",
        TestStatus.ERROR: "[ERR ]",
    }

    status_colors = {
        TestStatus.PASS: "\033[92m",  # Green
        TestStatus.FAIL: "\033[91m",  # Red
        TestStatus.SKIP: "\033[93m",  # Yellow
        TestStatus.ERROR: "\033[91m",  # Red
    }
    reset = "\033[0m"

    icon = status_icons.get(result.status, "[????]")
    color = status_colors.get(result.status, "")

    print(f"{color}{icon}{reset} {result.name} ({result.duration_ms:.0f}ms)")
    if result.message:
        print(f"       {result.message}")

    if verbose and result.details:
        print(f"       Details: {json.dumps(result.details, indent=2)}")


def print_summary(results: List[TestResult]):
    """Print test summary."""
    passed = sum(1 for r in results if r.status == TestStatus.PASS)
    failed = sum(1 for r in results if r.status == TestStatus.FAIL)
    skipped = sum(1 for r in results if r.status == TestStatus.SKIP)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)
    total = len(results)

    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} passed, {failed} failed, {skipped} skipped, {errors} errors")
    print("=" * 50)

    if failed > 0 or errors > 0:
        print("\nFailed/Error tests:")
        for r in results:
            if r.status in [TestStatus.FAIL, TestStatus.ERROR]:
                print(f"  - {r.name}: {r.message}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Neural Vault Pipeline Integration Tests")
    parser.add_argument("--test-dir", type=Path, default=Path("F:/_TestPool"),
                        help="Directory containing test files")
    parser.add_argument("--service", action="append", dest="services",
                        help="Test specific service(s) only")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Validate test directory
    if not args.test_dir.exists():
        print(f"Warning: Test directory {args.test_dir} does not exist")
        args.test_dir = Path(tempfile.gettempdir())

    print("=" * 50)
    print("Neural Vault Pipeline Integration Tests")
    print("=" * 50)
    print(f"Test Directory: {args.test_dir}")
    if args.services:
        print(f"Services: {', '.join(args.services)}")

    # Run tests
    results = run_tests(args.test_dir, args.services, args.verbose)

    # Print summary
    print_summary(results)

    # Exit code
    failed = sum(1 for r in results if r.status in [TestStatus.FAIL, TestStatus.ERROR])
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
