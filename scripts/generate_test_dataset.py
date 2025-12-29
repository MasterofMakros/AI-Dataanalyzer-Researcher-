"""
Test-Datensatz Generator - Direkt-Scan Version
Scannt F:/ direkt und sammelt 2 Dateien pro Typ
"""
import os
import shutil
from collections import defaultdict
from pathlib import Path
import random
from datetime import datetime

from config.paths import TEST_SUITE_DIR

TEST_DIR = TEST_SUITE_DIR
MAX_FILE_SIZE_MB = 50
FILES_PER_TYPE = 2
MAX_SCAN_FILES = 100000  # Limit fuer Geschwindigkeit

# Ordner die uebersprungen werden sollen
SKIP_DIRS = {
    '$RECYCLE.BIN', 'System Volume Information', 
    '_TestSuite', '_Quarantine', 'Windows', 
    '.git', 'node_modules', '__pycache__'
}

def scan_files():
    """Scanne F:/ und sammle Dateien nach Extension."""
    files_by_ext = defaultdict(list)
    scanned = 0
    
    print("Scanne F:/ ...")
    
    for root, dirs, files in os.walk("F:/"):
        # Skip bestimmte Ordner
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in files:
            if scanned >= MAX_SCAN_FILES:
                break
                
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()
            
            if not ext:
                ext = '[no_ext]'
            
            try:
                size_mb = filepath.stat().st_size / (1024 * 1024)
                
                if 0.001 < size_mb <= MAX_FILE_SIZE_MB:
                    files_by_ext[ext].append({
                        'path': str(filepath),
                        'filename': filename,
                        'size_mb': size_mb
                    })
                    scanned += 1
                    
                    if scanned % 10000 == 0:
                        print(f"  {scanned} Dateien gescannt, {len(files_by_ext)} Typen...")
                        
            except (PermissionError, OSError):
                continue
        
        if scanned >= MAX_SCAN_FILES:
            break
    
    print(f"  Gesamt: {scanned} Dateien, {len(files_by_ext)} Typen")
    return files_by_ext

def select_test_files(files_by_ext):
    """Waehle 2 Dateien pro Typ."""
    selected = {}
    
    for ext, files in files_by_ext.items():
        if len(files) >= FILES_PER_TYPE:
            # Sortiere nach Groesse, nimm mittlere
            sorted_files = sorted(files, key=lambda x: x['size_mb'])
            mid = len(sorted_files) // 2
            
            # Nimm 2 verschiedene
            indices = [mid, 0 if mid > 0 else len(sorted_files)-1]
            selected[ext] = [sorted_files[i] for i in indices[:FILES_PER_TYPE]]
        elif len(files) > 0:
            selected[ext] = files
    
    return selected

def copy_files(selected):
    """Kopiere Testdateien."""
    # Loesche/Erstelle Testordner
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True)
    
    copied = []
    errors = []
    
    for ext, files in selected.items():
        # Ordnername aus Extension
        folder_name = ext.replace('.', '').replace('[', '').replace(']', '') or 'no_ext'
        ext_folder = TEST_DIR / folder_name
        ext_folder.mkdir(exist_ok=True)
        
        for f in files:
            src = Path(f['path'])
            dst = ext_folder / f['filename']
            
            try:
                shutil.copy2(src, dst)
                copied.append({
                    'ext': ext,
                    'file': f['filename'],
                    'size': f['size_mb'],
                    'src': str(src),
                    'dst': str(dst)
                })
                print(f"  OK: {ext} - {f['filename'][:40]}")
            except Exception as e:
                errors.append({'ext': ext, 'file': f['filename'], 'error': str(e)})
                print(f"  FEHLER: {ext} - {f['filename'][:40]}: {e}")
    
    return copied, errors

def create_manifest(copied, errors, files_by_ext):
    """Erstelle Manifest-Datei."""
    manifest = TEST_DIR / "_MANIFEST.md"
    
    # Kategorisierung
    categories = {
        'Dokumente': {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.rtf', '.odt', '.ods'},
        'E-Mail': {'.eml', '.msg', '.mbox'},
        'Bilder': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico', '.psd'},
        'RAW-Fotos': {'.arw', '.cr2', '.cr3', '.nef', '.dng', '.raw', '.orf', '.rw2'},
        'Video': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'},
        'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'},
        'Archive': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
        'Code': {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php', '.rb', '.swift'},
        'Web': {'.html', '.htm', '.css', '.scss', '.less'},
        'Daten': {'.json', '.xml', '.yaml', '.yml', '.csv', '.sql', '.db', '.sqlite'},
        'Konfig': {'.ini', '.cfg', '.conf', '.config', '.env', '.properties'},
    }
    
    with open(manifest, 'w', encoding='utf-8') as f:
        f.write("# Neural Vault Test-Datensatz\n\n")
        f.write(f"> Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Summary
        total_size = sum(c['size'] for c in copied)
        f.write("## Zusammenfassung\n\n")
        f.write("| Metrik | Wert |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| Dateitypen auf F: | {len(files_by_ext)} |\n")
        f.write(f"| Typen im Test | {len(set(c['ext'] for c in copied))} |\n")
        f.write(f"| Test-Dateien | {len(copied)} |\n")
        f.write(f"| Gesamtgroesse | {total_size:.1f} MB |\n")
        f.write(f"| Fehler | {len(errors)} |\n\n")
        
        # Nach Kategorie
        f.write("## Dateien nach Kategorie\n\n")
        
        categorized = set()
        for cat_name, cat_exts in categories.items():
            cat_files = [c for c in copied if c['ext'] in cat_exts]
            if cat_files:
                f.write(f"### {cat_name} ({len(cat_files)} Dateien)\n\n")
                f.write("| Typ | Datei | Groesse |\n")
                f.write("| :--- | :--- | ---: |\n")
                for c in cat_files:
                    f.write(f"| `{c['ext']}` | {c['file'][:45]} | {c['size']:.2f} MB |\n")
                    categorized.add(c['ext'])
                f.write("\n")
        
        # Sonstige
        other_files = [c for c in copied if c['ext'] not in categorized]
        if other_files:
            f.write(f"### Sonstige ({len(other_files)} Dateien)\n\n")
            f.write("| Typ | Datei | Groesse |\n")
            f.write("| :--- | :--- | ---: |\n")
            for c in sorted(other_files, key=lambda x: x['ext']):
                f.write(f"| `{c['ext']}` | {c['file'][:45]} | {c['size']:.2f} MB |\n")
            f.write("\n")
        
        # Extension-Liste
        f.write("## Alle Extensions\n\n")
        f.write("```\n")
        all_exts = sorted(set(c['ext'] for c in copied))
        f.write(", ".join(all_exts))
        f.write("\n```\n")
    
    print(f"\nManifest: {manifest}")

def main():
    print("=" * 60)
    print("TEST-DATENSATZ GENERATOR (Direkt-Scan)")
    print("=" * 60)
    print(f"Ziel: {TEST_DIR}")
    print(f"Max. Dateigroesse: {MAX_FILE_SIZE_MB} MB")
    print(f"Dateien pro Typ: {FILES_PER_TYPE}")
    print()
    
    # Scan
    files_by_ext = scan_files()
    
    # Select
    print(f"\nWaehle Testdateien...")
    selected = select_test_files(files_by_ext)
    print(f"  {sum(len(v) for v in selected.values())} Dateien aus {len(selected)} Typen")
    
    # Copy
    print(f"\nKopiere Dateien nach {TEST_DIR}...")
    copied, errors = copy_files(selected)
    
    # Manifest
    create_manifest(copied, errors, files_by_ext)
    
    print("\n" + "=" * 60)
    print("FERTIG!")
    print(f"  Kopiert: {len(copied)} Dateien")
    print(f"  Fehler: {len(errors)}")
    print(f"  Ordner: {TEST_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
