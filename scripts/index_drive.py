import os
import csv
import time
from config.paths import BASE_DIR, SCRIPTS_DIR

# KONFIGURATION
SOURCE_DRIVE = "F:/"  # Dein Laufwerk
OUTPUT_FILE = str(SCRIPTS_DIR / "f_drive_index.csv")
MAX_ROWS = 50000  # Begrenzung für Gemini (Splittet Datei wenn nötig)

def create_index():
    print(f"Starte Indexierung von {SOURCE_DRIVE}...")
    start_time = time.time()
    
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Path', 'Filename', 'Extension', 'Size_MB', 'Depth']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        row_count = 0
        
        for root, dirs, files in os.walk(SOURCE_DRIVE):
            # Berechne Ordnertiefe
            depth = root[len(SOURCE_DRIVE):].count(os.sep)
            
            for name in files:
                try:
                    file_path = os.path.join(root, name)
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    _, ext = os.path.splitext(name)
                    
                    writer.writerow({
                        'Path': root.replace(SOURCE_DRIVE, ""), # Anonymisierter Pfad
                        'Filename': name,
                        'Extension': ext.lower(),
                        'Size_MB': round(file_size_mb, 2),
                        'Depth': depth
                    })
                    
                    row_count += 1
                    if row_count % 10000 == 0:
                        print(f"{row_count} Dateien indexiert...")
                        
                except Exception as e:
                    # Fehler bei Zugriff (z.B. Systemdateien) ignorieren
                    continue

    print(f"Fertig! {row_count} Dateien in {round(time.time() - start_time, 2)} Sekunden indexiert.")
    print(f"Datei gespeichert unter: {OUTPUT_FILE}")

if __name__ == "__main__":
    create_index()
