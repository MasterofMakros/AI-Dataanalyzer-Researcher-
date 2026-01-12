# Universal Format Support

> Neural Vault unterstützt **200+ Dateiformate** in 15 Kategorien
> Stand: 29.12.2025

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UNIVERSAL FILE PROCESSING                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   EINGANG                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    UNIVERSAL ROUTER (:8030)                          │   │
│   │                                                                      │   │
│   │  1. Magic Byte Detection (Datei-Signatur)                           │   │
│   │  2. Container-Analyse (ZIP/OLE2/RIFF/MP4)                           │   │
│   │  3. Extension-Fallback                                               │   │
│   │  4. Priority Scoring                                                 │   │
│   │  5. Queue Routing                                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│              ┌───────────────┼───────────────┐                              │
│              ▼               ▼               ▼                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│   │  DOCUMENTS   │  │    MEDIA     │  │   SPECIAL    │                     │
│   │  30 Formate  │  │  45 Formate  │  │  125 Formate │                     │
│   └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Format-Matrix: 200+ Formate

### Kategorie 1: Dokumente (30 Formate)

| Format | Extension | Processor | Strategie | Magic Bytes |
|:-------|:----------|:----------|:----------|:------------|
| PDF | .pdf | Tika → Markdown | HTML→MD | `%PDF` |
| Word (neu) | .docx | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| Word (alt) | .doc | Tika | Text | `\xD0\xCF\x11\xE0` |
| Excel (neu) | .xlsx | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| Excel (alt) | .xls | Tika | Text | `\xD0\xCF\x11\xE0` |
| PowerPoint (neu) | .pptx | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| PowerPoint (alt) | .ppt | Tika | Text | `\xD0\xCF\x11\xE0` |
| OpenDocument Text | .odt | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| OpenDocument Calc | .ods | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| OpenDocument Pres | .odp | Tika → Markdown | HTML→MD | `PK\x03\x04` |
| Rich Text | .rtf | Tika | Text | `{\rtf` |
| Plain Text | .txt | Tika | Text | - |
| CSV | .csv | Tika | Text | - |
| TSV | .tsv | Tika | Text | - |
| XML | .xml | Tika | Text | - |
| JSON | .json | Tika | Text | - |
| YAML | .yaml, .yml | Tika | Text | - |
| HTML | .html, .htm | Tika → Markdown | HTML→MD | - |
| XHTML | .xhtml | Tika → Markdown | HTML→MD | - |
| MHTML | .mhtml | Tika | Text | - |
| LaTeX | .tex, .latex | Pandoc | Text | - |
| Apple Pages | .pages | Tika | Text | `PK\x03\x04` |
| Apple Numbers | .numbers | Tika | Text | `PK\x03\x04` |
| Apple Keynote | .key | Tika | Text | `PK\x03\x04` |

### Kategorie 2: E-Books (12 Formate)

| Format | Extension | Processor | Strategie |
|:-------|:----------|:----------|:----------|
| EPUB | .epub | Tika → Markdown | HTML→MD |
| Kindle | .mobi | E-Book Parser | Text |
| Kindle 8 | .azw, .azw3 | E-Book Parser | Text |
| FictionBook | .fb2 | Tika | Text |
| DjVu | .djvu | DjVu Parser | OCR |
| Comic (ZIP) | .cbz | Archive → OCR | Listing + OCR |
| Comic (RAR) | .cbr | Archive → OCR | Listing + OCR |
| Comic (7z) | .cb7 | Archive → OCR | Listing + OCR |

### Kategorie 3: Bilder (25 Formate)

| Format | Extension | Processor | Strategie | OCR |
|:-------|:----------|:----------|:----------|:----|
| JPEG | .jpg, .jpeg | Tesseract | OCR | ✅ |
| PNG | .png | Tesseract | OCR | ✅ |
| GIF | .gif | Exiftool | Metadata | ❌ |
| BMP | .bmp | Tesseract | OCR | ✅ |
| TIFF | .tiff, .tif | Tesseract | OCR | ✅ |
| WebP | .webp | Tesseract | OCR | ✅ |
| HEIC/HEIF | .heic, .heif | Tesseract | OCR | ✅ |
| AVIF | .avif | Tesseract | OCR | ✅ |
| PSD | .psd | Exiftool | Metadata | ❌ |
| XCF | .xcf | Exiftool | Metadata | ❌ |
| ICO | .ico | Exiftool | Metadata | ❌ |
| SVG | .svg | Tika | Text | ❌ |
| EPS | .eps | Tika | Text | ❌ |
| AI | .ai | Exiftool | Metadata | ❌ |
| **RAW-Formate** | | | | |
| Canon | .cr2, .cr3 | Exiftool | Metadata | ❌ |
| Nikon | .nef | Exiftool | Metadata | ❌ |
| Sony | .arw | Exiftool | Metadata | ❌ |
| DNG | .dng | Exiftool | Metadata | ❌ |
| Fuji | .raf | Exiftool | Metadata | ❌ |
| Olympus | .orf | Exiftool | Metadata | ❌ |
| Panasonic | .rw2 | Exiftool | Metadata | ❌ |
| Pentax | .pef | Exiftool | Metadata | ❌ |
| OpenEXR | .exr | Exiftool | Metadata | ❌ |

### Kategorie 4: Audio (20 Formate)

| Format | Extension | Processor | Strategie | Transkription |
|:-------|:----------|:----------|:----------|:--------------|
| MP3 | .mp3 | Whisper | Transcribe | ✅ |
| AAC | .aac | Whisper | Transcribe | ✅ |
| M4A | .m4a | Whisper | Transcribe | ✅ |
| WAV | .wav | Whisper | Transcribe | ✅ |
| FLAC | .flac | Whisper | Transcribe | ✅ |
| ALAC | .alac | Whisper | Transcribe | ✅ |
| OGG | .ogg | Whisper | Transcribe | ✅ |
| Opus | .opus | Whisper | Transcribe | ✅ |
| WMA | .wma | Whisper | Transcribe | ✅ |
| AIFF | .aiff | Whisper | Transcribe | ✅ |
| APE | .ape | Whisper | Transcribe | ✅ |
| Audiobook | .m4b | Whisper (Deep) | Transcribe | ✅ |
| MIDI | .mid, .midi | FFmpeg | Metadata | ❌ |

### Kategorie 5: Video (25 Formate)

| Format | Extension | Processor | Strategie |
|:-------|:----------|:----------|:----------|
| MP4 | .mp4, .m4v | FFmpeg → Whisper | Audio Extract → Transcribe |
| MKV | .mkv | FFmpeg → Whisper | Audio Extract → Transcribe |
| WebM | .webm | FFmpeg → Whisper | Audio Extract → Transcribe |
| AVI | .avi | FFmpeg → Whisper | Audio Extract → Transcribe |
| MOV | .mov | FFmpeg → Whisper | Audio Extract → Transcribe |
| WMV | .wmv | FFmpeg → Whisper | Audio Extract → Transcribe |
| FLV | .flv | FFmpeg → Whisper | Audio Extract → Transcribe |
| MPEG | .mpg, .mpeg | FFmpeg → Whisper | Audio Extract → Transcribe |
| 3GP | .3gp, .3g2 | FFmpeg → Whisper | Audio Extract → Transcribe |
| MXF | .mxf | FFmpeg → Whisper | Audio Extract → Transcribe |
| TS | .ts, .m2ts | FFmpeg → Whisper | Audio Extract → Transcribe |
| VOB | .vob | FFmpeg → Whisper | Audio Extract → Transcribe |
| OGV | .ogv | FFmpeg → Whisper | Audio Extract → Transcribe |
| RealMedia | .rm, .rmvb | FFmpeg → Whisper | Audio Extract → Transcribe |
| DivX/XviD | .divx, .xvid | FFmpeg → Whisper | Audio Extract → Transcribe |

### Kategorie 6: E-Mail & Kommunikation (15 Formate)

| Format | Extension | Processor | Strategie | Priority |
|:-------|:----------|:----------|:----------|:---------|
| Email | .eml | Email Parser | Struktur | +25 |
| Outlook | .msg | Email Parser | Struktur | +25 |
| Mailbox | .mbox | Email Parser | Struktur | +25 |
| Outlook Archive | .pst | Email Parser | Struktur | +25 |
| Outlook Offline | .ost | Email Parser | Struktur | +25 |
| vCard | .vcf | Tika | Struktur | +20 |
| iCalendar | .ics, .ical | Tika | Struktur | +20 |

### Kategorie 7: Archive (20 Formate)

| Format | Extension | Processor | Strategie |
|:-------|:----------|:----------|:----------|
| ZIP | .zip | 7-Zip | Listing |
| RAR | .rar | 7-Zip | Listing |
| 7-Zip | .7z | 7-Zip | Listing |
| TAR | .tar | 7-Zip | Listing |
| GZIP | .gz, .tgz | 7-Zip | Listing |
| BZIP2 | .bz2, .tbz2 | 7-Zip | Listing |
| XZ | .xz, .txz | 7-Zip | Listing |
| Zstandard | .zst | 7-Zip | Listing |
| LZ | .lz | 7-Zip | Listing |
| LZMA | .lzma | 7-Zip | Listing |
| **Disk Images** | | | |
| ISO | .iso | 7-Zip | Listing |
| IMG | .img | 7-Zip | Listing |
| DMG | .dmg | 7-Zip | Listing |
| VHD | .vhd, .vhdx | 7-Zip | Listing |
| VMDK | .vmdk | 7-Zip | Listing |

### Kategorie 8: Source Code (40 Formate)

| Sprache | Extensions |
|:--------|:-----------|
| Python | .py |
| JavaScript | .js |
| TypeScript | .ts |
| Java | .java |
| C/C++ | .c, .cpp, .cxx, .h, .hpp |
| C# | .cs |
| Go | .go |
| Rust | .rs |
| Ruby | .rb |
| PHP | .php |
| Swift | .swift |
| Kotlin | .kt |
| Scala | .scala |
| R | .r |
| Perl | .pl |
| Lua | .lua |
| Shell | .sh |
| Batch | .bat |
| PowerShell | .ps1 |
| SQL | .sql |
| Groovy | .groovy |
| Dart | .dart |
| Elixir | .ex |
| Erlang | .erl |
| Haskell | .hs |
| Clojure | .clj |
| F# | .fs |
| OCaml | .ml |
| Assembly | .asm |
| COBOL | .cob |
| Fortran | .f90 |
| **Markup & Config** | |
| Markdown | .md |
| reStructuredText | .rst |
| AsciiDoc | .adoc |
| INI | .ini, .cfg, .conf |
| TOML | .toml |
| Properties | .properties |
| Environment | .env |

### Kategorie 9: Datenbanken (15 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| SQLite | .sqlite, .sqlite3, .db | DB Parser |
| Access | .mdb, .accdb | DB Parser |
| dBASE | .dbf | DB Parser |
| SQL Dump | .sql | Text |
| Parquet | .parquet | Scientific Parser |
| Feather | .feather | Scientific Parser |
| Arrow | .arrow | Scientific Parser |

### Kategorie 10: 3D-Modelle (15 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| Wavefront | .obj | Trimesh |
| STL | .stl | Trimesh |
| PLY | .ply | Trimesh |
| FBX | .fbx | Trimesh |
| glTF | .gltf, .glb | Trimesh |
| Collada | .dae | Trimesh |
| 3D Studio | .3ds | Trimesh |
| Blender | .blend | Metadata |
| 3ds Max | .max | Metadata |
| Maya | .ma, .mb | Metadata |
| Cinema 4D | .c4d | Metadata |
| SketchUp | .skp | Metadata |

### Kategorie 11: CAD & Engineering (12 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| AutoCAD | .dwg | CAD Parser |
| DXF | .dxf | CAD Parser |
| DWF | .dwf | CAD Parser |
| STEP | .step, .stp | CAD Parser |
| IGES | .iges, .igs | CAD Parser |
| SAT | .sat | CAD Parser |
| Inventor | .ipt, .iam | Metadata |
| SolidWorks | .sldprt, .sldasm | Metadata |

### Kategorie 12: GIS & Geodaten (10 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| Shapefile | .shp, .shx, .dbf | GIS Parser |
| GeoJSON | .geojson | Tika |
| KML | .kml, .kmz | Tika |
| GPX | .gpx | Tika |
| OSM | .osm, .pbf | GIS Parser |

### Kategorie 13: Wissenschaftliche Formate (15 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| MATLAB | .mat | Scientific Parser |
| NetCDF | .nc | Scientific Parser |
| HDF4/5 | .hdf, .hdf5, .h5 | Scientific Parser |
| FITS | .fits, .fit | Scientific Parser |
| NumPy | .npy, .npz | Scientific Parser |
| Pickle | .pickle, .pkl | Scientific Parser |
| Parquet | .parquet | Scientific Parser |
| Feather | .feather | Scientific Parser |
| Arrow | .arrow | Scientific Parser |

### Kategorie 14: Schriftarten (8 Formate)

| Format | Extension | Processor |
|:-------|:----------|:----------|
| TrueType | .ttf | Font Parser |
| OpenType | .otf | Font Parser |
| WOFF | .woff, .woff2 | Font Parser |
| EOT | .eot | Font Parser |
| PostScript | .pfb, .pfm | Font Parser |

### Kategorie 15: Spezialformate (20 Formate)

| Format | Extension | Processor | Notes |
|:-------|:----------|:----------|:------|
| Torrent | .torrent | Binary Parser | Dateiliste, Tracker |
| **Untertitel** | | | |
| SubRip | .srt | Tika | Direkter Text |
| ASS/SSA | .ass, .ssa | Tika | Direkter Text |
| WebVTT | .vtt | Tika | Direkter Text |
| **Apps** | | | |
| Android | .apk | Archive | Manifest |
| iOS | .ipa | Archive | Manifest |
| **Executables** | | | |
| Windows | .exe, .dll | Exiftool | Nur Metadata |
| Linux | .so | Exiftool | Nur Metadata |
| macOS | .dylib | Exiftool | Nur Metadata |
| **Verschlüsselt** | | | |
| GPG | .gpg, .pgp | Skip | Ohne Schlüssel nicht lesbar |

---

## Magic Byte Detection

Der Router erkennt Dateien anhand ihrer **Magic Bytes** (Datei-Signatur):

| Signatur (Hex) | Format | Bytes |
|:---------------|:-------|:------|
| `25 50 44 46` | PDF | `%PDF` |
| `50 4B 03 04` | ZIP-basiert | `PK\x03\x04` |
| `D0 CF 11 E0` | OLE2 (Office) | - |
| `FF D8 FF` | JPEG | - |
| `89 50 4E 47` | PNG | `\x89PNG` |
| `47 49 46 38` | GIF | `GIF8` |
| `52 49 46 46` | RIFF (WAV/AVI) | `RIFF` |
| `1A 45 DF A3` | MKV/WebM | - |
| `66 74 79 70` | MP4/MOV | `ftyp` |
| `52 61 72 21` | RAR | `Rar!` |
| `37 7A BC AF` | 7-Zip | `7z` |
| `1F 8B` | GZIP | - |
| `4D 5A` | EXE/DLL | `MZ` |
| `7F 45 4C 46` | ELF (Linux) | `\x7fELF` |

---

## Container-Analyse

### ZIP-basierte Formate

Der Router öffnet ZIP-Archive und prüft den Inhalt:

| Inhalt | Erkanntes Format |
|:-------|:-----------------|
| `word/document.xml` | DOCX |
| `xl/workbook.xml` | XLSX |
| `ppt/presentation.xml` | PPTX |
| `content.xml` | ODT/ODS/ODP |
| `META-INF/container.xml` | EPUB |
| `AndroidManifest.xml` | APK |
| `Payload/` | IPA |

### OLE2-basierte Formate

| Stream | Erkanntes Format |
|:-------|:-----------------|
| `WordDocument` | DOC |
| `Workbook` | XLS |
| `PowerPoint Document` | PPT |
| `__substg1.0_` | MSG |

### RIFF-Container

| FourCC | Erkanntes Format |
|:-------|:-----------------|
| `WAVE` | WAV |
| `AVI ` | AVI |
| `WEBP` | WebP |

### MP4/MOV Container (ftyp)

| Brand | Erkanntes Format |
|:------|:-----------------|
| `isom`, `mp41`, `mp42` | MP4 |
| `M4V ` | M4V |
| `M4A ` | M4A |
| `M4B ` | M4B (Audiobook) |
| `qt  ` | MOV |
| `3gp4`, `3gp5` | 3GP |

---

## Processing-Strategien

| Strategie | Beschreibung | Beispiel |
|:----------|:-------------|:---------|
| **TEXT** | Direkter Textinhalt | TXT, CSV, Code |
| **HTML_TO_MD** | HTML → Markdown | PDF, DOCX, HTML |
| **OCR** | Bilderkennung | JPG, PNG, TIFF |
| **TRANSCRIBE** | Audio → Text | MP3, WAV, MP4 |
| **METADATA** | Nur Metadaten | RAW, PSD, EXE |
| **LISTING** | Dateiliste | ZIP, RAR, ISO |
| **STRUCTURE** | Strukturierte Daten | EML, DB, JSON |
| **BINARY** | Binäranalyse | Unbekannt |
| **SKIP** | Überspringen | Verschlüsselt |

---

## Docker-Services

| Service | Formate | Port |
|:--------|:--------|:-----|
| **universal-router** | Alle 200+ | 8030 |
| **tika** | Dokumente (30) | 9998 |
| **whisper-fast** | Audio Fast (20) | 9001 |
| **whisper-accurate** | Audio Deep (20) | 9002 |
| **ffmpeg** | Video (25) | - |
| **tesseract** | Images OCR (15) | - |
| **parser-service** | Special (50) | 8002 |
| **7zip** | Archive (20) | - |

---

## Schnellstart

```bash
# 1. Router starten
docker compose -f docker-compose.intelligence.yml up -d universal-router

# 2. Datei routen
curl -X POST http://localhost:8030/route \
  -H "Content-Type: application/json" \
  -d '{"filepath": "/mnt/data/dokument.pdf"}'

# Response:
# {
#   "extension": "pdf",
#   "mime_type": "application/pdf",
#   "detection_method": "magic",
#   "target_queue": "extract:documents:pdf",
#   "priority": 65,
#   "processing_path": "deep"
# }

# 3. Batch-Routing
curl -X POST http://localhost:8030/route/batch \
  -H "Content-Type: application/json" \
  -d '{"filepaths": ["/mnt/data/file1.pdf", "/mnt/data/file2.mp3"]}'

# 4. Dateityp erkennen (ohne Queue)
curl -X POST http://localhost:8030/detect \
  -d '{"filepath": "/mnt/data/mystery_file"}'

# 5. Alle unterstützten Formate
curl http://localhost:8030/formats
```

---

## Erweiterung

Neue Formate hinzufügen in `config/format_registry.py`:

```python
register(FormatSpec(
    extension="xyz",
    name="XYZ Format",
    mime_types=["application/x-xyz"],
    category="custom",
    processor=ProcessorType.TIKA,
    strategy=ExtractionStrategy.TEXT,
    magic_bytes=b"XYZ\x00",
    priority_boost=10
))
```

---

*Dokumentation: 29.12.2025*
