"""
Neural Vault Quality Gates - Phase 2
6 automatische Prüfungen vor File-Move

Usage:
    from quality_gates import run_quality_gates
    result = run_quality_gates(file_data)
"""

import os
import re
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

@dataclass
class GateResult:
    """Ergebnis eines einzelnen Quality Gates."""
    gate_name: str
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"

@dataclass
class QualityResult:
    """Gesamtergebnis aller Quality Gates."""
    passed: bool
    gates: List[GateResult]
    quarantine_reason: str = ""
    quarantine_folder: str = ""

# Konfiguration
CONFIDENCE_THRESHOLD = 0.7
LOW_CONFIDENCE_THRESHOLD = 0.5

VALID_CATEGORIES = {
    "Finanzen", "Arbeit", "Privat", "Medien", "Dokumente", 
    "Technologie", "Gesundheit", "Reisen", "Sonstiges"
}

CATEGORY_MIME_MAP = {
    "Finanzen": ["application/pdf", "image/", "text/"],
    "Medien": ["image/", "video/", "audio/"],
    "Dokumente": ["application/pdf", "application/msword", "application/vnd.", "text/"],
}

from config.paths import ARCHIVE_DIR, BASE_DIR, LEDGER_DB_PATH, QUARANTINE_DIR

# Shadow Ledger alias for legacy naming.
SHADOW_LEDGER_PATH = LEDGER_DB_PATH

def gate_category_plausibility(data: Dict[str, Any]) -> GateResult:
    """
    Gate 1: CATEGORY_PLAUSIBILITY
    Prüft ob die KI-Kategorie zum MIME-Type passt.
    """
    category = data.get("category", "").split("|")[0].strip()
    mime_type = data.get("mime_type", "application/octet-stream")
    
    # Kategorie muss in der Liste sein
    if category not in VALID_CATEGORIES:
        return GateResult(
            gate_name="CATEGORY_PLAUSIBILITY",
            passed=False,
            message=f"Ungültige Kategorie: {category}",
            severity="error"
        )
    
    # MIME-Type Check (optional, nur Warnung)
    if category in CATEGORY_MIME_MAP:
        valid_mimes = CATEGORY_MIME_MAP[category]
        if not any(mime_type.startswith(m) for m in valid_mimes):
            return GateResult(
                gate_name="CATEGORY_PLAUSIBILITY",
                passed=True,  # Nur Warnung
                message=f"MIME-Type {mime_type} ungewöhnlich für Kategorie {category}",
                severity="warning"
            )
    
    return GateResult(
        gate_name="CATEGORY_PLAUSIBILITY",
        passed=True,
        message=f"Kategorie {category} plausibel",
        severity="info"
    )

def gate_filename_quality(data: Dict[str, Any]) -> GateResult:
    """
    Gate 2: FILENAME_QUALITY
    Prüft ob der neue Dateiname dem Schema entspricht.
    Format: YYYY-MM-DD_Kategorie_Entity_Description.ext
    """
    new_filename = data.get("new_filename", "")
    
    if not new_filename:
        return GateResult(
            gate_name="FILENAME_QUALITY",
            passed=False,
            message="Kein neuer Dateiname generiert",
            severity="error"
        )
    
    # Regex für das Schema (gelockert)
    # Format: YYYY-MM-DD_Kategorie_Entity.ext (Entity kann _, - und Zahlen enthalten)
    pattern = r"^\d{4}-\d{2}-\d{2}_[A-Za-zäöüÄÖÜß]+_[\w\-]+\.[a-z0-9]+$"
    
    if not re.match(pattern, new_filename, re.IGNORECASE):
        return GateResult(
            gate_name="FILENAME_QUALITY",
            passed=True,  # Nur Warnung, nicht blockieren
            message=f"Dateiname-Schema nicht optimal: {new_filename}",
            severity="warning"
        )
    
    # Keine Sonderzeichen außer _ und -
    forbidden = set('<>:"/\\|?*')
    if any(c in new_filename for c in forbidden):
        return GateResult(
            gate_name="FILENAME_QUALITY",
            passed=False,
            message=f"Ungültige Zeichen im Dateinamen: {new_filename}",
            severity="error"
        )
    
    return GateResult(
        gate_name="FILENAME_QUALITY",
        passed=True,
        message=f"Dateiname valide: {new_filename}",
        severity="info"
    )

def gate_target_folder_valid(data: Dict[str, Any]) -> GateResult:
    """
    Gate 3: TARGET_FOLDER_VALID
    Prüft ob der Zielordner existiert oder erstellt werden kann.
    """
    target_folder = data.get("target_folder", "")
    
    if not target_folder:
        return GateResult(
            gate_name="TARGET_FOLDER_VALID",
            passed=False,
            message="Kein Zielordner definiert",
            severity="error"
        )
    
    target_path = Path(target_folder)
    
    # Optional: Check if path is absolute or within allowed roots
    # if not str(target_path).startswith(str(ARCHIVE_DIR)): ...
    # For now, just ensure it is not empty
    if not target_path.is_absolute():
        return GateResult(
            gate_name="TARGET_FOLDER_VALID",
            passed=False,
            message=f"Zielordner kein absoluter Pfad: {target_folder}",
            severity="error"
        )
    
    # Ordner existiert oder kann erstellt werden
    if target_path.exists() or target_path.parent.exists():
        return GateResult(
            gate_name="TARGET_FOLDER_VALID",
            passed=True,
            message=f"Zielordner valide: {target_folder}",
            severity="info"
        )
    
    return GateResult(
        gate_name="TARGET_FOLDER_VALID",
        passed=False,
        message=f"Zielordner nicht erreichbar: {target_folder}",
        severity="error"
    )

def gate_no_collision(data: Dict[str, Any]) -> GateResult:
    """
    Gate 4: NO_COLLISION
    Prüft ob am Zielort bereits eine gleichnamige Datei existiert.
    """
    target_folder = data.get("target_folder", "")
    new_filename = data.get("new_filename", "")
    
    if not target_folder or not new_filename:
        return GateResult(
            gate_name="NO_COLLISION",
            passed=False,
            message="Zielordner oder Dateiname fehlt",
            severity="error"
        )
    
    target_path = Path(target_folder) / new_filename
    
    if target_path.exists():
        return GateResult(
            gate_name="NO_COLLISION",
            passed=False,
            message=f"Datei existiert bereits: {target_path}",
            severity="error"
        )
    
    return GateResult(
        gate_name="NO_COLLISION",
        passed=True,
        message="Kein Namenskonflikt",
        severity="info"
    )

def gate_confidence_threshold(data: Dict[str, Any]) -> GateResult:
    """
    Gate 5: CONFIDENCE_THRESHOLD
    Prüft ob die KI-Konfidenz über dem Schwellenwert liegt.
    """
    confidence = data.get("confidence", 0.0)
    
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return GateResult(
            gate_name="CONFIDENCE_THRESHOLD",
            passed=False,
            message=f"Konfidenz zu niedrig: {confidence:.0%} (Min: {LOW_CONFIDENCE_THRESHOLD:.0%})",
            severity="error"
        )
    
    if confidence < CONFIDENCE_THRESHOLD:
        return GateResult(
            gate_name="CONFIDENCE_THRESHOLD",
            passed=True,  # Warnung, aber durchlassen
            message=f"Konfidenz unter Optimal: {confidence:.0%} (Empfohlen: {CONFIDENCE_THRESHOLD:.0%})",
            severity="warning"
        )
    
    return GateResult(
        gate_name="CONFIDENCE_THRESHOLD",
        passed=True,
        message=f"Konfidenz ausreichend: {confidence:.0%}",
        severity="info"
    )

def gate_content_extracted(data: Dict[str, Any]) -> GateResult:
    """
    Gate 6: CONTENT_EXTRACTED
    Prüft ob Text/Metadaten extrahiert wurden.
    """
    extracted_text = data.get("extracted_text", "")
    meta_description = data.get("meta_description", "")
    
    # Mindestens eines muss vorhanden sein
    if not extracted_text and not meta_description:
        return GateResult(
            gate_name="CONTENT_EXTRACTED",
            passed=False,
            message="Weder Text noch Beschreibung extrahiert",
            severity="error"
        )
    
    # Warnung bei sehr kurzem Text
    if len(extracted_text) < 50 and len(meta_description) < 20:
        return GateResult(
            gate_name="CONTENT_EXTRACTED",
            passed=True,
            message=f"Wenig Content extrahiert ({len(extracted_text)} Zeichen)",
            severity="warning"
        )
    
    return GateResult(
        gate_name="CONTENT_EXTRACTED",
        passed=True,
        message=f"Content extrahiert ({len(extracted_text)} Zeichen)",
        severity="info"
    )

def check_duplicate(sha256: str) -> Tuple[bool, str]:
    """
    Prüft ob ein Duplikat in der Shadow Ledger existiert.
    Returns: (is_duplicate, original_path)
    """
    if not SHADOW_LEDGER_PATH.exists():
        return False, ""
    
    try:
        conn = sqlite3.connect(SHADOW_LEDGER_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_path FROM files WHERE sha256 = ? LIMIT 1",
            (sha256,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return True, row[0]
    except Exception:
        pass
    
    return False, ""

def run_quality_gates(data: Dict[str, Any]) -> QualityResult:
    """
    Führt alle 6 Quality Gates aus.
    
    Args:
        data: Dict mit folgenden Keys:
            - sha256: Hash der Datei
            - original_filename: Ursprünglicher Name
            - new_filename: Generierter neuer Name
            - target_folder: Zielordner
            - category: KI-Kategorie
            - confidence: KI-Konfidenz (0.0-1.0)
            - mime_type: MIME-Type
            - extracted_text: Extrahierter Text
            - meta_description: KI-Beschreibung
    
    Returns:
        QualityResult mit passed, gates, quarantine_reason, quarantine_folder
    """
    gates = [
        gate_category_plausibility(data),
        gate_filename_quality(data),
        gate_target_folder_valid(data),
        gate_no_collision(data),
        gate_confidence_threshold(data),
        gate_content_extracted(data),
    ]
    
    # Duplikat-Check (Bonus)
    sha256 = data.get("sha256", "")
    if sha256:
        is_dup, original_path = check_duplicate(sha256)
        if is_dup:
            gates.append(GateResult(
                gate_name="DUPLICATE_CHECK",
                passed=False,
                message=f"Duplikat von: {original_path}",
                severity="error"
            ))
    
    # Ergebnis berechnen
    errors = [g for g in gates if not g.passed]
    warnings = [g for g in gates if g.passed and g.severity == "warning"]
    
    if errors:
        # Quarantine bestimmen
        first_error = errors[0]
        if "Duplikat" in first_error.message:
            quarantine_folder = str(QUARANTINE_DIR / "_duplicates")
        elif "Konfidenz" in first_error.message:
            quarantine_folder = str(QUARANTINE_DIR / "_low_confidence")
        else:
            quarantine_folder = str(QUARANTINE_DIR / "_review_needed")
        
        return QualityResult(
            passed=False,
            gates=gates,
            quarantine_reason=first_error.message,
            quarantine_folder=quarantine_folder
        )
    
    return QualityResult(
        passed=True,
        gates=gates,
        quarantine_reason="",
        quarantine_folder=""
    )

def generate_smart_filename(
    original_filename: str,
    category: str,
    entity: str = "",
    date: str = ""
) -> str:
    """
    Generiert einen Smart Filename nach dem Schema.
    
    Format: YYYY-MM-DD_Kategorie_Entity_Original.ext
    """
    # Datum bestimmen
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Extension
    ext = Path(original_filename).suffix.lower()
    
    # Entity bereinigen
    if not entity:
        entity = Path(original_filename).stem
    entity = re.sub(r'[<>:"/\\|?*\s]+', '_', entity)[:30]
    
    # Kategorie bereinigen (nur erstes Wort)
    cat_clean = category.split("|")[0].split("/")[0].strip()
    cat_clean = re.sub(r'[<>:"/\\|?*\s]+', '', cat_clean)
    
    return f"{date}_{cat_clean}_{entity}{ext}"

def determine_target_folder(category: str, subcategory: str = "") -> str:
    """
    Bestimmt den Zielordner basierend auf Kategorie.
    """
    base = str(ARCHIVE_DIR)
    
    folder_map = {
        "Finanzen": f"{base}/Finanzen",
        "Arbeit": f"{base}/Arbeit",
        "Privat": f"{base}/Privat",
        "Medien": f"{base}/Medien",
        "Dokumente": f"{base}/Dokumente",
        "Technologie": f"{base}/Technologie",
        "Gesundheit": f"{base}/Gesundheit",
        "Reisen": f"{base}/Reisen",
        "Sonstiges": f"{base}/Sonstiges",
    }
    
    cat_clean = category.split("|")[0].split("/")[0].strip()
    return folder_map.get(cat_clean, f"{base}/Sonstiges")


if __name__ == "__main__":
    # Test
    test_data = {
        "sha256": "abc123",
        "original_filename": "Rechnung_Bauhaus.pdf",
        "new_filename": "2024-12-26_Finanzen_Bauhaus_Gartenmaterial.pdf",
        "target_folder": str(ARCHIVE_DIR / "Finanzen"),
        "category": "Finanzen",
        "confidence": 0.85,
        "mime_type": "application/pdf",
        "extracted_text": "Bauhaus Rechnung über 127,50 EUR für Gartenmaterial...",
        "meta_description": "Bauhaus Rechnung für Gartenzubehör vom Dezember 2024"
    }
    
    result = run_quality_gates(test_data)
    print(f"\n{'✅ PASSED' if result.passed else '❌ FAILED'}")
    print("\nGates:")
    for gate in result.gates:
        icon = "✅" if gate.passed else "❌"
        print(f"  {icon} {gate.gate_name}: {gate.message}")
    
    if not result.passed:
        print(f"\n📁 Quarantine: {result.quarantine_folder}")
        print(f"   Grund: {result.quarantine_reason}")
