import csv
from config.paths import SCRIPTS_DIR

CSV_FILE = SCRIPTS_DIR / 'f_drive_index.csv'
with open(CSV_FILE, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    print("Spalten:", list(next(csv.reader(open(CSV_FILE, 'r', encoding='utf-8')))))
    f.seek(0)
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i < 3:
            print(f"\nZeile {i+1}:")
            for key, val in row.items():
                print(f"  {key}: {val[:80] if val else 'N/A'}")
        else:
            break
