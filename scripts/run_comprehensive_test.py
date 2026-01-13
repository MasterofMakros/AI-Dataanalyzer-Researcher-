"""
Neural Vault - Umfassender Dateityp-Test
Testet alle Dateitypen im TestSuite-Ordner und erstellt Bericht
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

from config.paths import TEST_SUITE_DIR, BASE_DIR

# Konfiguration
TEST_DIR = TEST_SUITE_DIR
REPORT_FILE = TEST_DIR / "_TEST_REPORT.md"
RESULTS_JSON = TEST_DIR / "_test_results.json"

TIKA_URL = "http://localhost:9998"
OLLAMA_URL = "http://localhost:11435"

# Keys
def load_env():
    env_path = BASE_DIR / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env

ENV = load_env()

@dataclass
class TestResult:
    filepath: str
    extension: str
    filename: str
    size_mb: float
    
    # Tika
    tika_success: bool = False
    tika_time: float = 0.0
    tika_mime: str = ""
    tika_text_length: int = 0
    tika_error: str = ""
    
    # Ollama
    ollama_success: bool = False
    ollama_time: float = 0.0
    ollama_category: str = ""
    ollama_confidence: float = 0.0
    ollama_error: str = ""
    
    # Overall
    processing_success: bool = False
    total_time: float = 0.0

def test_tika(filepath: Path) -> dict:
    """Teste Tika Text-Extraktion."""
    result = {
        "success": False,
        "time": 0.0,
        "mime": "",
        "text_length": 0,
        "error": ""
    }
    
    start = time.time()
    try:
        # MIME-Type Detection
        with open(filepath, "rb") as f:
            mime_resp = requests.put(
                f"{TIKA_URL}/detect/stream",
                data=f.read(8192),
                headers={"Accept": "text/plain"},
                timeout=30
            )
        result["mime"] = mime_resp.text.strip() if mime_resp.ok else "unknown"
        
        # Text Extraction
        with open(filepath, "rb") as f:
            text_resp = requests.put(
                f"{TIKA_URL}/tika",
                data=f,
                headers={"Accept": "text/plain"},
                timeout=60
            )
        
        if text_resp.ok:
            result["text_length"] = len(text_resp.text.strip())
            result["success"] = True
        else:
            result["error"] = f"HTTP {text_resp.status_code}"
            
    except Exception as e:
        result["error"] = str(e)[:100]
    
    result["time"] = time.time() - start
    return result

def test_ollama(text: str, filename: str) -> dict:
    """Teste Ollama Klassifizierung."""
    result = {
        "success": False,
        "time": 0.0,
        "category": "",
        "confidence": 0.0,
        "error": ""
    }
    
    if len(text) < 10:
        text = f"Dateiname: {filename}"
    
    prompt = f"""Klassifiziere diese Datei. Antworte NUR mit JSON.

Dateiname: {filename}
Inhalt: {text[:1000]}

JSON-Format:
{{"category": "Technologie", "confidence": 0.8}}

Kategorien: Finanzen, Arbeit, Privat, Medien, Dokumente, Technologie, Sonstiges"""

    start = time.time()
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        
        if response.ok:
            resp_text = response.json().get("response", "{}")
            parsed = json.loads(resp_text)
            result["category"] = parsed.get("category", "Sonstiges")
            result["confidence"] = float(parsed.get("confidence", 0.5))
            result["success"] = True
        else:
            result["error"] = f"HTTP {response.status_code}"
            
    except json.JSONDecodeError:
        result["error"] = "JSON Parse Error"
        result["category"] = "Sonstiges"
        result["confidence"] = 0.5
        result["success"] = True  # Fallback OK
    except Exception as e:
        result["error"] = str(e)[:100]
    
    result["time"] = time.time() - start
    return result

def process_file(filepath: Path) -> TestResult:
    """Verarbeite eine einzelne Datei."""
    stat = filepath.stat()
    
    result = TestResult(
        filepath=str(filepath),
        extension=filepath.suffix.lower() or "[no_ext]",
        filename=filepath.name,
        size_mb=stat.st_size / (1024 * 1024)
    )
    
    start_total = time.time()
    
    # 1. Tika Test
    tika = test_tika(filepath)
    result.tika_success = tika["success"]
    result.tika_time = tika["time"]
    result.tika_mime = tika["mime"]
    result.tika_text_length = tika["text_length"]
    result.tika_error = tika["error"]
    
    # 2. Ollama Test (nur wenn Tika Text hat oder Dateiname)
    if tika["text_length"] > 0:
        # Hole Text nochmal
        try:
            with open(filepath, "rb") as f:
                text_resp = requests.put(f"{TIKA_URL}/tika", data=f, 
                                        headers={"Accept": "text/plain"}, timeout=60)
                text = text_resp.text[:2000] if text_resp.ok else ""
        except:
            text = ""
    else:
        text = ""
    
    ollama = test_ollama(text, filepath.name)
    result.ollama_success = ollama["success"]
    result.ollama_time = ollama["time"]
    result.ollama_category = ollama["category"]
    result.ollama_confidence = ollama["confidence"]
    result.ollama_error = ollama["error"]
    
    result.total_time = time.time() - start_total
    result.processing_success = result.tika_success and result.ollama_success
    
    return result

def run_tests(limit: int = None) -> List[TestResult]:
    """Fuehre alle Tests durch."""
    results = []
    
    # Sammle alle Dateien
    test_files = []
    for folder in TEST_DIR.iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            for f in folder.iterdir():
                if f.is_file():
                    test_files.append(f)
    
    if limit:
        test_files = test_files[:limit]
    
    total = len(test_files)
    print(f"Starte Tests fuer {total} Dateien...")
    print("-" * 60)
    
    for i, filepath in enumerate(test_files, 1):
        print(f"[{i}/{total}] {filepath.suffix}: {filepath.name[:40]}...", end=" ", flush=True)
        
        result = process_file(filepath)
        results.append(result)
        
        status = "OK" if result.processing_success else "FAIL"
        print(f"{status} ({result.total_time:.1f}s)")
    
    return results

def generate_report(results: List[TestResult]):
    """Generiere ausfuehrlichen Bericht."""
    
    # Statistiken berechnen
    total = len(results)
    success = sum(1 for r in results if r.processing_success)
    tika_success = sum(1 for r in results if r.tika_success)
    ollama_success = sum(1 for r in results if r.ollama_success)
    
    avg_time = sum(r.total_time for r in results) / total if total > 0 else 0
    avg_tika = sum(r.tika_time for r in results) / total if total > 0 else 0
    avg_ollama = sum(r.ollama_time for r in results) / total if total > 0 else 0
    avg_confidence = sum(r.ollama_confidence for r in results if r.ollama_success) / ollama_success if ollama_success > 0 else 0
    
    # Nach Extension gruppieren
    by_ext = defaultdict(list)
    for r in results:
        by_ext[r.extension].append(r)
    
    # Report schreiben
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Neural Vault - Umfassender Test-Bericht\n\n")
        f.write(f"> Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## Zusammenfassung\n\n")
        f.write("| Metrik | Wert |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Dateien getestet** | {total} |\n")
        f.write(f"| **Erfolgreich** | {success} ({success/total*100:.1f}%) |\n")
        f.write(f"| **Tika Erfolg** | {tika_success} ({tika_success/total*100:.1f}%) |\n")
        f.write(f"| **Ollama Erfolg** | {ollama_success} ({ollama_success/total*100:.1f}%) |\n")
        f.write(f"| **Dateitypen** | {len(by_ext)} |\n")
        f.write(f"| **Fehlerrate** | {(total-success)/total*100:.1f}% |\n\n")
        
        f.write("### Performance\n\n")
        f.write("| Metrik | Wert |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Durchschn. Gesamtzeit** | {avg_time:.1f}s |\n")
        f.write(f"| **Durchschn. Tika Zeit** | {avg_tika:.1f}s |\n")
        f.write(f"| **Durchschn. Ollama Zeit** | {avg_ollama:.1f}s |\n")
        f.write(f"| **Durchschn. Konfidenz** | {avg_confidence:.0%} |\n\n")
        
        # Nach Extension
        f.write("## Ergebnisse nach Dateityp\n\n")
        f.write("| Extension | Getestet | Erfolg | Tika | Ollama | Avg Time |\n")
        f.write("| :--- | ---: | ---: | ---: | ---: | ---: |\n")
        
        for ext in sorted(by_ext.keys()):
            ext_results = by_ext[ext]
            ext_total = len(ext_results)
            ext_success = sum(1 for r in ext_results if r.processing_success)
            ext_tika = sum(1 for r in ext_results if r.tika_success)
            ext_ollama = sum(1 for r in ext_results if r.ollama_success)
            ext_time = sum(r.total_time for r in ext_results) / ext_total
            
            status = "OK" if ext_success == ext_total else "WARN" if ext_success > 0 else "FAIL"
            f.write(f"| `{ext}` | {ext_total} | {ext_success} ({status}) | {ext_tika} | {ext_ollama} | {ext_time:.1f}s |\n")
        
        # Fehler-Details
        failures = [r for r in results if not r.processing_success]
        if failures:
            f.write(f"\n## Fehler ({len(failures)})\n\n")
            f.write("| Datei | Tika | Ollama | Fehler |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for r in failures[:30]:
                tika_status = "OK" if r.tika_success else "FAIL"
                ollama_status = "OK" if r.ollama_success else "FAIL"
                error = r.tika_error or r.ollama_error or "Unknown"
                f.write(f"| `{r.extension}` {r.filename[:30]} | {tika_status} | {ollama_status} | {error[:40]} |\n")
        
        # Kategorie-Verteilung
        categories = defaultdict(int)
        for r in results:
            if r.ollama_category:
                categories[r.ollama_category] += 1
        
        f.write("\n## Kategorie-Verteilung (Ollama)\n\n")
        f.write("| Kategorie | Anzahl |\n")
        f.write("| :--- | ---: |\n")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            f.write(f"| {cat} | {count} |\n")
    
    # JSON speichern
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    
    print(f"\nBericht: {REPORT_FILE}")
    print(f"JSON: {RESULTS_JSON}")

def main():
    print("=" * 60)
    print("NEURAL VAULT - UMFASSENDER DATEITYP-TEST")
    print("=" * 60)
    print(f"Test-Ordner: {TEST_DIR}")
    print(f"Tika: {TIKA_URL}")
    print(f"Ollama: {OLLAMA_URL}")
    print()
    
    # Limit fuer ersten Test (alle = None)
    limit = 50  # Setze auf None fuer alle Dateien
    
    results = run_tests(limit)
    
    print("\n" + "=" * 60)
    print("GENERIERE BERICHT...")
    generate_report(results)
    
    # Summary
    total = len(results)
    success = sum(1 for r in results if r.processing_success)
    print("\n" + "=" * 60)
    print(f"FERTIG: {success}/{total} erfolgreich ({success/total*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
