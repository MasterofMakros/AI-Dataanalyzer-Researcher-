"""
A/B-Test: Parallel File Walker
os.walk (A) vs Dask (B) vs concurrent.futures (C)

Messkriterien:
- File Discovery Speed (Files/s)
- Memory Usage (MB)
- CPU Utilization (%)
- Error Handling
"""

import time
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
import psutil
import concurrent.futures

# Test-Verzeichnis (realistisch groß)
TEST_DIR = Path(r"F:\_TestSuite")  # ~500 Dateien
from config.paths import BASE_DIR

LARGE_DIR = Path(os.path.splitdrive(BASE_DIR)[0] + "/")  # Optional: Vollscan-Simulation (Root of drive)

@dataclass
class WalkerResult:
    name: str
    files_found: int
    dirs_found: int
    duration_sec: float
    files_per_sec: float
    memory_mb: float
    errors: int


def measure_resources() -> tuple:
    """Misst aktuelle Ressourcen."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024, process.cpu_percent()


def test_os_walk(directory: Path) -> WalkerResult:
    """Test A: Standard os.walk"""
    print(f"\n{'='*60}")
    print(f"Test A: os.walk")
    print(f"{'='*60}")
    
    start_mem, _ = measure_resources()
    start_time = time.time()
    
    files = 0
    dirs = 0
    errors = 0
    
    try:
        for root, dirnames, filenames in os.walk(directory):
            dirs += len(dirnames)
            files += len(filenames)
    except Exception as e:
        errors += 1
        print(f"  ❌ Error: {e}")
    
    duration = time.time() - start_time
    end_mem, _ = measure_resources()
    
    result = WalkerResult(
        name="os.walk",
        files_found=files,
        dirs_found=dirs,
        duration_sec=duration,
        files_per_sec=files / duration if duration > 0 else 0,
        memory_mb=end_mem - start_mem,
        errors=errors
    )
    
    print(f"  Files:    {result.files_found:,}")
    print(f"  Dirs:     {result.dirs_found:,}")
    print(f"  Zeit:     {result.duration_sec:.2f}s")
    print(f"  Speed:    {result.files_per_sec:,.0f} Files/s")
    print(f"  Memory:   {result.memory_mb:.1f} MB")
    
    return result


def test_dask_walk(directory: Path) -> WalkerResult:
    """Test B: Dask Parallel Walker"""
    print(f"\n{'='*60}")
    print(f"Test B: Dask Delayed")
    print(f"{'='*60}")
    
    try:
        import dask
        from dask import delayed, compute
    except ImportError:
        print("  ❌ Dask nicht installiert")
        return WalkerResult("Dask", 0, 0, 0, 0, 0, 1)
    
    start_mem, _ = measure_resources()
    start_time = time.time()
    
    @delayed
    def count_dir(path):
        files = 0
        dirs = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    files += 1
                elif entry.is_dir():
                    dirs += 1
        except:
            pass
        return files, dirs
    
    # Sammle alle Verzeichnisse
    all_dirs = []
    for root, dirnames, _ in os.walk(directory):
        all_dirs.append(root)
    
    # Parallel verarbeiten
    tasks = [count_dir(d) for d in all_dirs]
    results = compute(*tasks)
    
    total_files = sum(r[0] for r in results)
    total_dirs = sum(r[1] for r in results)
    
    duration = time.time() - start_time
    end_mem, _ = measure_resources()
    
    result = WalkerResult(
        name="Dask",
        files_found=total_files,
        dirs_found=total_dirs,
        duration_sec=duration,
        files_per_sec=total_files / duration if duration > 0 else 0,
        memory_mb=end_mem - start_mem,
        errors=0
    )
    
    print(f"  Files:    {result.files_found:,}")
    print(f"  Dirs:     {result.dirs_found:,}")
    print(f"  Zeit:     {result.duration_sec:.2f}s")
    print(f"  Speed:    {result.files_per_sec:,.0f} Files/s")
    print(f"  Memory:   {result.memory_mb:.1f} MB")
    
    return result


def test_concurrent_walk(directory: Path, workers: int = 8) -> WalkerResult:
    """Test C: ThreadPoolExecutor Walker"""
    print(f"\n{'='*60}")
    print(f"Test C: concurrent.futures ({workers} Workers)")
    print(f"{'='*60}")
    
    start_mem, _ = measure_resources()
    start_time = time.time()
    
    def count_dir(path):
        files = 0
        dirs = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    files += 1
                elif entry.is_dir():
                    dirs += 1
        except:
            pass
        return files, dirs
    
    # Sammle alle Verzeichnisse
    all_dirs = []
    for root, dirnames, _ in os.walk(directory):
        all_dirs.append(root)
    
    # Parallel mit ThreadPool
    total_files = 0
    total_dirs = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(count_dir, all_dirs))
    
    total_files = sum(r[0] for r in results)
    total_dirs = sum(r[1] for r in results)
    
    duration = time.time() - start_time
    end_mem, _ = measure_resources()
    
    result = WalkerResult(
        name=f"ThreadPool-{workers}",
        files_found=total_files,
        dirs_found=total_dirs,
        duration_sec=duration,
        files_per_sec=total_files / duration if duration > 0 else 0,
        memory_mb=end_mem - start_mem,
        errors=0
    )
    
    print(f"  Files:    {result.files_found:,}")
    print(f"  Dirs:     {result.dirs_found:,}")
    print(f"  Zeit:     {result.duration_sec:.2f}s")
    print(f"  Speed:    {result.files_per_sec:,.0f} Files/s")
    print(f"  Memory:   {result.memory_mb:.1f} MB")
    
    return result


def compare_walkers(results: List[WalkerResult]):
    """Vergleiche alle Walker-Ergebnisse."""
    print(f"\n{'='*70}")
    print(f"A/B-TEST ERGEBNIS: File Walker Vergleich")
    print(f"{'='*70}")
    
    # Sortiere nach Speed
    sorted_results = sorted(results, key=lambda x: x.files_per_sec, reverse=True)
    
    baseline = next((r for r in results if r.name == "os.walk"), results[0])
    
    print(f"\n{'Walker':<20} {'Files':<12} {'Zeit':<10} {'Speed':<15} {'Memory':<10} {'Speedup':<10}")
    print("-" * 80)
    
    for r in sorted_results:
        speedup = r.files_per_sec / baseline.files_per_sec if baseline.files_per_sec > 0 else 0
        print(f"{r.name:<20} {r.files_found:<12,} {r.duration_sec:<10.2f}s {r.files_per_sec:<15,.0f} {r.memory_mb:<10.1f}MB {speedup:<10.2f}x")
    
    # Gewinner bestimmen
    winner = sorted_results[0]
    
    print(f"\n🏆 SCHNELLSTER: {winner.name}")
    print(f"   → {winner.files_per_sec:,.0f} Files/s")
    
    # Alle Aspekte prüfen
    all_better = all([
        winner.files_per_sec >= r.files_per_sec for r in results if r.name != winner.name
    ])
    
    memory_acceptable = winner.memory_mb < 500  # Max 500 MB
    
    if winner.name != "os.walk" and all_better and memory_acceptable:
        print(f"\n✅ EMPFEHLUNG: UPGRADE zu {winner.name}")
    else:
        print(f"\n⚠️  EMPFEHLUNG: KEEP os.walk (Trade-offs vorhanden)")


if __name__ == "__main__":
    print("=" * 70)
    print("NEURAL VAULT - A/B-TEST: FILE WALKER")
    print("=" * 70)
    print(f"Testverzeichnis: {TEST_DIR}")
    
    results = []
    
    # Test A: os.walk
    results.append(test_os_walk(TEST_DIR))
    
    # Test B: Dask
    results.append(test_dask_walk(TEST_DIR))
    
    # Test C: ThreadPool
    results.append(test_concurrent_walk(TEST_DIR, workers=8))
    
    # Vergleich
    compare_walkers(results)
    
    print("\n" + "=" * 70)
    print("A/B-TESTS ABGESCHLOSSEN")
    print("=" * 70)
