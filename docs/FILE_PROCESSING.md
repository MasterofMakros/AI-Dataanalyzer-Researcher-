# Dateiverarbeitung & Metadaten-Extraktion

> **Wie werden Dateien aller Art ausgelesen und für die Suche aufbereitet?**

*Stand: 2025-12-26*

---

## 1. Überblick: Der Verarbeitungsfluss

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATEI EINGANG                                   │
│                    (beliebiges Format)                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 1: Basis-Analyse (für ALLE Dateien)                            │
│  ─────────────────────────────────────────────────                      │
│  Tool: Python + Apache Tika                                             │
│                                                                         │
│  Extrahiert:                                                            │
│  • SHA-256 Hash (Duplikat-Erkennung)                                   │
│  • Dateigröße (Bytes)                                                   │
│  • MIME-Type (z.B. "application/pdf")                                  │
│  • Erstelldatum / Änderungsdatum                                       │
│  • Dateiname + Extension                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 2: Format-spezifische Extraktion                               │
│  ─────────────────────────────────────────                              │
│  (Details siehe Tabelle unten)                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 3: KI-Anreicherung (Ollama)                                    │
│  ───────────────────────────────────                                    │
│                                                                         │
│  Extrahiert:                                                            │
│  • Kategorie (Rechnung, Vertrag, Foto, ...)                            │
│  • Subkategorie (Eingangsrechnung, Mietvertrag, ...)                   │
│  • Entities (Vendor, Amount, Date, Personen, Orte)                     │
│  • ⭐ META-BESCHREIBUNG (1-2 Sätze: "Worum geht es?")                  │
│  • Vorgeschlagener Dateiname                                            │
│  • Vorgeschlagener Zielordner                                           │
│  • Schlüsselwörter / Tags                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 3b: Transkription mit Zeitmarken (nur Audio/Video)             │
│  ──────────────────────────────────────────────────────────             │
│  Tool: Faster-Whisper                                                   │
│                                                                         │
│  Erstellt:                                                              │
│  • Vollständiges Transkript                                            │
│  • Zeitmarken pro Segment (alle 5-30 Sekunden)                         │
│  • Sprechererkennung (wenn mehrere Stimmen)                            │
│  • Kapitelerkennung (thematische Abschnitte)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 4: Vektorisierung (LlamaIndex → Qdrant)                        │
│  ────────────────────────────────────────────────                       │
│                                                                         │
│  Erstellt:                                                              │
│  • Text-Embedding (768-1536 Dimensionen)                               │
│  • Chunking (500-1000 Tokens pro Chunk)                                │
│  • Vektor-ID für Qdrant                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHRITT 5: Speicherung                                                 │
│  ──────────────────────                                                 │
│                                                                         │
│  • Shadow Ledger (SQLite): Alle Metadaten                              │
│  • Qdrant: Vektor-Embeddings für semantische Suche                     │
│  • Dateisystem: Datei wird verschoben/umbenannt                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Format-spezifische Extraktion (Detail)

### 📄 Dokumente (PDF, DOCX, ODT, TXT, RTF)

| Tool | Was wird extrahiert | Wann |
| :--- | :--- | :--- |
| **Apache Tika** | Volltext, Autor, Titel, Seitenzahl, Erstellungsprogramm | Immer |
| **IBM Docling** | Tabellen (als strukturiertes JSON), Formeln, Überschriften-Hierarchie | Bei komplexen Layouts |
| **Surya OCR** | Text aus Scans/Bildern in PDFs | Wenn kein Text-Layer vorhanden |
| **TrOCR** | Handschriftlicher Text | Wenn Handschrift erkannt |

**Extrahierte Metadaten:**
```json
{
  "content_type": "application/pdf",
  "page_count": 3,
  "author": "Max Mustermann",
  "creation_date": "2024-05-12T10:30:00",
  "producer": "Microsoft Word",
  "extracted_text": "Rechnung Nr. 12345...",
  "tables": [
    {"rows": 5, "cols": 3, "data": [...]}
  ],
  "has_ocr_text": true,
  "language": "de"
}
```

---

### 📧 E-Mails (EML, MSG, MBOX)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **Apache Tika** | Absender, Empfänger, CC, BCC, Betreff, Datum, Body (Plain + HTML) |
| **Python email** | Anhänge (werden separat verarbeitet) |

**Extrahierte Metadaten:**
```json
{
  "content_type": "message/rfc822",
  "from": "sender@example.com",
  "to": ["recipient@example.com"],
  "cc": [],
  "subject": "Ihre Rechnung vom 12.05.2024",
  "date": "2024-05-12T14:22:00+02:00",
  "body_text": "Sehr geehrter Herr...",
  "body_html": "<html>...",
  "attachments": [
    {"filename": "Rechnung.pdf", "size": 125000, "processed_id": "abc123"}
  ],
  "thread_id": "xyz789",
  "is_reply": true
}
```

---

### 🖼️ Bilder (JPG, PNG, HEIC, WEBP, TIFF)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **Pillow/ExifRead** | EXIF-Daten (GPS, Kamera, Datum, Blende, ISO) |
| **CLIP** | Bild-Embedding (für "Suche nach ähnlichen Bildern") |
| **LLaVA (via Ollama)** | Natürlichsprachliche Beschreibung ("Ein golden retriever am Strand") |
| **Immich** | Gesichtserkennung, Objekterkennung |

**Extrahierte Metadaten:**
```json
{
  "content_type": "image/jpeg",
  "width": 4032,
  "height": 3024,
  "exif": {
    "make": "Apple",
    "model": "iPhone 14 Pro",
    "datetime_original": "2024-08-15T14:30:22",
    "gps_latitude": 41.3851,
    "gps_longitude": 2.1734,
    "focal_length": "6.86mm",
    "aperture": "f/1.78"
  },
  "ai_description": "Ein Golden Retriever läuft am Strand bei Sonnenuntergang",
  "ai_tags": ["Hund", "Strand", "Sonnenuntergang", "Meer"],
  "faces_detected": 0,
  "dominant_colors": ["#F4A460", "#87CEEB", "#FFD700"]
}
```

---

### 🎥 Videos (MP4, MKV, AVI, MOV, WEBM)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **FFprobe** | Dauer, Auflösung, Codec, Bitrate, Audio-Spuren |
| **Faster-Whisper** | ⭐ Transkription MIT ZEITMARKEN |
| **CLIP (Frame-Sampling)** | Beschreibung von Key-Frames (alle 30 Sek) |
| **Ollama** | ⭐ Meta-Beschreibung + Kapitelstruktur |
| **Czkawka** | Perceptual Hash für Duplikat-Erkennung |

**Extrahierte Metadaten:**
```json
{
  "content_type": "video/mp4",
  "duration_seconds": 1847,
  "resolution": "1920x1080",
  "codec_video": "h264",
  "codec_audio": "aac",
  "bitrate_kbps": 8500,
  "fps": 30,
  "audio_tracks": ["de"],
  
  "⭐ meta_description": "Ein 30-minütiges Tutorial über die Einrichtung von Docker auf Windows. Der Sprecher erklärt Schritt für Schritt die Installation, Konfiguration und häufige Fehlerquellen.",
  
  "⭐ transcript_timestamped": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Willkommen zu meinem Docker-Tutorial.",
      "speaker": "Speaker_1"
    },
    {
      "start": 5.2,
      "end": 12.8,
      "text": "Heute zeige ich euch, wie ihr Docker auf Windows installiert.",
      "speaker": "Speaker_1"
    },
    {
      "start": 12.8,
      "end": 25.1,
      "text": "Zuerst müssen wir die Docker Desktop Anwendung herunterladen.",
      "speaker": "Speaker_1"
    },
    {
      "start": 180.0,
      "end": 195.5,
      "text": "Ein häufiger Fehler ist, dass WSL2 nicht aktiviert ist.",
      "speaker": "Speaker_1"
    }
  ],
  
  "⭐ chapters": [
    {"start": 0, "end": 120, "title": "Einleitung", "summary": "Begrüßung und Übersicht"},
    {"start": 120, "end": 600, "title": "Installation", "summary": "Download und Installation von Docker Desktop"},
    {"start": 600, "end": 1200, "title": "Konfiguration", "summary": "WSL2 Setup und Ressourcen-Einstellungen"},
    {"start": 1200, "end": 1847, "title": "Troubleshooting", "summary": "Häufige Fehler und deren Lösungen"}
  ],
  
  "tags": ["Docker", "Tutorial", "Windows", "Installation", "DevOps"],
  "perceptual_hash": "a4f7b2c1d9e8..."
}
```

**⭐ Suchbare Zeitmarken:**
```
User: "Wo erklärt er den WSL2 Fehler?"

→ Suche in transcript_timestamped: "WSL2" + "Fehler"
→ Result: Video bei 03:00 (180 Sekunden)
→ Deep-Link: file:///F:/tutorials/docker.mp4?t=180
```

---

### 🎵 Audio (MP3, WAV, FLAC, M4A, OGG)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **Mutagen** | ID3-Tags (Titel, Artist, Album, Jahr, Genre) |
| **Faster-Whisper** | ⭐ Transkription MIT ZEITMARKEN (für Podcasts, Voice Memos) |
| **Ollama** | ⭐ Meta-Beschreibung + Themenextraktion |

**Beispiel 1: Musik (keine Transkription nötig)**
```json
{
  "content_type": "audio/mpeg",
  "duration_seconds": 355,
  "bitrate_kbps": 320,
  "sample_rate": 44100,
  "id3": {
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "album": "A Night at the Opera",
    "year": 1975,
    "genre": "Rock"
  },
  "is_music": true,
  "is_voice_memo": false,
  "transcript_timestamped": null,
  
  "⭐ meta_description": "Bohemian Rhapsody von Queen aus dem Album 'A Night at the Opera' (1975). Ein 6-minütiger Progressive-Rock-Klassiker."
}
```

**Beispiel 2: Voice Memo / Podcast (MIT Transkription)**
```json
{
  "content_type": "audio/m4a",
  "duration_seconds": 487,
  "bitrate_kbps": 128,
  "sample_rate": 44100,
  "is_music": false,
  "is_voice_memo": true,
  
  "⭐ meta_description": "Voice Memo vom 15.08.2024: Ideen für das Q4-Projekt, Diskussion über Budget und Timeline. Erwähnt werden: Marketing-Kampagne, Sarah vom Vertrieb, Deadline Ende November.",
  
  "⭐ transcript_timestamped": [
    {
      "start": 0.0,
      "end": 8.5,
      "text": "Hey, das ist eine schnelle Notiz zu meinen Ideen für Q4.",
      "speaker": "Speaker_1"
    },
    {
      "start": 8.5,
      "end": 22.0,
      "text": "Ich denke wir sollten die Marketing-Kampagne auf November verschieben.",
      "speaker": "Speaker_1"
    },
    {
      "start": 22.0,
      "end": 35.5,
      "text": "Sarah vom Vertrieb hat gesagt, das Budget steht erst Ende Oktober.",
      "speaker": "Speaker_1"
    },
    {
      "start": 180.0,
      "end": 195.0,
      "text": "Die Deadline für den Pitch ist der 28. November.",
      "speaker": "Speaker_1"
    }
  ],
  
  "⭐ extracted_entities": {
    "people": ["Sarah"],
    "departments": ["Vertrieb", "Marketing"],
    "dates": ["November", "Ende Oktober", "28. November"],
    "topics": ["Q4-Projekt", "Budget", "Kampagne", "Pitch"]
  },
  
  "⭐ action_items": [
    "Marketing-Kampagne auf November verschieben",
    "Budget-Status mit Sarah klären"
  ]
}
```

**⭐ Suchbare Zeitmarken bei Audio:**
```
User: "Wann habe ich etwas über Sarah gesagt?"

→ Suche in transcript_timestamped: "Sarah"
→ Result: Voice Memo bei 00:22 (22 Sekunden)
→ Entities zeigen: Sarah = Vertrieb

User: "Finde alle Voice Memos über Budget"

→ Suche in meta_description + entities: "Budget"
→ Results: 3 Voice Memos gefunden
```

---

### 📦 Archive (ZIP, RAR, 7Z, TAR.GZ)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **Python zipfile/rarfile** | Liste aller enthaltenen Dateien |
| **Ratarmount** | Virtuelles Mounten (ohne Extraktion) |

**Extrahierte Metadaten:**
```json
{
  "content_type": "application/zip",
  "compressed_size_bytes": 52428800,
  "uncompressed_size_bytes": 104857600,
  "file_count": 127,
  "folder_count": 15,
  "contents": [
    {"path": "Projekt/README.md", "size": 4096},
    {"path": "Projekt/src/main.py", "size": 8192},
    {"path": "Projekt/docs/manual.pdf", "size": 2097152}
  ],
  "is_encrypted": false,
  "compression_ratio": 0.5
}
```

**Hinweis:** Inhalte von Archiven werden NICHT automatisch extrahiert. Stattdessen:
- Die Inhaltsliste wird indexiert (Suche nach Dateinamen im Archiv möglich)
- Bei Bedarf kann via **Ratarmount** virtuell zugegriffen werden

---

### 💻 Code & Config (PY, JS, JSON, YAML, MD, HTML, CSS)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **Apache Tika** | Volltext als Plain Text |
| **Linguist** | Programmiersprache erkennen |
| **Custom Parser** | Imports, Klassen, Funktionen (für Code-Suche) |

**Extrahierte Metadaten:**
```json
{
  "content_type": "text/x-python",
  "language": "Python",
  "line_count": 245,
  "imports": ["pandas", "numpy", "sklearn"],
  "classes": ["DataProcessor", "ModelTrainer"],
  "functions": ["load_data", "train_model", "evaluate"],
  "has_docstrings": true,
  "encoding": "utf-8"
}
```

---

### 🔧 Binärdateien (EXE, DLL, ISO, DMG)

| Tool | Was wird extrahiert |
| :--- | :--- |
| **File Magic** | Genauen Typ erkennen |
| **Python hashlib** | SHA-256 Hash |

**Extrahierte Metadaten:**
```json
{
  "content_type": "application/x-executable",
  "sha256": "a1b2c3d4...",
  "file_size_bytes": 5242880,
  "is_executable": true,
  "platform": "Windows x64"
}
```

**⚠️ Sicherheit:** Binärdateien werden NIE ausgeführt. Nur Hash + Metadaten.

---

## 3. Das Metadaten-Schema (Shadow Ledger)

Alle extrahierten Metadaten werden in der SQLite-Datenbank gespeichert:

```sql
-- Jede Datei hat einen Eintrag in file_metadata
INSERT INTO file_metadata (
    -- Basis (immer vorhanden)
    sha256,
    original_filename,
    original_path,
    current_filename,
    current_path,
    file_size_bytes,
    content_type,
    
    -- Timestamps
    file_created_at,
    file_modified_at,
    ingested_at,
    
    -- KI-Klassifizierung
    category,
    subcategory,
    confidence,
    
    -- Extrahierte Inhalte
    extracted_text,           -- Volltext (für Suche)
    extracted_entities,       -- JSON: {"vendor": "Bauhaus", "amount": 45.50}
    
    -- Format-spezifisch (JSON)
    format_metadata,          -- Alles andere (EXIF, ID3, etc.)
    
    -- Externe IDs
    qdrant_point_id
) VALUES (...);
```

### Das `extracted_entities` Feld (JSON)

Je nach Dateityp enthält dieses Feld verschiedene Entities:

| Dokumenttyp | Typische Entities |
| :--- | :--- |
| **Rechnung** | `vendor`, `amount`, `currency`, `invoice_number`, `invoice_date`, `due_date` |
| **Kontoauszug** | `bank`, `account_number`, `statement_date`, `balance`, `transactions[]` |
| **Vertrag** | `parties[]`, `contract_type`, `start_date`, `end_date`, `value` |
| **Foto** | `location`, `people[]`, `objects[]`, `event` |
| **E-Mail** | `sender`, `recipients[]`, `topic`, `action_items[]` |

---

## 4. Die Such-Indizes

### 4.1 Qdrant (Semantische Suche)

```python
# Beispiel: Dokument in Qdrant speichern
qdrant_client.upsert(
    collection_name="neural_vault",
    points=[
        {
            "id": "file_12345",
            "vector": embedding_768d,  # LlamaIndex generiert
            "payload": {
                "original_filename": "IMG_4523.jpg",
                "current_filename": "2024-08-15_Foto_Barcelona_Strand.jpg",
                "category": "Foto",
                "path": "/07 Persönlich/Fotos/2024/",
                "extracted_text": "Golden Retriever am Strand...",
                "entities": {"location": "Barcelona", "tags": ["Hund", "Strand"]}
            }
        }
    ]
)
```

**Suchmöglichkeiten:**
- "Zeige mir Fotos vom Strand" → Semantische Ähnlichkeit
- "Finde Rechnungen über 100€" → Payload-Filter + Semantik

## 5. Zusammenfassung: Was wird wo gespeichert?

| Speicherort | Was | Zweck |
| :--- | :--- | :--- |
| **Dateisystem (F:/)** | Die Datei selbst (umbenannt) | Zugriff via Nextcloud/Explorer |
| **Shadow Ledger (SQLite)** | Alle Metadaten + Original-Dateiname | Audit-Trail, Schnelle Abfragen |
| **Qdrant** | Vektor-Embeddings + Payload | Semantische Suche ("ähnliche Dokumente") |

---

## 6. Beispiel: Kompletter Durchlauf einer Rechnung

**Input:** `IMG_4523.jpg` (Foto einer Bauhaus-Rechnung)

### Schritt 1: Basis-Analyse
```json
{
  "sha256": "a1b2c3...",
  "original_filename": "IMG_4523.jpg",
  "content_type": "image/jpeg",
  "file_size_bytes": 2457600
}
```

### Schritt 2: Format-spezifisch (EXIF + OCR)
```json
{
  "exif": {
    "datetime_original": "2024-05-12T10:15:00",
    "device": "iPhone 14 Pro"
  },
  "ocr_text": "BAUHAUS\nRechnung Nr. 2024-12345\nDatum: 12.05.2024\nGesamt: 127,50 EUR\nGartenschlauch 25m..."
}
```

### Schritt 3: KI-Klassifizierung
```json
{
  "category": "Finanzen",
  "subcategory": "Rechnung",
  "confidence": 0.94,
  "entities": {
    "vendor": "Bauhaus",
    "amount": 127.50,
    "currency": "EUR",
    "invoice_number": "2024-12345",
    "invoice_date": "2024-05-12",
    "items": ["Gartenschlauch 25m"]
  },
  "suggested_filename": "2024-05-12_Rechnung_Bauhaus_127EUR.jpg",
  "suggested_folder": "/09 Finanzen/Eingangsrechnungen/2024/"
}
```

### Schritt 4: Speicherung
- **Datei verschoben nach:** `F:/09 Finanzen/Eingangsrechnungen/2024/2024-05-12_Rechnung_Bauhaus_127EUR.jpg`
- **Shadow Ledger:** Alle Metadaten gespeichert, Original-Name erhalten
- **Qdrant:** Embedding gespeichert mit Payload

### Spätere Suche
```
User: "Zeige mir Bauhaus-Rechnungen von 2024"

→ Qdrant: Payload-Filter category="Rechnung" AND invoice_date LIKE "2024%"
→ Result: 2024-05-12_Rechnung_Bauhaus_127EUR.jpg
```

---

*Dieses Dokument erklärt, wie JEDE Datei verarbeitet wird, um maximale Auffindbarkeit zu gewährleisten.*
