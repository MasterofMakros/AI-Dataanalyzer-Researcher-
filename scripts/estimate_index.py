"""Analyze F:/ drive index for storage and time estimates."""
import csv
from collections import Counter
from pathlib import Path

import os
from config.paths import BASE_DIR

csv_path = str(BASE_DIR / "scripts" / "f_drive_index.csv")

total_files = 0
total_size_mb = 0
ext_count = Counter()
ext_size = Counter()
text_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.xlsx', '.xls', '.csv', '.json', '.xml', '.html', '.htm', '.eml', '.msg'}

with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_files += 1
        ext = row.get('Extension', '').lower()
        try:
            size = float(row.get('Size_MB', 0))
        except:
            size = 0
        total_size_mb += size
        ext_count[ext] += 1
        ext_size[ext] += size

# Berechne Text-Files
text_count = sum(ext_count[e] for e in text_extensions if e in ext_count)
text_size = sum(ext_size[e] for e in text_extensions if e in ext_size)

# Medien-Dateien
media_ext = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav', '.flac'}
media_count = sum(ext_count[e] for e in media_ext if e in ext_count)
media_size = sum(ext_size[e] for e in media_ext if e in ext_size)

print('='*60)
print('F:/ DRIVE INDEX ANALYSE')
print('='*60)
print(f'Gesamt Dateien: {total_files:,}')
print(f'Gesamt Größe: {total_size_mb/1024:.1f} GB')
print()
print('KATEGORIEN:')
print(f'  Text-Dateien: {text_count:,} ({text_size/1024:.1f} GB)')
print(f'  Medien-Dateien: {media_count:,} ({media_size/1024:.1f} GB)')
print(f'  Andere: {total_files - text_count - media_count:,}')
print()
print('TOP 15 Dateitypen (Anzahl):')
for ext, count in ext_count.most_common(15):
    name = ext if ext else '[none]'
    print(f'  {name}: {count:,}')
print()
print('TOP 15 Dateitypen (Größe GB):')
for ext, size in sorted(ext_size.items(), key=lambda x: x[1], reverse=True)[:15]:
    name = ext if ext else '[none]'
    print(f'  {name}: {size/1024:.2f} GB')

print()
print('='*60)
print('SPEICHER- UND ZEIT-SCHÄTZUNG')
print('='*60)

# Speicher-Schätzung
# Qdrant: ~768 floats * 4 bytes * Anzahl Dokumente = ~3KB pro Doc
# Shadow Ledger: ~1KB pro Datei

qdrant_size_gb = (text_count * 3) / 1024 / 1024  # 3KB pro Text-Doc
ledger_size_gb = (total_files * 1) / 1024 / 1024  # 1KB pro Datei

print(f'Qdrant Vektoren: ~{qdrant_size_gb:.2f} GB (nur Text-Dateien)')
print(f'Shadow Ledger DB: ~{ledger_size_gb:.2f} GB')
print(f'GESAMT geschätzt: ~{qdrant_size_gb + ledger_size_gb:.2f} GB')

print()
print('='*60)
print('ZEIT-SCHÄTZUNG (Ryzen AI 9 HX 370, Ollama Llama3:8b)')
print('='*60)

# Zeit-Schätzung basierend auf Tests
# Text-Dateien: ~35s pro Datei (Tika + Ollama)
# Medien-Dateien: ~2s pro Datei (nur Hash + Metadata)
# Andere: ~1s pro Datei

text_time_h = (text_count * 35) / 3600
media_time_h = (media_count * 2) / 3600
other_time_h = ((total_files - text_count - media_count) * 1) / 3600

print('Verarbeitungszeit pro Kategorie:')
print(f'  Text-Dateien ({text_count:,}): ~{text_time_h:.1f} Stunden')
print(f'  Medien-Dateien ({media_count:,}): ~{media_time_h:.1f} Stunden')
print(f'  Andere Dateien: ~{other_time_h:.1f} Stunden')
print()
print(f'GESAMT SEQUENTIAL: ~{text_time_h + media_time_h + other_time_h:.1f} Stunden')
print(f'                   = {(text_time_h + media_time_h + other_time_h)/24:.1f} Tage')
print()
print('MIT OPTIMIERUNG (4 Worker, kein Ollama für Medien):')
optimized_h = (text_time_h / 2) + (media_time_h / 4) + (other_time_h / 4)
print(f'  Geschätzt: ~{optimized_h:.1f} Stunden = {optimized_h/24:.1f} Tage')
