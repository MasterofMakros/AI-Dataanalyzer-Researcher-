"""
Neural Vault Feedback Tracker
=============================

Erfasst User-Korrekturen an KI-Klassifikationen für kontinuierliches Lernen.

Wenn ein User eine Datei manuell in einen anderen Ordner verschiebt oder
die Kategorie ändert, ist das ein "Roter Knopf" für die ursprüngliche
Klassifikation und wertvolles Feedback.

Übernahme aus Gemini-Analyse vom 2025-12-28.

Usage:
    from utils.feedback_tracker import FeedbackTracker

    tracker = FeedbackTracker()

    # Wenn User eine Datei manuell umkategorisiert
    tracker.log_correction(
        file_hash="abc123...",
        predicted_category="Privat",
        actual_category="Geschäftlich",
        predicted_path="/Privat/Dokumente/",
        actual_path="/Geschäftlich/Rechnungen/"
    )

    # Statistiken abrufen
    stats = tracker.get_correction_stats()
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.paths import DATA_DIR


FEEDBACK_DB_PATH = DATA_DIR / "feedback_tracker.db"


@dataclass
class CorrectionEvent:
    """Ein einzelnes Korrektur-Ereignis."""
    file_hash: str
    filename: str
    predicted_category: str
    actual_category: str
    predicted_path: Optional[str] = None
    actual_path: Optional[str] = None
    predicted_confidence: Optional[float] = None
    correction_type: str = "category"  # category, path, both
    user_comment: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class FeedbackTracker:
    """
    Tracker für User-Korrekturen an KI-Klassifikationen.

    Speichert alle Korrekturen in einer SQLite-Datenbank,
    um später Muster zu erkennen und die Klassifikation zu verbessern.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or FEEDBACK_DB_PATH
        self._init_database()

    def _init_database(self):
        """Initialisiert die Feedback-Datenbank."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Haupttabelle für Korrekturen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT NOT NULL,
                filename TEXT NOT NULL,
                predicted_category TEXT,
                actual_category TEXT,
                predicted_path TEXT,
                actual_path TEXT,
                predicted_confidence REAL,
                correction_type TEXT DEFAULT 'category',
                user_comment TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE
            )
        """)

        # Index für schnelle Abfragen
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_category
            ON corrections(predicted_category, actual_category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_timestamp
            ON corrections(timestamp)
        """)

        # Aggregat-Tabelle für häufige Fehlklassifikationen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predicted_category TEXT NOT NULL,
                actual_category TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                last_seen TEXT,
                UNIQUE(predicted_category, actual_category)
            )
        """)

        conn.commit()
        conn.close()

    def log_correction(
        self,
        file_hash: str,
        filename: str,
        predicted_category: str,
        actual_category: str,
        predicted_path: Optional[str] = None,
        actual_path: Optional[str] = None,
        predicted_confidence: Optional[float] = None,
        user_comment: Optional[str] = None
    ) -> int:
        """
        Protokolliert eine User-Korrektur.

        Args:
            file_hash: SHA-256 Hash der Datei
            filename: Dateiname
            predicted_category: Was die KI vorhergesagt hat
            actual_category: Was der User korrigiert hat
            predicted_path: Ursprünglicher Pfad
            actual_path: Neuer Pfad nach User-Korrektur
            predicted_confidence: Konfidenz der ursprünglichen Vorhersage
            user_comment: Optionaler Kommentar des Users

        Returns:
            ID des Korrektur-Eintrags
        """
        # Bestimme Korrektur-Typ
        if predicted_path and actual_path and predicted_category != actual_category:
            correction_type = "both"
        elif predicted_path and actual_path:
            correction_type = "path"
        else:
            correction_type = "category"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Korrektur einfügen
        cursor.execute("""
            INSERT INTO corrections (
                file_hash, filename, predicted_category, actual_category,
                predicted_path, actual_path, predicted_confidence,
                correction_type, user_comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_hash, filename, predicted_category, actual_category,
            predicted_path, actual_path, predicted_confidence,
            correction_type, user_comment
        ))

        correction_id = cursor.lastrowid

        # Pattern-Tabelle aktualisieren
        cursor.execute("""
            INSERT INTO correction_patterns (predicted_category, actual_category, last_seen)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(predicted_category, actual_category) DO UPDATE SET
                occurrence_count = occurrence_count + 1,
                last_seen = datetime('now')
        """, (predicted_category, actual_category))

        conn.commit()
        conn.close()

        print(f"📝 Korrektur protokolliert: {predicted_category} → {actual_category}")
        return correction_id

    def get_correction_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über alle Korrekturen zurück.

        Returns:
            Dictionary mit Statistiken
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Gesamtzahl
        cursor.execute("SELECT COUNT(*) FROM corrections")
        total = cursor.fetchone()[0]

        # Nach Typ
        cursor.execute("""
            SELECT correction_type, COUNT(*)
            FROM corrections
            GROUP BY correction_type
        """)
        by_type = dict(cursor.fetchall())

        # Häufigste Fehlklassifikationen
        cursor.execute("""
            SELECT predicted_category, actual_category, occurrence_count
            FROM correction_patterns
            ORDER BY occurrence_count DESC
            LIMIT 10
        """)
        top_patterns = [
            {
                "predicted": row[0],
                "actual": row[1],
                "count": row[2]
            }
            for row in cursor.fetchall()
        ]

        # Korrekturen pro Woche
        cursor.execute("""
            SELECT strftime('%Y-W%W', timestamp) as week, COUNT(*)
            FROM corrections
            GROUP BY week
            ORDER BY week DESC
            LIMIT 12
        """)
        by_week = dict(cursor.fetchall())

        # Accuracy-Trend (% korrekt)
        cursor.execute("""
            SELECT
                strftime('%Y-%m', timestamp) as month,
                COUNT(*) as corrections
            FROM corrections
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly_corrections = dict(cursor.fetchall())

        conn.close()

        return {
            "total_corrections": total,
            "by_type": by_type,
            "top_misclassifications": top_patterns,
            "corrections_by_week": by_week,
            "monthly_trend": monthly_corrections
        }

    def get_category_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Erstellt eine Confusion Matrix für Kategorien.

        Returns:
            Nested Dict: confusion[predicted][actual] = count
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT predicted_category, actual_category, COUNT(*)
            FROM corrections
            GROUP BY predicted_category, actual_category
        """)

        confusion = {}
        for row in cursor.fetchall():
            predicted, actual, count = row
            if predicted not in confusion:
                confusion[predicted] = {}
            confusion[predicted][actual] = count

        conn.close()
        return confusion

    def get_files_needing_review(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gibt Dateien zurück, die ähnlich zu korrigierten Dateien sind.

        Basierend auf Pattern-Analyse: Wenn "Privat → Geschäftlich" häufig
        vorkommt, sollten alle "Privat"-Dateien reviewt werden.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Finde häufige Fehlklassifikationsmuster
        cursor.execute("""
            SELECT predicted_category, actual_category, occurrence_count
            FROM correction_patterns
            WHERE occurrence_count >= 3
            ORDER BY occurrence_count DESC
        """)

        patterns = cursor.fetchall()
        conn.close()

        return [
            {
                "problematic_category": p[0],
                "correct_category": p[1],
                "occurrence_count": p[2],
                "suggestion": f"Dateien in '{p[0]}' sollten auf '{p[1]}' geprüft werden"
            }
            for p in patterns
        ]

    def export_for_training(self, output_path: Optional[Path] = None) -> Path:
        """
        Exportiert Korrekturen als JSON für zukünftiges Fine-Tuning.

        Returns:
            Pfad zur Export-Datei
        """
        if output_path is None:
            output_path = DATA_DIR / "correction_export.json"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_hash, filename, predicted_category, actual_category,
                   predicted_confidence, timestamp
            FROM corrections
            ORDER BY timestamp DESC
        """)

        corrections = [
            {
                "file_hash": row[0],
                "filename": row[1],
                "predicted": row[2],
                "actual": row[3],
                "confidence": row[4],
                "timestamp": row[5]
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "total_corrections": len(corrections),
                "corrections": corrections
            }, f, indent=2, ensure_ascii=False)

        print(f"📤 {len(corrections)} Korrekturen exportiert nach {output_path}")
        return output_path


def detect_manual_move(
    file_hash: str,
    old_path: str,
    new_path: str,
    shadow_ledger_path: Optional[Path] = None
) -> Optional[CorrectionEvent]:
    """
    Erkennt, ob ein Dateiwechsel eine manuelle User-Korrektur war.

    Vergleicht mit Shadow Ledger, um festzustellen, ob die Datei
    von der KI an einen anderen Ort gelegt wurde als der User sie jetzt hat.

    Args:
        file_hash: SHA-256 der Datei
        old_path: Ursprünglicher Pfad (wo KI sie hingelegt hat)
        new_path: Neuer Pfad (wo User sie hinverschoben hat)
        shadow_ledger_path: Pfad zur Shadow Ledger DB

    Returns:
        CorrectionEvent wenn Korrektur erkannt, sonst None
    """
    from config.paths import LEDGER_DB_PATH

    ledger_path = shadow_ledger_path or LEDGER_DB_PATH

    if not ledger_path.exists():
        return None

    conn = sqlite3.connect(ledger_path)
    cursor = conn.cursor()

    # Hole Original-Klassifikation
    cursor.execute("""
        SELECT original_filename, category, confidence, current_path
        FROM files
        WHERE sha256 = ?
    """, (file_hash,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    filename, predicted_category, confidence, ledger_path = row

    # Extrahiere Kategorie aus Pfaden (vereinfacht)
    def extract_category_from_path(path: str) -> str:
        """Extrahiert Kategorie aus Ordnerpfad."""
        parts = Path(path).parts
        for part in parts:
            if part.startswith(("Finanzen", "Arbeit", "Privat", "Medien", "Projekte")):
                return part
        return "Sonstiges"

    old_cat = extract_category_from_path(old_path)
    new_cat = extract_category_from_path(new_path)

    # Wenn Kategorie sich geändert hat → Korrektur
    if old_cat != new_cat:
        return CorrectionEvent(
            file_hash=file_hash,
            filename=filename,
            predicted_category=old_cat,
            actual_category=new_cat,
            predicted_path=old_path,
            actual_path=new_path,
            predicted_confidence=confidence,
            correction_type="both"
        )

    return None


# Beispiel-Nutzung
if __name__ == "__main__":
    tracker = FeedbackTracker()

    # Simuliere einige Korrekturen
    tracker.log_correction(
        file_hash="abc123",
        filename="Rechnung_Test.pdf",
        predicted_category="Privat",
        actual_category="Geschäftlich",
        predicted_confidence=0.75
    )

    tracker.log_correction(
        file_hash="def456",
        filename="Vertrag_XY.pdf",
        predicted_category="Dokumente",
        actual_category="Geschäftlich",
        predicted_confidence=0.82
    )

    # Statistiken ausgeben
    stats = tracker.get_correction_stats()
    print("\n📊 Korrektur-Statistiken:")
    print(f"   Gesamt: {stats['total_corrections']}")
    print(f"   Nach Typ: {stats['by_type']}")
    print(f"\n   Top Fehlklassifikationen:")
    for p in stats['top_misclassifications']:
        print(f"      {p['predicted']} → {p['actual']}: {p['count']}x")

    # Review-Empfehlungen
    review = tracker.get_files_needing_review()
    if review:
        print("\n⚠️ Review-Empfehlungen:")
        for r in review:
            print(f"   {r['suggestion']}")
