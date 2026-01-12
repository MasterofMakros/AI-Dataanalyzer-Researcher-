
"""
Test for ABT-N02: Data Narrator
Verifies that CSV/Excel files are correctly converted to Markdown narratives.
"""
import pandas as pd
import sys
from pathlib import Path

# Add project root
sys.path.append("F:/conductor")

from scripts.experimental.data_narrator import narrate_table

def test_narrator():
    print("🧪 Generiere Test-Daten...")
    
    # 1. Create Dummy CSV
    data = {
        "Datum": ["2024-01-01", "2024-01-02", "2024-03-15", "2024-06-20"],
        "Kategorie": ["Einnahme", "Ausgabe", "Ausgabe", "Einnahme"],
        "Betrag": [5000.00, -120.50, -45.99, 250.00],
        "Beschreibung": ["Gehalt", "Supermarkt", "Tankstelle", "Flohmarkt Verkauf"]
    }
    df = pd.DataFrame(data)
    df["Datum"] = pd.to_datetime(df["Datum"])
    
    test_csv = Path("F:/_TestPool/test_finance.csv")
    test_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(test_csv, index=False)
    
    print(f"✅ CSV erstellt: {test_csv}")
    
    # 2. Run Narrator
    print("\n📝 Running Data Narrator...")
    try:
        markdown = narrate_table(df, str(test_csv))
        
        print("\n--- GENERATED MARKDOWN START ---")
        print(markdown)
        print("--- GENERATED MARKDOWN END ---\n")
        
        # 3. Validation Checks
        checks = []
        checks.append(("Zeilen count correct", "Zeilen:** 4" in markdown))
        checks.append(("Sum correct", "Summe=5083.51" in markdown or "Summe=5083.5" in markdown)) # 5000+250 - 120.5 - 45.99 = 5083.51
        checks.append(("Date range correct", "Von 2024-01-01" in markdown))
        checks.append(("Table preview present", "| Datum" in markdown))
        
        print("🔍 Verification:")
        all_passed = True
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
            if not passed: all_passed = False
            
        if all_passed:
            print("\n🎉 Test ABT-N02 PASSED!")
        else:
            print("\n🔥 Test ABT-N02 FAILED.")
            
    except Exception as e:
        print(f"❌ Error during narration: {e}")

if __name__ == "__main__":
    test_narrator()
