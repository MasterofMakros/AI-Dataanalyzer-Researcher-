"""
Topic Modeling Service using BERTopic (Step 3)
Discover hidden themes in the _Inbox
"""

import os
from pathlib import Path
from typing import List, Dict
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

# Konfiguration
from config.paths import INBOX_DIR, BASE_DIR

INBOX_PATH = INBOX_DIR
MODEL_PATH = BASE_DIR / "models" / "bertopic_v1"

class TopicModeler:
    def __init__(self):
        # Wir nutzen ein Standard-BERTopic Modell (nutzt standardmäßig all-MiniLM-L6-v2)
        # Für Deutsch/Multilingual wäre 'paraphrase-multilingual-MiniLM-L12-v2' besser
        self.model = BERTopic(language="multilingual")
        
    def load_documents(self, directory: Path, extensions: List[str] = [".txt", ".md"]) -> List[str]:
        """Lädt Textdokumente aus einem Verzeichnis."""
        docs = []
        filenames = []
        for ext in extensions:
            for filepath in directory.glob(f"*{ext}"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        if len(text.strip()) > 50: # Min length
                            docs.append(text)
                            filenames.append(filepath.name)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
        return docs, filenames

    def fit_transform(self, docs: List[str]):
        """Trainiert das Modell auf den Dokumenten."""
        if not docs:
            print("Keine Dokumente gefunden.")
            return None, None
            
        print(f"Trainiere BERTopic auf {len(docs)} Dokumenten...")
        topics, probs = self.model.fit_transform(docs)
        return topics, probs

    def get_topic_info(self):
        """Gibt Topic-Info zurück."""
        return self.model.get_topic_info()

    def visuals(self):
        """Erzeugt Visualisierungen (HTML)."""
        return self.model.visualize_topics()

if __name__ == "__main__":
    print("Starte Topic Modeling Service...")
    modeler = TopicModeler()
    
    # Test-Lauf auf _Inbox
    docs, files = modeler.load_documents(INBOX_PATH)
    
    if docs:
        topics, _ = modeler.fit_transform(docs)
        info = modeler.get_topic_info()
        print("\nGefundene Themen:")
        print(info.head(10))
        
        # Speichern
        # modeler.model.save(MODEL_PATH)
    else:
        print("Abbruch: Zu wenige Dokumente in _Inbox.")
