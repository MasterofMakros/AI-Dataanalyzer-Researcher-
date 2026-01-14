
import time
import os
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

# Target File
from config.paths import INBOX_DIR, DATA_DIR, LEDGER_DB_PATH, BASE_DIR

FILE_PATH = str(INBOX_DIR / "Einnahmen_Überschussrechnung_für_Dummies_Das_Pocketbuch_(German_Edition).pdf")
# Note: The find script output "original_path" is likely inside INBOX_DIR or similar.
# I will use a simpler file from the dataset if that one is hard to locate,
# but for now, let's assume I can find one file.
# Actually, I'll grab the first file from the DB to be safe.

HOST_URL = "http://localhost:8002"  # docling-service

import sqlite3

with sqlite3.connect(LEDGER_DB_PATH) as conn:
    row = conn.execute(
        "SELECT original_path FROM files WHERE original_filename LIKE '%.pdf' LIMIT 1"
    ).fetchone()

if row:
    FILE_PATH = row[0]

print(f"📄 Benchmarking on: {FILE_PATH}")

def bench_pymupdf(path):
    start = time.time()
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    end = time.time()
    return end - start, len(text)

def bench_docling(path):
    start = time.time()
    converter = DocumentConverter()
    result = converter.convert(path)
    md = result.document.export_to_markdown()
    end = time.time()
    return end - start, len(md), md

print(f"\n🥊 ROUND 1: PyMuPDF (The Incumbent)")
t_mu, len_mu = bench_pymupdf(FILE_PATH)
print(f"   Speed: {t_mu:.4f}s")
print(f"   Chars: {len_mu}")

print(f"\n🥊 ROUND 2: Docling (The Challenger)")
try:
    t_doc, len_doc, md_content = bench_docling(FILE_PATH)
    print(f"   Speed: {t_doc:.4f}s")
    print(f"   Chars: {len_doc}")
    
    ratio = t_doc / t_mu
    print(f"\n📊 Result: Docling is {ratio:.1f}x slower but extracted {len_doc} chars.")
    
    # Save Output
    out_file = "F:/conductor/data/docling_sample.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"💾 Saved Deep Extract to {out_file}")
    
except Exception as e:
    print(f"❌ Docling Failed: {e}")
