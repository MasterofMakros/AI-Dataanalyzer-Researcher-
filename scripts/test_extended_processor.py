"""
Test-Suite für Extended File Processor
Testet alle neuen Dateityp-Parser auf echten Dateien
"""

import json
import time
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

# Import processors
import sys
sys.path.insert(0, str(Path(__file__).parent))
from extended_file_processor import (
    process_torrent, process_eml, process_exr, 
    process_srt, process_apk, get_supported_extensions
)

from config.paths import TEST_SUITE_DIR, BASE_DIR

TEST_BASE = Path("F:/") # Still scanning F:/ for test files as per original intent

def find_test_files():
    """Finde echte Testdateien auf F:"""
    test_files = {}
    extensions = [".torrent", ".eml", ".exr", ".srt", ".apk"]
    
    for ext in extensions:
        print(f"Suche {ext}...", end=" ")
        for f in TEST_BASE.rglob(f"*{ext}"):
            test_files[ext] = f
            print(f"✅ {f.name[:50]}")
            break
        else:
            print("❌ nicht gefunden")
    
    return test_files


def run_test(ext: str, filepath: Path, processor):
    """Führe einzelnen Test aus"""
    print(f"\n{'='*60}")
    print(f"TEST: {ext}")
    print(f"Datei: {filepath.name}")
    print(f"{'='*60}")
    
    start = time.time()
    result = processor(filepath)
    duration = time.time() - start
    
    print(f"Erfolg: {'✅' if result.success else '❌'}")
    print(f"Verarbeitungszeit: {duration:.4f}s")
    print(f"Vollständigkeit: {result.completeness*100:.0f}%")
    print(f"Konfidenz: {result.confidence*100:.0f}%")
    print(f"Summary: {result.summary}")
    
    if result.error:
        print(f"Fehler: {result.error}")
    
    if result.metadata:
        print(f"Metadaten:")
        for key, value in list(result.metadata.items())[:10]:
            val_str = str(value)[:80]
            print(f"  {key}: {val_str}")
    
    return result


def main():
    print("="*60)
    print("EXTENDED FILE PROCESSOR - TEST SUITE")
    print(f"Datum: {datetime.now().isoformat()}")
    print("="*60)
    
    processors = {
        ".torrent": process_torrent,
        ".eml": process_eml,
        ".exr": process_exr,
        ".srt": process_srt,
        ".apk": process_apk,
    }
    
    # Finde Testdateien
    print("\n1. SUCHE TESTDATEIEN")
    print("-"*40)
    test_files = find_test_files()
    
    # Führe Tests aus
    print("\n2. TESTS")
    print("-"*40)
    
    results = {}
    passed = 0
    failed = 0
    
    for ext, processor in processors.items():
        if ext in test_files:
            result = run_test(ext, test_files[ext], processor)
            results[ext] = {
                "success": result.success,
                "time": result.processing_time,
                "completeness": result.completeness,
                "confidence": result.confidence,
                "summary": result.summary
            }
            if result.success:
                passed += 1
            else:
                failed += 1
        else:
            results[ext] = {"success": False, "error": "Keine Testdatei gefunden"}
            failed += 1
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Bestanden: {passed}/{len(processors)}")
    print(f"Fehlgeschlagen: {failed}/{len(processors)}")
    
    total = passed + failed
    if total > 0:
        print(f"Erfolgsquote: {passed/total*100:.0f}%")
    
    # Speichere Ergebnisse
    report_path = TEST_SUITE_DIR / "_EXTENDED_PROCESSOR_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "failed": failed,
            "results": results
        }, f, indent=2, default=str)
    
    print(f"\nBericht: {report_path}")
    return passed, failed


if __name__ == "__main__":
    main()
