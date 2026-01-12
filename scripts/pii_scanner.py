"""
PII Scanner Service using GLiNER (Step 4)
Detects IBANs, Person Names, and other PII in documents.
"""

import sys
from pathlib import Path
from gliner import GLiNER

# Konfiguration
MODEL_NAME = "urchade/gliner_medium-v2.1"
LABELS = ["person", "iban", "date", "address", "organization"]

class PIIScanner:
    def __init__(self):
        print(f"Lade GLiNER Modell: {MODEL_NAME}...")
        self.model = GLiNER.from_pretrained(MODEL_NAME)
        
    def scan_text(self, text: str):
        """Scannt Text nach PII und gibt Entities zurück."""
        entities = self.model.predict_entities(text, LABELS, threshold=0.5)
        return entities

    def scan_file(self, filepath: Path):
        """Scannt eine Datei (Text)."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            return self.scan_text(text)
        except Exception as e:
            print(f"Fehler beim Lesen von {filepath}: {e}")
            return []

if __name__ == "__main__":
    print("Starte PII Scanner...")
    scanner = PIIScanner()
    
    # Test-Scan
    print("\nTeste mit Dummy-Daten (Deutsche IBAN)...")
    sample_text = """
    Hallo, mein Name ist Max Mustermann. 
    Bitte überweisen Sie das Geld auf mein Konto: DE12 3456 7890 1234 5678 90 bei der Sparkasse.
    Ich wohne in der Musterstraße 123, 12345 Berlin.
    """
    
    entities = scanner.scan_text(sample_text)
    
    print("\nGefundene PII:")
    for ent in entities:
        print(f"- {ent['label']}: {ent['text']} ({ent['score']:.2f})")
