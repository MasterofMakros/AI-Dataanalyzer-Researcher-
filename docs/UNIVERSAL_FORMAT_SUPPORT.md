# Universal Format Support

> Neural Vault unterstützt die in `docs/capabilities/formats.md` dokumentierte Anzahl an Dateiformaten in 15 Kategorien
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

## Format-Matrix: siehe `docs/capabilities/formats.md`

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
| PSD | .psd | Metadata Extractor (ExifTool) | Metadata | ❌ |
| XCF | .xcf | Metadata Extractor (ExifTool) | Metadata | ❌ |
| ICO | .ico | Metadata Extractor (ExifTool) | Metadata | ❌ |
| SVG | .svg | Tika | Text | ❌ |
| EPS | .eps | Tika | Text | ❌ |
| AI | .ai | Metadata Extractor (ExifTool) | Metadata | ❌ |
| **RAW-Formate** | | | | |
| Canon | .cr2, .cr3 | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Nikon | .nef | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Sony | .arw | Metadata Extractor (ExifTool) | Metadata | ❌ |
| DNG | .dng | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Fuji | .raf | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Olympus | .orf | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Panasonic | .rw2 | Metadata Extractor (ExifTool) | Metadata | ❌ |
| Pentax | .pef | Metadata Extractor (ExifTool) | Metadata | ❌ |
| OpenEXR | .exr | Metadata Extractor (ExifTool) | Metadata | ❌ |

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
| Windows | .exe, .dll | Metadata Extractor (ExifTool) | Nur Metadata |
| Linux | .so | Exiftool | Nur Metadata |
| macOS | .dylib | Exiftool | Nur Metadata |
| **Verschlüsselt** | | | |
| GPG | .gpg, .pgp | Skip | Ohne Schlüssel nicht lesbar |

---

## Darstellungs-Playbook (UI/UX)

> Ziel: Jede Quelle lässt sich im Suchergebnis **verifizieren** (Ausschnitte sehen/hören) und bei Bedarf **vertiefen**.

### Quellen-Sprunglogik (LLM → Viewer)

- **Quellenanker normalisieren:** Jede evidenzierte Quelle bekommt ein `source_anchor`-Objekt mit `format`, `uri` und einem formatspezifischen Locator (z. B. `page`, `timecode`, `line_range`, `bbox`, `chapter`, `cell`).  
- **Viewer-Router:** UI wählt anhand `format` den passenden Viewer und übergibt den Locator (deeplink bzw. initiale Fokus-Position).  
- **Antwort → Evidenzen:** LLM liefert pro Antwortsatz eine Liste von Quellenankern (mit Start/Ende), die beim Klick den Viewer exakt positionieren.  

### Dokumente

- **Paginated Document Viewer (Text-Layer + Highlights):** PDF, DOCX, DOC, ODT, RTF, Apple Pages (.pages).  
- **Spreadsheet Grid + Formel-Ansicht:** XLSX, XLS, ODS, Apple Numbers (.numbers), CSV, TSV.  
- **Slide Deck Viewer (Folie/Notizen/Navigation):** PPTX, PPT, ODP, Apple Keynote (.key).  
- **Struktur-Explorer (Tree + Raw-Ansicht):** XML, JSON, YAML/YML.  
- **HTML/Markup Preview (Rendered + Source Toggle):** HTML/HTM, XHTML, MHTML, LaTeX (.tex/.latex), TXT.  

### E-Books

- **E-Book Reader (Reflow + Kapitel-Navigation):** EPUB, MOBI, AZW, AZW3, FB2.  
- **Image/Page Viewer + OCR-Overlay:** DjVu.  
- **Comic Reader (Bildstrecke + Thumbnails):** CBZ, CBR, CB7.  

### Bilder

- **Image Viewer (Zoom, EXIF, OCR-Overlay):** JPEG, PNG, BMP, TIFF, WebP, HEIC/HEIF, AVIF.  
- **Animierte Vorschau:** GIF (mit Play/Pause).  
- **Vector Viewer (SVG/PDF-Render):** SVG, EPS.  
- **Design-Dateien (Rasterized Preview + Metadata):** PSD, XCF, AI, ICO.  
- **RAW Viewer (Embedded Preview + EXIF, optional Develop):** CR2/CR3, NEF, ARW, DNG, RAF, ORF, RW2, PEF.  
- **HDR Viewer (Tone-Mapping + Layers):** EXR.  

### Audio

- **Waveform Player + Timecoded Transcript:** MP3, AAC, M4A, WAV, FLAC, ALAC, OGG, Opus, WMA, AIFF, APE.  
- **Audiobook Player (Kapitel + Speed):** M4B.  
- **MIDI Player (Synth + Piano Roll):** MID/MIDI.  

### Video

- **Video Player (Timeline + Keyframes + Transcript):** MP4/M4V, MKV, WebM, AVI, MOV, WMV, FLV, MPG/MPEG, 3GP/3G2, MXF, TS/M2TS, VOB, OGV, RM/RMVB, DivX/XviD.  

### E-Mail & Kommunikation

- **Message Viewer (Header, Body, Attachments, Thread):** EML, MSG, MBOX.  
- **Mailbox Explorer (Folder Tree + Message View):** PST, OST.  
- **Contact Card Viewer:** VCF.  
- **Calendar Event Viewer (Timeline + TZ):** ICS/ICAL.  

### Archive & Disk Images

- **File Tree + On-Demand Preview (safe extract):** ZIP, RAR, 7Z, TAR, GZ/TGZ, BZ2/TBZ2, XZ/TXZ, ZST, LZ, LZMA.  
- **Disk Image Browser (Mount/List + File Tree):** ISO, IMG, DMG, VHD/VHDX, VMDK.  

### Source Code & Markup

- **Syntax-Highlight Code Viewer:** .py, .js, .ts, .java, .c/.cpp/.cxx/.h/.hpp, .cs, .go, .rs, .rb, .php, .swift, .kt, .scala, .r, .pl, .lua, .sh, .bat, .ps1, .sql, .groovy, .dart, .ex, .erl, .hs, .clj, .fs, .ml, .asm, .cob, .f90.  
- **Rendered + Source Toggle:** Markdown (.md), reStructuredText (.rst), AsciiDoc (.adoc).  
- **Config Viewer (Key/Value + Raw):** .ini/.cfg/.conf, .toml, .properties, .env.  

### Datenbanken

- **Schema Explorer + Table Preview:** SQLite (.sqlite/.sqlite3/.db), Access (.mdb/.accdb), dBASE (.dbf).  
- **SQL Viewer (Syntax + ERD Extract):** .sql.  
- **Column Stats + Sample Rows:** Parquet, Feather, Arrow.  

### 3D-Modelle

- **WebGL 3D Viewer (Orbit/Measure + Mesh Stats):** OBJ, STL, PLY, FBX, glTF/GLB, DAE, 3DS.  
- **Metadata + Conversion Hint:** BLEND, MAX, MA/MB, C4D, SKP.  

### CAD & Engineering

- **CAD Viewer (2D/3D Render + Layers + Maßstab):** DWG, DXF, DWF, STEP/STP, IGES/IGS, SAT.  
- **Metadata + Conversion Hint:** IPT/IAM, SLDPRT/SLDASM.  

### GIS & Geodaten

- **Map Viewer (Tiles + Layer Toggle + Bounds):** SHP/SHX/DBF, GeoJSON, KML/KMZ, GPX, OSM/PBF.  

### Wissenschaftliche Formate

- **Dataset Explorer (Arrays + Plot + Stats):** MAT, NetCDF, HDF/HDF5/H5, FITS, NPY/NPZ, Parquet, Feather, Arrow.  
- **Safe Summary (No Execute) + Conversion Hint:** Pickle/PKL.  

### Schriftarten

- **Font Specimen Viewer (Alphabet, Weights, Glyph Table):** TTF, OTF, WOFF/WOFF2, EOT, PFB/PFM.  

### Spezialformate

- **Torrent Inspector (File List + Trackers):** .torrent.  
- **Subtitle Viewer (Timecodes + Search Highlights):** SRT, ASS/SSA, VTT.  
- **App Package Viewer (Manifest + Resources):** APK, IPA.  
- **Binary Inspector (Metadata + Hashes + Strings):** EXE/DLL, SO, DYLIB.  
- **Encrypted Placeholder + Decrypt Prompt:** GPG/PGP.  

---

## Quellenanker: Beispiele pro Format

- **PDF/DOCX:** `{"page": 12, "char_range": [532, 812]}` → Seite 12 öffnen, Text markieren.  
- **Audio/Video:** `{"timecode": "00:12:05", "duration": 18}` → Player an Zeitmarke springen, Segment highlighten.  
- **Tabellen:** `{"sheet": "Report", "cell": "D12"}` → Grid auf Zelle fokussieren.  
- **Code/Logs:** `{"line_range": [120, 146]}` → Zeilenbereich hervorheben.  
- **Bilder/OCR:** `{"bbox": [x, y, w, h]}` → Zoom auf OCR-Box.  
- **E-Mails:** `{"message_id": "<...>", "section": "body"}` → Nachricht/Abschnitt fokussieren.  
- **3D/CAD:** `{"view": "isometric", "layer": "Walls"}` → vordefinierte Ansicht/Layer.  
- **GIS:** `{"bbox": [minLon, minLat, maxLon, maxLat]}` → Kartenzoom auf Bounding Box.  

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
| **universal-router** | Alle (siehe `docs/capabilities/formats.md`) | 8030 |
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
