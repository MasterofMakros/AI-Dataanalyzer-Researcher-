# Format-Verarbeitungsspezifikation (Vollständig)

> **Wie wird JEDES Format verarbeitet?**

*Stand: 2025-12-26*

---

## Legende

| Symbol | Bedeutung |
| :--- | :--- |
| ✅ | Vollständig implementiert |
| ⚠️ | Teilweise / Fallback |
| ❌ | Nur Hash |

---

## 1. DOKUMENTE

### PDF (.pdf) - 35.587 Dateien
```yaml
Tools: Apache Tika, IBM Docling, Surya OCR, TrOCR
Extrahiert:
  - Volltext (alle Seiten)
  - Tabellen (strukturiert als JSON)
  - Bilder (extrahiert, separat analysiert)
  - Metadaten: Autor, Erstelldatum, Producer
  - OCR: Wenn Scan erkannt (kein Text-Layer)
  - Handschrift: TrOCR wenn erkannt
Indexiert in: Qdrant (Volltext), Qdrant (Chunks)
Sortierung: Nach Kategorie (Rechnung→Finanzen, Vertrag→Rechtliches)
```

### Word (.docx, .doc) - 25.417 Dateien
```yaml
Tools: Apache Tika, python-docx
Extrahiert:
  - Volltext
  - Überschriften-Hierarchie
  - Tabellen
  - Kommentare & Änderungen
  - Eingebettete Bilder
  - Metadaten: Autor, Firma, Erstelldatum
Indexiert in: Qdrant, Qdrant
```

### Excel (.xlsx, .xls) - 16.991 Dateien
```yaml
Tools: Apache Tika, openpyxl, xlrd
Extrahiert:
  - Alle Sheets (Namen + Inhalt)
  - Zellwerte (als Text)
  - Formeln (als Referenz)
  - Diagramm-Titel
  - Spaltenüberschriften
Indexiert in: Qdrant
Besonderheit: Zahlenformate erhalten (Währung, Datum)
```

### PowerPoint (.pptx, .ppt) - 3.675 Dateien
```yaml
Tools: Apache Tika, python-pptx
Extrahiert:
  - Folientext
  - Notizen
  - Folientitel
  - Eingebettete Bilder
Indexiert in: Qdrant, Qdrant
```

### Text (.txt, .md, .rtf) - 21.449 Dateien
```yaml
Tools: Native Python, markdown
Extrahiert:
  - Volltext
  - Markdown-Struktur (bei .md)
Indexiert in: Qdrant, Qdrant
```

---

## 2. E-MAIL

### EML (.eml) - 65.958 Dateien
```yaml
Tools: Python email, Apache Tika
Extrahiert:
  - From, To, CC, BCC
  - Subject, Date
  - Body (Plain + HTML)
  - Anhänge (separat verarbeitet)
  - Thread-ID
  - In-Reply-To
Indexiert in: Qdrant (Volltext), SQLite (Metadaten)
Sortierung: Nach Absender-Domain, Datum
```

### MSG (.msg) - 396 Dateien
```yaml
Tools: Apache Tika, extract-msg
Extrahiert: Wie EML + Outlook-spezifische Felder
```

### PST (.pst) - 351 Dateien
```yaml
Tools: libpst, readpst
Strategie: Archiv entpacken → einzelne E-Mails als EML
Extrahiert: Alle enthaltenen E-Mails + Kalender + Kontakte
Achtung: Kann sehr groß sein, Batch-Verarbeitung
```

---

## 3. BILDER

### JPEG/JPG (.jpg, .jpeg) - 65.746 Dateien
```yaml
Tools: Pillow, ExifRead, CLIP, LLaVA
Extrahiert:
  - EXIF: GPS, Kamera, Datum, Blende, ISO
  - CLIP-Embedding: Für Ähnlichkeitssuche
  - LLaVA-Beschreibung: "Ein Hund am Strand"
  - Dominant Colors
  - Gesichtserkennung (via Immich)
Indexiert in: Qdrant (CLIP-Vektor), SQLite (EXIF)
Sortierung: Nach Datum, Ort, erkannten Objekten
```

### PNG (.png) - 35.007 Dateien
```yaml
Tools: Pillow, CLIP, LLaVA
Extrahiert:
  - Basis-Metadaten
  - CLIP-Embedding
  - Beschreibung
  - Screenshot-Erkennung (Text via OCR)
```

### TIFF (.tif, .tiff) - 11.390 Dateien
```yaml
Tools: Pillow, ExifRead, Surya OCR
Extrahiert:
  - EXIF (oft Scanner-Info)
  - OCR wenn Scan/Dokument
  - Multi-Page-Support
Besonderheit: Oft gescannte Dokumente → OCR prioritär
```

### RAW-Formate (.arw, .rw, .rwl) - ~4.000 Dateien
```yaml
Tools: rawpy, ExifRead
Extrahiert:
  - EXIF (Kamera, Einstellungen)
  - Thumbnail für Vorschau
  - GPS wenn vorhanden
```

### SVG (.svg) - 6.137 Dateien
```yaml
Tools: xml.etree, svglib
Extrahiert:
  - Text-Elemente
  - Titel, Description
  - Struktur-Infos
```

### WebP (.webp) - 386 Dateien
```yaml
Tools: Pillow, CLIP
Extrahiert: Wie PNG
```

### EXR (.exr) - 4.524 Dateien
```yaml
Tools: OpenEXR
Extrahiert:
  - HDR-Metadaten
  - Layer-Namen
  - Render-Engine Info
```

---

## 4. VIDEO

### MP4 (.mp4) - 3.003 Dateien
```yaml
Tools: FFprobe, Faster-Whisper, CLIP
Extrahiert:
  - Dauer, Auflösung, Codec, Bitrate, FPS
  - Audio-Transkript MIT ZEITMARKEN
  - Kapitelmarken (wenn vorhanden)
  - Key-Frame-Beschreibungen (alle 30 Sek)
  - Untertitel (wenn eingebettet)
Indexiert in: Qdrant (pro Segment), Qdrant (Volltranskript)
Deep-Link: video.mp4?t=125 (Sekunden)
```

### MKV (.mkv) - 2.535 Dateien
```yaml
Tools: FFprobe, Faster-Whisper, MKVToolNix
Extrahiert:
  - Wie MP4 +
  - Kapitelmarken
  - Mehrere Audio-Tracks
  - Eingebettete Untertitel (.srt)
```

### MOV (.mov) - 340 Dateien
```yaml
Tools: FFprobe, Faster-Whisper
Extrahiert:
  - Wie MP4 +
  - Apple-spezifische Metadaten
  - GPS (wenn iPhone)
  - HDR-Info (ProRes, HEVC)
```

### MTS (.mts) - 2.011 Dateien
```yaml
Tools: FFprobe, Faster-Whisper
Info: AVCHD-Kameraformat
Extrahiert: Wie MP4, oft ohne Metadaten
```

### VOB/DVD (VIDEO_TS/) - ~500 Dateien
```yaml
Tools: lsdvd, FFprobe, Faster-Whisper
Strategie: Als EINHEIT behandeln
Extrahiert:
  - DVD-Titel aus IFO
  - Kapitelmarken
  - Audio-Transkript (längster Titel)
  - Sprachen, Untertitel
Indexiert als: Eine Datei pro DVD, nicht pro VOB
```

### AVI (.avi) - ~200 Dateien
```yaml
Tools: FFprobe, Faster-Whisper
Extrahiert: Wie MP4 (Legacy-Format)
```

### SWF (.swf) - 461 Dateien
```yaml
Tools: swftools
Extrahiert:
  - Nur Metadaten (Flash deprecated)
  - Embedded Text wenn möglich
Status: ⚠️ Legacy
```

---

## 5. AUDIO

### MP3 (.mp3) - 2.027 Dateien
```yaml
Tools: Mutagen, Faster-Whisper
Extrahiert:
  - ID3-Tags: Titel, Artist, Album, Jahr, Genre
  - Cover-Art
  - Transkript wenn Sprache (Podcast, Voice Memo)
Logik: Musik → nur Tags; Sprache → Transkript
```

### WAV (.wav) - 486 Dateien
```yaml
Tools: wave, Faster-Whisper
Extrahiert:
  - Dauer, Sample-Rate, Channels
  - Transkript MIT ZEITMARKEN
```

### M4A (.m4a) - 345 Dateien
```yaml
Tools: Mutagen, Faster-Whisper
Extrahiert: Wie MP3
```

### WMA (.wma) - ~50 Dateien
```yaml
Tools: FFmpeg → WAV → Whisper
Extrahiert:
  - WMA-Tags
  - Transkript nach Konvertierung
```

### FLAC (.flac) - ~30 Dateien
```yaml
Tools: Mutagen
Extrahiert:
  - Vorbis-Tags
  - Meist Musik → nur Tags
```

---

## 6. ARCHIVE

### ZIP (.zip) - 1.540 Dateien
```yaml
Tools: zipfile
Extrahiert:
  - Dateiliste (Pfade + Größen)
  - Kompressionsinfo
NICHT: Automatisch entpacken
Indexiert: Dateinamen im Archiv durchsuchbar
```

### RAR (.rar) - 2.192 Dateien
```yaml
Tools: rarfile, unrar
Extrahiert: Wie ZIP
```

### 7Z (.7z) - ~100 Dateien
```yaml
Tools: py7zr
Extrahiert: Wie ZIP
```

### GZ/TAR.GZ (.gz) - 1.410 Dateien
```yaml
Tools: gzip, tarfile
Extrahiert: Wie ZIP
```

### APK (.apk) - 1.571 Dateien
```yaml
Tools: zipfile (APK ist ZIP)
Extrahiert:
  - AndroidManifest.xml: App-Name, Permissions
  - Package-Name
  - Version
```

### ISO (.iso) - ~20 Dateien
```yaml
Tools: pycdlib
Extrahiert:
  - Volume-Label
  - Dateiliste
  - Boot-Info
```

---

## 7. CODE & CONFIG

### Python (.py) - 13.385 Dateien
```yaml
Tools: ast, Python Parser
Extrahiert:
  - Volltext
  - Imports
  - Klassen + Methoden
  - Docstrings
  - TODO/FIXME Kommentare
```

### JavaScript (.js, .mjs, .cjs) - 70.924 Dateien
```yaml
Tools: esprima, Volltext
Extrahiert:
  - Volltext
  - Imports/Exports
  - Funktionsnamen
```

### TypeScript (.ts, .tsx) - 21.140 Dateien
```yaml
Tools: Volltext
Extrahiert:
  - Volltext
  - Komponenten-Namen (bei TSX)
```

### HTML (.html, .htm) - 176.115 Dateien
```yaml
Tools: BeautifulSoup
Extrahiert:
  - Title, Meta-Description
  - Volltext (ohne Tags)
  - Bilder-URLs
  - Links
```

### CSS (.css) - 1.516 Dateien
```yaml
Tools: Volltext
Extrahiert: Volltext (für Suche nach Klassennamen)
```

### JSON (.json) - 24.705 Dateien
```yaml
Tools: json
Extrahiert:
  - Volltext
  - Key-Names
  - Struktur-Info
```

### YAML (.yml, .yaml) - 626 Dateien
```yaml
Tools: pyyaml
Extrahiert: Volltext
```

### SQL (.sql) - ~500 Dateien
```yaml
Tools: Volltext
Extrahiert:
  - Tabellennamen
  - Volltext
```

### PowerShell (.ps1) - 1.108 Dateien
```yaml
Tools: Volltext
Extrahiert: Volltext
```

---

## 8. CAD & 3D

### DWG (.dwg) - 582 Dateien
```yaml
Tools: ODA File Converter, LibreDWG
Extrahiert:
  - Layer-Namen
  - Block-Namen
  - Text-Elemente
  - Bemaßungen
  - Thumbnail (PNG-Export)
```

### FBX (.fbx) - 3.215 Dateien
```yaml
Tools: FBX SDK, Assimp
Extrahiert:
  - Mesh-Namen
  - Material-Namen
  - Texture-Pfade
  - Bone/Rig-Info
```

### C4D (.c4d) - 411 Dateien
```yaml
Tools: ⚠️ Proprietär (Cinema4D)
Strategie: Suche Export-Dateien (.fbx, .obj)
Fallback: Dateiname + Datum
```

### OBJ/STL (.obj, .stl) - ~200 Dateien
```yaml
Tools: trimesh
Extrahiert:
  - Vertex-Count
  - Dimensionen
  - Material-Referenzen
```

---

## 9. UNTERTITEL

### SRT (.srt) - 4.644 Dateien
```yaml
Tools: pysrt
Extrahiert:
  - Volltext MIT ZEITMARKEN
  - Jeder Eintrag separat indexiert
Suche: "Was wird bei Minute 5 gesagt?"
Deep-Link: video.mp4?t=300
```

### VTT (.vtt) - ~50 Dateien
```yaml
Tools: webvtt-py
Extrahiert: Wie SRT (WebVTT-Format)
```

---

## 10. SONSTIGES

### Torrent (.torrent) - 94.568 Dateien
```yaml
Tools: bencodepy
Extrahiert:
  - Dateiliste (was wird geteilt)
  - Tracker-URL
  - Hash
  - Ersteller
  - Erstelldatum
```

### LNK (.lnk) - 603 Dateien
```yaml
Tools: pylnk
Extrahiert:
  - Ziel-Pfad
  - Beschreibung
```

### INI (.ini) - 1.107 Dateien
```yaml
Tools: configparser
Extrahiert: Volltext
```

---

## 11. NICHT INDEXIERT

### Temporär
```
.tmp, .bak, .swp, .lock
→ Ignorieren
```

### Kompiliert
```
.pyc, .pyo, .class, .o
→ Ignorieren (aus Quellcode generiert)
```

### Source Maps
```
.map
→ Ignorieren (Debug-Info)
```

### System
```
.dll, .exe, .sys, .mui, .manifest, .cat, .mum
→ Nur SHA-256 Hash
```

---

*Jedes Format hat eine definierte Strategie für maximale Suchgenauigkeit.*
