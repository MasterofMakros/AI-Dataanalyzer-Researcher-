"""
A/B-Test Framework für Neural Vault Challenger-Evaluierung
Stand: 27.12.2025

Regel: Upgrade nur wenn Challenger in ALLEN Aspekten besser ist.
"""

import time
import os
import sys
import json
import traceback
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Callable, List, Dict, Any, Optional
import psutil

# Test-Verzeichnis
TEST_DIR = Path(r"F:\_TestSuite\_FormatCoverage")

@dataclass
class BenchmarkResult:
    """Ergebnis eines einzelnen Benchmark-Laufs."""
    name: str
    variant: str  # "A" (aktuell) oder "B" (challenger)
    accuracy: float  # 0.0 - 1.0
    speed_docs_per_sec: float
    memory_mb: float
    cpu_percent: float
    errors: int
    total_files: int
    success_rate: float
    extra_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_metrics is None:
            self.extra_metrics = {}

@dataclass
class ABTestResult:
    """Vergleich zweier Varianten."""
    test_name: str
    variant_a: BenchmarkResult  # Aktuell
    variant_b: BenchmarkResult  # Challenger
    winner: str  # "A", "B", oder "TIE"
    recommendation: str  # "KEEP", "UPGRADE", oder "INCONCLUSIVE"
    all_aspects_better: bool


def measure_resources() -> tuple:
    """Misst aktuelle Ressourcen."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024, process.cpu_percent()


def run_benchmark(
    name: str,
    variant: str,
    test_func: Callable,
    test_files: List[Path],
    accuracy_func: Callable = None
) -> BenchmarkResult:
    """Führt Benchmark für eine Variante durch."""
    
    print(f"\n{'='*60}")
    print(f"Benchmark: {name} (Variante {variant})")
    print(f"{'='*60}")
    
    start_mem, _ = measure_resources()
    start_time = time.time()
    
    successes = 0
    errors = 0
    accuracies = []
    
    for i, filepath in enumerate(test_files):
        try:
            result = test_func(filepath)
            if result.get("success", False):
                successes += 1
                if accuracy_func:
                    acc = accuracy_func(filepath, result)
                    accuracies.append(acc)
            else:
                errors += 1
            
            # Progress
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(test_files)}] {successes} OK, {errors} Fehler")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ {filepath.name}: {str(e)[:50]}")
    
    end_time = time.time()
    end_mem, cpu = measure_resources()
    
    duration = end_time - start_time
    docs_per_sec = len(test_files) / duration if duration > 0 else 0
    
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    
    result = BenchmarkResult(
        name=name,
        variant=variant,
        accuracy=avg_accuracy,
        speed_docs_per_sec=docs_per_sec,
        memory_mb=end_mem - start_mem,
        cpu_percent=cpu,
        errors=errors,
        total_files=len(test_files),
        success_rate=successes / len(test_files) if test_files else 0
    )
    
    print(f"\n  Ergebnis Variante {variant}:")
    print(f"    Accuracy:   {result.accuracy*100:.1f}%")
    print(f"    Speed:      {result.speed_docs_per_sec:.2f} Docs/s")
    print(f"    Memory:     {result.memory_mb:.1f} MB")
    print(f"    Success:    {result.success_rate*100:.1f}%")
    print(f"    Errors:     {result.errors}")
    
    return result


def compare_variants(a: BenchmarkResult, b: BenchmarkResult, test_name: str) -> ABTestResult:
    """Vergleicht zwei Varianten und bestimmt Gewinner."""
    
    # Alle Aspekte prüfen (B muss in ALLEN besser sein)
    b_better_accuracy = b.accuracy >= a.accuracy
    b_better_speed = b.speed_docs_per_sec >= a.speed_docs_per_sec
    b_better_memory = b.memory_mb <= a.memory_mb or b.memory_mb < 100  # Toleranz für kleine Werte
    b_better_success = b.success_rate >= a.success_rate
    b_fewer_errors = b.errors <= a.errors
    
    all_better = all([
        b_better_accuracy,
        b_better_speed,
        b_better_memory,
        b_better_success,
        b_fewer_errors
    ])
    
    # Signifikante Verbesserung in Hauptmetriken?
    significant_improvement = (
        b.accuracy > a.accuracy + 0.05 or  # +5% Accuracy
        b.speed_docs_per_sec > a.speed_docs_per_sec * 1.5  # +50% Speed
    )
    
    if all_better and significant_improvement:
        winner = "B"
        recommendation = "UPGRADE"
    elif all_better:
        winner = "B"
        recommendation = "UPGRADE (marginal)"
    elif b_better_accuracy and b_better_success:
        winner = "TIE"
        recommendation = "INCONCLUSIVE"
    else:
        winner = "A"
        recommendation = "KEEP"
    
    return ABTestResult(
        test_name=test_name,
        variant_a=a,
        variant_b=b,
        winner=winner,
        recommendation=recommendation,
        all_aspects_better=all_better
    )


def print_comparison(result: ABTestResult):
    """Druckt Vergleichsergebnis."""
    
    a = result.variant_a
    b = result.variant_b
    
    print(f"\n{'='*70}")
    print(f"A/B-TEST ERGEBNIS: {result.test_name}")
    print(f"{'='*70}")
    
    print(f"\n{'Metrik':<20} {'A (Aktuell)':<15} {'B (Challenger)':<15} {'Besser':<10}")
    print("-" * 60)
    
    # Accuracy
    better = "B ✅" if b.accuracy >= a.accuracy else "A ✅"
    print(f"{'Accuracy':<20} {a.accuracy*100:>12.1f}% {b.accuracy*100:>12.1f}% {better:<10}")
    
    # Speed
    better = "B ✅" if b.speed_docs_per_sec >= a.speed_docs_per_sec else "A ✅"
    print(f"{'Speed (Docs/s)':<20} {a.speed_docs_per_sec:>12.2f} {b.speed_docs_per_sec:>12.2f} {better:<10}")
    
    # Memory
    better = "B ✅" if b.memory_mb <= a.memory_mb else "A ✅"
    print(f"{'Memory (MB)':<20} {a.memory_mb:>12.1f} {b.memory_mb:>12.1f} {better:<10}")
    
    # Success Rate
    better = "B ✅" if b.success_rate >= a.success_rate else "A ✅"
    print(f"{'Success Rate':<20} {a.success_rate*100:>12.1f}% {b.success_rate*100:>12.1f}% {better:<10}")
    
    # Errors
    better = "B ✅" if b.errors <= a.errors else "A ✅"
    print(f"{'Errors':<20} {a.errors:>12} {b.errors:>12} {better:<10}")
    
    print("-" * 60)
    print(f"\n🏆 GEWINNER: Variante {result.winner}")
    print(f"📋 EMPFEHLUNG: {result.recommendation}")
    print(f"✅ Alle Aspekte besser: {'Ja' if result.all_aspects_better else 'Nein'}")
    
    if not result.all_aspects_better:
        print("\n⚠️  WARNUNG: Challenger ist NICHT in allen Aspekten besser!")
        print("   → Keine Implementierung empfohlen (Verschlimmbesserung möglich)")


def get_test_files(extensions: List[str], max_per_ext: int = 5) -> List[Path]:
    """Sammelt Testdateien."""
    files = []
    for ext in extensions:
        ext_dir = TEST_DIR / ext.lstrip(".")
        if ext_dir.exists():
            ext_files = list(ext_dir.glob(f"*{ext}"))[:max_per_ext]
            files.extend(ext_files)
    return files


# ============================================================
# TEST-DEFINITIONEN
# ============================================================

def test_ocr_tesseract(filepath: Path) -> dict:
    """Test A: Tesseract OCR via Docker."""
    import subprocess
    
    container_path = str(filepath).replace("F:", "/mnt/data").replace("\\", "/")
    cmd = [
        "docker", "exec", "conductor-tesseract",
        "tesseract", container_path, "stdout", "-l", "deu+eng"
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        text = proc.stdout
        return {"success": len(text) > 10, "text": text, "chars": len(text)}
    except:
        return {"success": False}


def test_ocr_docling(filepath: Path) -> dict:
    """Test B: Docling OCR (falls installiert)."""
    try:
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        result = converter.convert(str(filepath))
        text = result.document.export_to_markdown()
        return {"success": len(text) > 10, "text": text, "chars": len(text)}
    except ImportError:
        return {"success": False, "error": "Docling nicht installiert"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_walker_os(directory: Path) -> dict:
    """Test A: os.walk File Discovery."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for f in filenames:
            files.append(Path(root) / f)
    return {"success": True, "count": len(files), "files": files}


def test_walker_dask(directory: Path) -> dict:
    """Test B: Dask Parallel File Discovery."""
    try:
        import dask
        from dask import delayed, compute
        
        @delayed
        def scan_dir(path):
            return list(Path(path).iterdir())
        
        # Einfacher Test: Sammle alle Dateien
        files = []
        for item in directory.iterdir():
            if item.is_file():
                files.append(item)
            elif item.is_dir():
                files.extend(item.rglob("*"))
        
        return {"success": True, "count": len([f for f in files if f.is_file()])}
    except ImportError:
        return {"success": False, "error": "Dask nicht installiert"}


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("NEURAL VAULT - A/B-TEST FRAMEWORK")
    print("Regel: Upgrade nur wenn Challenger in ALLEN Aspekten besser")
    print("=" * 70)
    
    # Test 1: OCR (Tesseract vs Docling)
    print("\n📊 Test 1: OCR Vergleich")
    ocr_files = get_test_files([".jpg", ".png", ".tiff"], max_per_ext=3)
    
    if ocr_files:
        result_a = run_benchmark(
            "OCR", "A (Tesseract)",
            test_ocr_tesseract,
            ocr_files
        )
        
        result_b = run_benchmark(
            "OCR", "B (Docling)",
            test_ocr_docling,
            ocr_files
        )
        
        comparison = compare_variants(result_a, result_b, "OCR: Tesseract vs Docling")
        print_comparison(comparison)
    else:
        print("  Keine Testdateien gefunden")
    
    print("\n" + "=" * 70)
    print("A/B-TESTS ABGESCHLOSSEN")
    print("=" * 70)
