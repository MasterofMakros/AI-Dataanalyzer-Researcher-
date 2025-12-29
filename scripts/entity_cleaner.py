"""
Entity Cleaner (Fuzzy Logic)
Identifies and merges duplicate entities in the Knowledge Graph / Metadata Layer.
ABT-N01 Implementation.
"""
import sys
import sqlite3
import json
import difflib
from pathlib import Path
from collections import defaultdict

# Add project root
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.paths import LEDGER_DB_PATH

def get_entities():
    """Fetch structured entities from Ledger."""
    conn = sqlite3.connect(str(LEDGER_DB_PATH))
    # Try different tables/columns as fallback
    try:
        # Strategy A: 'files' table
        cursor = conn.execute("SELECT id, extracted_entities FROM files WHERE extracted_entities IS NOT NULL AND extracted_entities != ''")
    except sqlite3.OperationalError:
        try:
            # Strategy B: 'filesystem_entry' table (uses path as ID usually)
            cursor = conn.execute("SELECT path, status FROM filesystem_entry") # Fallback just to list
            print("  ⚠️ Column 'extracted_entities' not found. Scanning filenames instead.")
            # Mock structure for filename analysis
            data = [(row[0], json.dumps({'vendor': Path(row[0]).parent.name})) for row in cursor.fetchall()]
            conn.close()
            return data
        except Exception as e:
            print(f"Error querying ledger: {e}")
            return []
    data = cursor.fetchall()
    conn.close()
    return data

def find_duplicates(entities, threshold=0.85):
    """Cluster strings by similarity."""
    clusters = defaultdict(list)
    processed = set()
    
    # Extract just the names/values we care about (e.g. 'sender', 'vendor')
    # This assumes entities are JSON: {'vendor': 'Amazon', 'date': ...}
    
    unique_names = set()
    name_to_ids = defaultdict(list)
    
    for doc_id, ent_json in entities:
        try:
            ent = json.loads(ent_json)
            # Focus on Vendor/Sender for now
            name = ent.get('sender') or ent.get('vendor') or ent.get('organization')
            if name:
                clean_name = name.strip()
                unique_names.add(clean_name)
                name_to_ids[clean_name].append(doc_id)
        except:
            continue
            
    sorted_names = sorted(list(unique_names))
    
    print(f"Analyzing {len(sorted_names)} unique entity names...")
    
    merges = []
    
    for i, name1 in enumerate(sorted_names):
        if name1 in processed:
            continue
            
        cluster = [name1]
        processed.add(name1)
        
        for name2 in sorted_names[i+1:]:
            if name2 in processed:
                continue
                
            # Quick check: First char match often helps performance
            if name1[0].lower() != name2[0].lower():
                continue
                
            similarity = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            
            if similarity >= threshold:
                cluster.append(name2)
                processed.add(name2)
        
        if len(cluster) > 1:
            merges.append(cluster)
            
    return merges

def main():
    print("🧹 Starting Entity Cleanup (Dry Run)...")
    
    # 1. Load Data
    raw_data = get_entities()
    print(f"loaded {len(raw_data)} records with entities.")
    
    # 2. Analyze
    merges = find_duplicates(raw_data)
    
    # 3. Report
    print(f"\nFound {len(merges)} potential entity clusters:\n")
    
    for cluster in merges:
        # Determine strict "Winner" (shortest or longest? usually most frequent, but here just longest)
        winner = max(cluster, key=len)
        print(f"🔗 Cluster: {cluster}")
        print(f"   ↳ Suggest merging into: '{winner}'")
        print("-" * 30)
        
    print("\n✅ Analysis Complete. Run with --apply to execute merges (Not implemented in Pilot).")

if __name__ == "__main__":
    main()
