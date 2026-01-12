import csv
import collections
import os

INPUT_FILE = r"F:\conductor\scripts\f_drive_index.csv"
OUTPUT_REPORT = r"F:\conductor\scripts\index_analysis_report.txt"

def analyze_csv():
    print("Starte Analyse...")
    
    stats_ext_count = collections.Counter()
    stats_ext_size = collections.Counter()
    
    large_files = [] # Files > 2GB
    deep_paths = [] # Depth > 10
    red_flags = [] # "backup", "copy", "rechnung", etc.
    
    red_flag_keywords = ["backup", "kopie", "copy", "sync", "old", "alt", "archiv", "dump", "temp"]
    
    total_files = 0
    total_size_mb = 0
    
    with open(INPUT_FILE, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_files += 1
            
            # 1. Extension Stats
            ext = row['Extension'].lower()
            if not ext:
                ext = "[no_extension]"
            
            try:
                size_mb = float(row['Size_MB'])
            except ValueError:
                size_mb = 0.0
                
            stats_ext_count[ext] += 1
            stats_ext_size[ext] += size_mb
            total_size_mb += size_mb
            
            # 2. Red Flags (Large Files)
            if size_mb > 2000: # > 2GB
                large_files.append((row['Filename'], size_mb, row['Path']))
            
            # 3. Depth
            try:
                depth = int(row['Depth'])
                if depth > 10:
                    deep_paths.append((row['Path'], depth))
            except ValueError:
                pass
                
            # 4. Keyword Flags
            fname_lower = row['Filename'].lower()
            for kw in red_flag_keywords:
                if kw in fname_lower:
                    red_flags.append(row['Filename'])
                    break
                    
    # Generate Report
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as out:
        out.write(f"=== ANALYSE BERICHT ===\n")
        out.write(f"Total Files: {total_files}\n")
        out.write(f"Total Size: {total_size_mb/1024:.2f} GB\n\n")
        
        out.write("TOP 20 EXTENSIONS (BY COUNT):\n")
        for ext, count in stats_ext_count.most_common(20):
            out.write(f"{ext}: {count}\n")
            
        out.write("\nTOP 20 EXTENSIONS (BY SIZE MB):\n")
        # Sort by value desc
        sorted_size = sorted(stats_ext_size.items(), key=lambda item: item[1], reverse=True)[:20]
        for ext, size in sorted_size:
            out.write(f"{ext}: {size:.2f} MB\n")
            
        out.write("\nLARGE FILES (>2GB) - TOP 20:\n")
        # Sort large files by size desc
        large_files.sort(key=lambda x: x[1], reverse=True)
        for name, size, path in large_files[:20]:
            out.write(f"{name} ({size:.2f} MB) - {path}\n")
            
        out.write(f"\nRED FL FILES DETECTED (Sample): {len(red_flags)}\n")
        for f in red_flags[:20]:
            out.write(f"{f}\n")

    print(f"Analyse fertig! Bericht unter {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_csv()
