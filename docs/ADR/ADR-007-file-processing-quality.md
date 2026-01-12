# ADR-007: Universelle Dateiverarbeitung & Qualitätssicherung

## Status
**Akzeptiert** (2025-12-26)

## Kontext und Problemstellung

Der `_Inbox` Ordner empfängt Dateien **jeder erdenklichen Art** von verschiedenen Geräten (Handy, Tablet, Laptop). Das System muss:

1. **Jeden Dateityp verarbeiten können** (oder sicher scheitern)
2. **Plausibilitätsprüfungen durchführen** (War die Klassifizierung sinnvoll?)
3. **Fehler transparent behandeln** (Keine Dateien "verschwinden")

---

## Entscheidung

### 1. Universelle Dateitypmatrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATEI EINGANG (_Inbox)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Dateityp-Erkennung (Apache Tika)                               │
│  → MIME-Type, Extension, Magic Bytes                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ DOKUMENTE │   │  MEDIEN   │   │ ANDERE    │
            │ PDF,DOCX  │   │ JPG,MP4   │   │ ZIP,EXE   │
            │ TXT,HTML  │   │ PNG,MP3   │   │ ISO,CAD   │
            └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
                  │               │               │
                  ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ OCR/Parse │   │ EXIF/Meta │   │ Hash Only │
            │ Surya,Tika│   │ CLIP,EXIF │   │ Kategorie │
            └───────────┘   └───────────┘   └───────────┘
                  │               │               │
                  └───────────────┴───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: KI-Klassifizierung (Ollama)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Plausibilitätsprüfung                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ ✅ PASSED │   │ ⚠️ REVIEW │   │ ❌ FAILED │
            │ Auto-Move │   │ Telegram  │   │ Quarantäne│
            └───────────┘   └───────────┘   └───────────┘
```

### 2. Dateitypmatrix mit Verarbeitungsstrategie

| Kategorie | Dateitypen | Verarbeitungsstrategie | Fallback |
| :--- | :--- | :--- | :--- |
| **📄 Dokumente** | PDF, DOCX, DOC, ODT, TXT, RTF, XLS, XLSX, PPT, PPTX | Tika → Text Extract → Surya OCR (wenn Scan) → LLM | Nur Metadaten |
| **📧 E-Mail** | EML, MSG, MBOX | Tika → Header + Body Extract → Index | Als Text speichern |
| **🖼️ Bilder** | JPG, PNG, GIF, WEBP, HEIC, TIFF, BMP | EXIF → CLIP Embedding → LLaVA Beschreibung | Nur EXIF + Hash |
| **🎥 Video** | MP4, MKV, AVI, MOV, WEBM | EXIF → Thumbnail → Whisper (Audio) → CLIP (Frames) | Nur Metadaten |
| **🎵 Audio** | MP3, WAV, FLAC, OGG, M4A | ID3 Tags → Whisper Transkription | Nur Metadaten |
| **📦 Archive** | ZIP, RAR, 7Z, TAR, GZ | Liste Inhalt → Extrahiere für separate Verarbeitung | Nur Index der Inhalte |
| **💻 Code** | PY, JS, TS, HTML, CSS, JSON, XML, MD | Syntax-Highlighting → Sprache erkennen | Als Text |
| **🔧 System** | EXE, DLL, ISO, DMG, APK | NUR Hash + Metadaten (keine Ausführung!) | Nur Hash |
| **❓ Unbekannt** | Alles andere | Hash + MIME-Type + Extension | In "Unsortiert" |

### 3. Plausibilitätsprüfungen (Quality Gates)

Jede verarbeitete Datei durchläuft diese Prüfungen:

```python
class QualityGates:
    """
    Plausibilitätsprüfungen für verarbeitete Dateien.
    Alle Prüfungen müssen bestanden werden, sonst → Review Queue.
    """
    
    def check_all(self, file_metadata: dict) -> tuple[bool, list[str]]:
        """Führt alle Prüfungen durch. Returns (passed, [errors])"""
        errors = []
        
        # Gate 1: Kategorie-Plausibilität
        if not self.check_category_plausibility(file_metadata):
            errors.append("CATEGORY_MISMATCH")
        
        # Gate 2: Dateiname-Qualität
        if not self.check_filename_quality(file_metadata):
            errors.append("FILENAME_QUALITY")
        
        # Gate 3: Zielordner existiert
        if not self.check_target_folder_valid(file_metadata):
            errors.append("INVALID_TARGET")
        
        # Gate 4: Keine Duplikate am Ziel
        if not self.check_no_collision(file_metadata):
            errors.append("NAME_COLLISION")
        
        # Gate 5: Konfidenz-Schwellenwert
        if not self.check_confidence_threshold(file_metadata):
            errors.append("LOW_CONFIDENCE")
        
        # Gate 6: Inhalt nicht leer
        if not self.check_content_extracted(file_metadata):
            errors.append("EMPTY_CONTENT")
        
        passed = len(errors) == 0
        return passed, errors
    
    def check_category_plausibility(self, meta: dict) -> bool:
        """Prüft ob Kategorie zum MIME-Type passt."""
        mime = meta.get('content_type', '')
        category = meta.get('category', '')
        
        # Beispiel: Ein Video sollte nicht als "Rechnung" klassifiziert werden
        if mime.startswith('video/') and category in ['Rechnung', 'Kontoauszug', 'Vertrag']:
            return False
        
        # Ein PDF mit "Invoice" im Text sollte als Rechnung erkannt werden
        if 'invoice' in meta.get('extracted_text', '').lower() and category != 'Rechnung':
            return False
            
        return True
    
    def check_filename_quality(self, meta: dict) -> bool:
        """Prüft ob der generierte Dateiname sinnvoll ist."""
        new_name = meta.get('current_filename', '')
        
        # Mindestlänge
        if len(new_name) < 10:
            return False
        
        # Enthält Datum im richtigen Format
        import re
        if not re.match(r'\d{4}-\d{2}-\d{2}', new_name):
            return False
        
        # Keine ungültigen Zeichen
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(c in new_name for c in invalid_chars):
            return False
            
        return True
    
    def check_confidence_threshold(self, meta: dict) -> bool:
        """Prüft ob die KI-Konfidenz ausreichend ist."""
        confidence = meta.get('confidence', 0)
        
        # Schwellenwert: 70% für Auto-Move, darunter → Review
        return confidence >= 0.70
    
    def check_content_extracted(self, meta: dict) -> bool:
        """Prüft ob überhaupt Inhalt extrahiert wurde."""
        text = meta.get('extracted_text', '')
        entities = meta.get('extracted_entities', {})
        
        # Bei Dokumenten muss Text vorhanden sein
        if meta.get('content_type', '').startswith('application/pdf'):
            return len(text.strip()) > 50  # Mindestens 50 Zeichen
        
        # Bei Bildern müssen EXIF oder Entities vorhanden sein
        if meta.get('content_type', '').startswith('image/'):
            return len(entities) > 0 or meta.get('has_exif', False)
        
        return True  # Für andere Typen: OK wenn kein Inhalt
```

### 4. Fehlerbehandlung: Quarantäne-System

```
F:/
├── _Inbox/                  # Eingangskorbπ
├── _Quarantine/             # ⚠️ Problematische Dateien
│   ├── _processing_error/   # Verarbeitung fehlgeschlagen
│   ├── _low_confidence/     # KI unsicher (<50%)
│   ├── _review_needed/      # Plausibilitätsprüfung fehlgeschlagen
│   └── _duplicates/         # Exakte Duplikate (SHA-256 Match)
└── (Zielordner)/            # Normale sortierte Dateien
```

**Quarantäne-Regeln:**

| Situation | Aktion | Zielordner |
| :--- | :--- | :--- |
| Verarbeitung wirft Exception | Log Error → Quarantäne | `_Quarantine/_processing_error/` |
| Konfidenz < 50% | Telegram-Nachricht → Quarantäne | `_Quarantine/_low_confidence/` |
| Konfidenz 50-70% | Telegram-Nachricht → Warten auf Bestätigung | Bleibt in `_Inbox` |
| Konfidenz > 70% + alle Gates OK | Auto-Move | Zielordner |
| Plausibilitätsprüfung fehlgeschlagen | Telegram → Quarantäne | `_Quarantine/_review_needed/` |
| Exaktes Duplikat (SHA-256) | Auto-Move + Info | `_Quarantine/_duplicates/` |

### 5. Telegram-Benachrichtigungen

```python
def send_review_notification(file_meta: dict, errors: list[str]):
    """Sendet Telegram-Benachrichtigung für manuelle Überprüfung."""
    
    message = f"""
🔍 *Manuelle Überprüfung erforderlich*

📁 *Datei:* `{file_meta['original_filename']}`
📂 *Vorgeschlagene Kategorie:* {file_meta['category']}
📊 *Konfidenz:* {file_meta['confidence']*100:.0f}%

⚠️ *Probleme:*
{chr(10).join(f"  • {e}" for e in errors)}

*Vorgeschlagener neuer Name:*
`{file_meta['current_filename']}`

*Zielordner:*
`{file_meta['target_folder']}`

👆 Antwort mit:
• ✅ = Bestätigen und verschieben
• ❌ = Ablehnen (bleibt in Inbox)
• 📝 = Korrigieren (antworte mit: `Kategorie: XYZ`)
"""
    
    telegram_send(message)
```

---

## Validierungs-Schema (SQLite Erweiterung)

```sql
-- Zusätzliche Tabelle für Quarantäne-Tracking
CREATE TABLE IF NOT EXISTS quarantine_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES file_metadata(id),
    quarantine_reason TEXT NOT NULL,
    quarantine_path TEXT NOT NULL,
    original_inbox_path TEXT NOT NULL,
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    resolved_by TEXT,  -- 'auto' oder 'user:username'
    resolution TEXT    -- 'approved', 'rejected', 'reprocessed'
);

-- Zusätzliche Tabelle für Qualitätsprüfungen
CREATE TABLE IF NOT EXISTS quality_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES file_metadata(id),
    check_name TEXT NOT NULL,
    check_passed BOOLEAN NOT NULL,
    check_details TEXT,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- View: Dateien die Aufmerksamkeit brauchen
CREATE VIEW IF NOT EXISTS v_needs_attention AS
SELECT 
    fm.id,
    fm.original_filename,
    fm.category,
    fm.confidence,
    fm.status,
    ql.quarantine_reason,
    ql.created_at as quarantined_at
FROM file_metadata fm
LEFT JOIN quarantine_log ql ON fm.id = ql.file_id
WHERE fm.status IN ('error', 'awaiting_confirmation', 'quarantined')
   OR fm.requires_confirmation = TRUE
ORDER BY fm.ingested_at ASC;
```

---

## Konsequenzen

### Positiv
- ✅ **Jeder Dateityp** wird verarbeitet (kein Datenverlust)
- ✅ **Transparente Fehlerbehandlung** (Quarantäne statt Löschen)
- ✅ **Qualitätssicherung** durch mehrstufige Prüfungen
- ✅ **User im Loop** bei unsicheren Entscheidungen

### Negativ
- ⚠️ Mehr Telegram-Nachrichten bei vielen unsicheren Klassifizierungen
- ⚠️ Quarantäne-Ordner muss regelmäßig geprüft werden
- ⚠️ Komplexerer Workflow (mehr bewegliche Teile)

---

## Verknüpfte Dokumente

- [ADR-004: Document ETL Pipeline](./ADR-004-document-etl.md)
- [ADR-005: OCR Strategy](./ADR-005-ocr-strategy.md)
- [ADR-006: Nextcloud Integration](./ADR-006-nextcloud-integration.md)
