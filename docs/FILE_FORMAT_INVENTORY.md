# Dateiformat-Inventar: Laufwerk F:

> **Vollständige Analyse aller Dateitypen auf dem 10TB Speicher**

*Scan-Datum: 2025-12-26*

---

## Zusammenfassung

| Kategorie | Anzahl Formate | Gesamtdateien | Status |
| :--- | :--- | :--- | :--- |
| **Dokumente** | 25+ | ~180.000 | ✅ Voll unterstützt |
| **Medien (Bild)** | 15+ | ~120.000 | ✅ Voll unterstützt |
| **Medien (Video)** | 10+ | ~8.000 | ✅ Voll unterstützt |
| **Medien (Audio)** | 8+ | ~3.500 | ✅ Voll unterstützt |
| **Code/Config** | 30+ | ~150.000 | ✅ Voll unterstützt |
| **Archive** | 8+ | ~5.500 | ✅ Container-Index |
| **CAD/3D** | 5+ | ~4.000 | ⚠️ Teilweise |
| **System/Binary** | 15+ | ~50.000 | ⚠️ Nur Hash |

---

## Top 50 Dateitypen (nach Anzahl)

| # | Extension | Anzahl | Kategorie | Verarbeitungsstrategie |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **.html** | 166.303 | Web | Volltext, DOM-Struktur |
| 2 | **.torrent** | 94.568 | Meta | Tracker-Info, Dateiliste |
| 3 | **.js** | 67.059 | Code | Volltext, Imports |
| 4 | **.eml** | 65.958 | E-Mail | Header, Body, Anhänge |
| 5 | **.jpg** | 61.086 | Bild | EXIF, CLIP, Beschreibung |
| 6 | **.pdf** | 35.587 | Dokument | OCR, Tabellen, Volltext |
| 7 | **.png** | 35.007 | Bild | CLIP, Beschreibung |
| 8 | **.dll** | 28.884 | Binary | Nur Hash |
| 9 | **.json** | 24.705 | Data | Volltext, Schema |
| 10 | **.ts** | 19.699 | Code/Video | TypeScript ODER MPEG-TS |
| 11 | **.manifest** | 17.626 | System | Ignorieren |
| 12 | **.map** | 17.178 | Code | Source Maps, ignorieren |
| 13 | **.tmp** | 16.102 | Temp | ❌ Nicht indexieren |
| 14 | **.doc** | 15.077 | Dokument | Tika, Volltext |
| 15 | **.py** | 13.385 | Code | Volltext, Classes, Imports |
| 16 | **.txt** | 12.334 | Text | Volltext |
| 17 | **.xlsx** | 11.459 | Dokument | Tabellen, Formeln |
| 18 | **.tif/.tiff** | 11.390 | Bild | EXIF, OCR (wenn Scan) |
| 19 | **.docx** | 10.340 | Dokument | Tika, Volltext |
| 20 | **.htm** | 9.812 | Web | Volltext |
| 21 | **.pyc** | 8.733 | Binary | ❌ Nicht indexieren |
| 22 | **.md** | 8.705 | Dokument | Markdown → Volltext |
| 23 | **.mui** | 7.846 | System | Ignorieren |
| 24 | **.svg** | 6.137 | Bild | Text-Elemente |
| 25 | **.xls** | 5.532 | Dokument | Tabellen |
| 26 | **.exe** | 4.947 | Binary | Nur Hash |
| 27 | **.jpeg** | 4.660 | Bild | EXIF, CLIP |
| 28 | **.srt** | 4.644 | Untertitel | ⭐ Volltext + Zeitmarken |
| 29 | **.exr** | 4.524 | Bild/3D | HDR-Metadaten |
| 30 | **.bmp** | 4.133 | Bild | Basis-Metadaten |
| 31 | **.dat** | 3.597 | Binary | Nur Hash |
| 32 | **.pptx** | 3.321 | Dokument | Folien, Text |
| 33 | **.fbx** | 3.215 | 3D | Mesh-Info, Materialien |
| 34 | **.mp4** | 3.003 | Video | ⭐ Transkript, Frames |
| 35 | **.gif** | 2.733 | Bild | Basis |
| 36 | **.mkv** | 2.535 | Video | ⭐ Transkript, Kapitel |
| 37 | **.rar** | 2.192 | Archiv | Inhaltsliste |
| 38 | **.lua** | 2.147 | Code | Volltext |
| 39 | **.mp3** | 2.027 | Audio | ID3-Tags, Transkript |
| 40 | **.mts** | 2.011 | Video | AVCHD, Transkript |
| 41 | **.xml** | 1.952 | Data | Volltext, Schema |
| 42 | **.csv** | 1.597 | Data | Spalten, Volltext |
| 43 | **.apk** | 1.571 | Archiv | Manifest, Inhalt |
| 44 | **.zip** | 1.540 | Archiv | Inhaltsliste |
| 45 | **.css** | 1.516 | Code | Volltext |
| 46 | **.tsx** | 1.441 | Code | TypeScript React |
| 47 | **.gz** | 1.410 | Archiv | Inhaltsliste |
| 48 | **.ttf** | 1.161 | Font | Font-Name |
| 49 | **.ps1** | 1.108 | Code | PowerShell |
| 50 | **.ini** | 1.107 | Config | Volltext |

---

## Spezialformate (Detailliert)

### 📐 CAD/3D-Formate

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.dwg** | 582 | ODA Converter | Layer, Texte, Bemaßungen |
| **.fbx** | 3.215 | FBX SDK | Mesh-Info, Materialien |
| **.c4d** | 411 | ⚠️ Proprietär | Fallback: Export suchen |
| **.exr** | 4.524 | OpenEXR | HDR-Metadaten |
| **.vtf/.vtx** | ~850 | Source Engine | Texture-Info |

### 🎬 Video-Formate

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.mp4** | 3.003 | FFprobe, Whisper | Transkript + Frames |
| **.mkv** | 2.535 | FFprobe, Whisper | Transkript + Kapitel |
| **.mts** | 2.011 | FFprobe, Whisper | AVCHD-Kamera |
| **.mov** | 340 | FFprobe, Whisper | Apple QuickTime |
| **.ts** | ~5.000 | FFprobe | MPEG-TS (Teil von .mkv) |
| **.vob** | ~500 | DVD-Handler | Als DVD-Einheit |
| **.avi** | ~200 | FFprobe, Whisper | Legacy |
| **.swf** | 461 | ⚠️ Flash (Legacy) | Nur Metadaten |

### 🎵 Audio-Formate

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.mp3** | 2.027 | Mutagen, Whisper | ID3 + Transkript |
| **.wav** | 486 | Whisper | Transkript |
| **.m4a** | 345 | Mutagen, Whisper | AAC-Audio |
| **.wma** | ~50 | FFmpeg → Whisper | Legacy Windows |
| **.flac** | ~30 | Mutagen | Lossless |

### 📧 E-Mail & Kommunikation

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.eml** | 65.958 | Tika, email | Header, Body, Anhänge |
| **.msg** | 396 | Tika | Outlook-Format |
| **.pst** | 351 | ⚠️ Kompliziert | Outlook-Archiv |

### 📦 Archive

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.zip** | 1.540 | zipfile | Inhaltsliste |
| **.rar** | 2.192 | rarfile | Inhaltsliste |
| **.gz** | 1.410 | gzip | Inhaltsliste |
| **.apk** | 1.571 | zipfile | Android-App, Manifest |
| **.cab** | 405 | cabfile | Windows-Installer |

### 📷 RAW-Formate (Kamera)

| Extension | Anzahl | Tool | Strategie |
| :--- | :--- | :--- | :--- |
| **.arw** | 661 | rawpy, ExifRead | Sony RAW |
| **.rw/.rwl** | ~3.000 | rawpy | Leica/Panasonic RAW |
| **.tif** | 11.390 | Pillow, ExifRead | TIFF (oft Scans) |

---

## Formate die NICHT indexiert werden

| Extension | Anzahl | Grund |
| :--- | :--- | :--- |
| **.tmp** | 16.102 | Temporäre Dateien |
| **.pyc** | 8.733 | Python Bytecode (aus .py generiert) |
| **.manifest** | 17.626 | Windows Assemblies |
| **.map** | 17.178 | Source Maps (aus .js generiert) |
| **.mui** | 7.846 | Windows UI Resources |
| **.dll** | 28.884 | Binary (nur Hash) |
| **.exe** | 4.947 | Binary (nur Hash) |
| **.mum/.cat** | ~6.000 | Windows Update |

---

## Verarbeitungsmatrix (Vollständig)

### ✅ Vollständig analysiert (Volltext + Metadaten + Embedding)

```
.pdf, .docx, .doc, .xlsx, .xls, .pptx, .ppt, .odt, .ods, .odp
.txt, .md, .rtf, .csv, .json, .xml, .yaml, .yml
.html, .htm
.eml, .msg
.jpg, .jpeg, .png, .gif, .bmp, .webp, .tif, .tiff, .svg
.mp4, .mkv, .mov, .avi, .mts, .webm
.mp3, .wav, .m4a, .flac, .ogg
.py, .js, .ts, .tsx, .jsx, .css, .sql, .sh, .ps1
.srt, .vtt (Untertitel)
```

### ⚠️ Teilweise analysiert (Metadaten + Container-Info)

```
.zip, .rar, .7z, .gz, .tar, .apk
.dwg (CAD - Textelemente)
.fbx, .obj, .stl (3D - Mesh-Info)
.arw, .rw, .raw (RAW - EXIF)
.pst (Outlook - Komplex)
.iso, .dmg (Disk Images)
.vob, .ifo, .bup (DVD - als Einheit)
```

### ❌ Nur Hash + Basis-Metadaten

```
.exe, .dll, .sys, .bin, .dat
.tmp, .pyc, .pyo
.ttf, .otf, .woff (Fonts)
.mui, .manifest, .cat, .mum (System)
```

---

## Empfehlungen

### 1. Hohe Priorität für bessere Unterstützung

| Format | Anzahl | Empfehlung |
| :--- | :--- | :--- |
| **.pst** | 351 | Outlook-Archiv Parser implementieren |
| **.dwg** | 582 | ODA Converter integrieren |
| **.c4d** | 411 | Cinema4D-Export-Suche |

### 2. Ignorieren (Cleanup-Kandidaten)

| Format | Anzahl | Empfehlung |
| :--- | :--- | :--- |
| **.tmp** | 16.102 | Löschen |
| **.pyc** | 8.733 | Löschen (regenerierbar) |
| **.map** | 17.178 | Löschen (regenerierbar) |

### 3. Spezialbehandlung

| Format | Empfehlung |
| :--- | :--- |
| **.torrent** | Tracker-Info + Dateiliste indexieren |
| **.srt** | Untertitel MIT Zeitmarken indexieren |
| **.vob** | Als DVD-Einheit, nicht einzeln |

---

*Dieses Inventar wird bei der ersten Vollindexierung aktualisiert.*
