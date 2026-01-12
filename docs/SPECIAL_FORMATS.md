# Spezialformate: Verarbeitungsstrategie

> **Wie werden exotische Dateiformate verarbeitet?**

*Stand: 2025-12-26*

---

## 1. Übersicht: Format-Kategorien

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATEI-KLASSIFIZIERUNG                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ STANDARD        │  │ SPEZIALIST      │  │ LEGACY/EXOTISCH │         │
│  │ (Vollanalyse)   │  │ (Tool-basiert)  │  │ (Basis-Index)   │         │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤         │
│  │ PDF, DOCX       │  │ WAV, FLAC       │  │ SHAPR, DWG      │         │
│  │ JPG, PNG        │  │ WMA, OGG        │  │ ISO, DMG        │         │
│  │ MP4, MKV        │  │ MOV, AVI        │  │ VOB (DVD)       │         │
│  │ MP3, M4A        │  │ VIDEO_TS        │  │ VCD, SVCD       │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                         │
│  Volltext + OCR      Metadaten + Audio    Hash + Container-Info        │
│  + Embedding         + Transkript         + ggf. Extraktion            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Audio-Formate

### WAV (Waveform Audio)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | Python `wave`, `pydub`, Faster-Whisper |
| **Extrahiert** | Dauer, Sample-Rate, Channels, Bit-Depth |
| **Transkription** | ✅ Ja (wenn Sprache erkannt) |

```json
{
  "content_type": "audio/wav",
  "duration_seconds": 245,
  "sample_rate": 44100,
  "channels": 2,
  "bit_depth": 16,
  "is_music": false,
  "is_voice": true,
  "transcript_timestamped": [...],
  "meta_description": "Voice Memo: Besprechungsnotizen vom 15.08.2024..."
}
```

### WMA (Windows Media Audio)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | FFprobe, Mutagen, Faster-Whisper |
| **Extrahiert** | WMA-Tags (Titel, Artist, Album), Bitrate |
| **Transkription** | ✅ Ja (Konvertierung zu WAV intern) |

```json
{
  "content_type": "audio/x-ms-wma",
  "duration_seconds": 312,
  "bitrate_kbps": 192,
  "wma_tags": {
    "title": "Meeting Recording 2024-05-12",
    "artist": "Windows Sound Recorder"
  },
  "transcript_timestamped": [...],
  "meta_description": "WMA-Aufnahme: Meeting-Mitschnitt vom 12.05.2024..."
}
```

---

## 3. Video-Formate

### MOV (Apple QuickTime)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | FFprobe, Faster-Whisper, CLIP |
| **Extrahiert** | Codec, Auflösung, Dauer, GPS (wenn iPhone), Audio-Transkript |
| **Besonderheit** | HEVC/ProRes Codecs, HDR-Metadaten |

```json
{
  "content_type": "video/quicktime",
  "duration_seconds": 180,
  "resolution": "3840x2160",
  "codec_video": "hevc",
  "codec_audio": "aac",
  "fps": 60,
  "hdr": true,
  "creation_software": "iPhone 15 Pro",
  "gps": {
    "latitude": 48.1351,
    "longitude": 11.5820
  },
  "transcript_timestamped": [...],
  "meta_description": "iPhone-Video aus München (4K HDR, 3 Min). Stadtspaziergang..."
}
```

### VIDEO_TS / VOB (DVD-Struktur)

**Das sehe ich in deinem Screenshot!**

| Attribut | Wert |
| :--- | :--- |
| **Struktur** | `VIDEO_TS/` Ordner mit .VOB, .IFO, .BUP Dateien |
| **Tool** | FFprobe, `lsdvd`, HandBrake CLI |
| **Strategie** | Als EINHEIT behandeln, nicht einzelne .VOB-Dateien |

**Verarbeitungsstrategie:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DVD-ORDNER ERKENNUNG                                                   │
│                                                                         │
│  Hunting Hitler Season 2/                                               │
│  └── Disc 2/                                                            │
│      ├── 0012FA/           ← Ignorieren (Kopierschutz-Reste)           │
│      └── VIDEO_TS/         ← ⭐ Das ist die DVD                         │
│          ├── VIDEO_TS.BUP  ← Backup der IFO                            │
│          ├── VIDEO_TS.IFO  ← DVD-Menü-Struktur                         │
│          ├── VIDEO_TS.VOB  ← Menü-Video                                │
│          ├── VTS_01_0.VOB  ← Titel 1, Teil 0 (evtl. Intro)             │
│          ├── VTS_01_1.VOB  ← Titel 1, Teil 1 (Hauptfilm Segment 1)     │
│          ├── VTS_01_2.VOB  ← Titel 1, Teil 2 (Hauptfilm Segment 2)     │
│          └── ...                                                        │
│                                                                         │
│  VERARBEITUNG:                                                          │
│  1. Erkenne VIDEO_TS als DVD-Struktur                                  │
│  2. Lese IFO für Kapitelmarken + Titel                                 │
│  3. Transkribiere Audio aus größtem VOB-Set                            │
│  4. Indexiere als EINE Einheit (nicht 8 einzelne Dateien)              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Extrahierte Metadaten:**

```json
{
  "content_type": "video/dvd",
  "is_dvd_structure": true,
  "dvd_path": "F:/Datenpool Gesellschaftsaechitektur/Hunting Hitler/Hunting Hitler Season 2/Disc 2/VIDEO_TS",
  
  "titles": [
    {
      "title_number": 1,
      "duration_seconds": 2640,
      "chapters": [
        {"chapter": 1, "start": 0, "title": "Opening"},
        {"chapter": 2, "start": 180, "title": "Chapter 2"},
        {"chapter": 3, "start": 420, "title": "Chapter 3"}
      ],
      "audio_tracks": [
        {"language": "en", "format": "AC3", "channels": "5.1"},
        {"language": "de", "format": "AC3", "channels": "2.0"}
      ],
      "subtitles": ["en", "de", "fr"]
    }
  ],
  
  "total_size_bytes": 4500000000,
  "vob_files": ["VTS_01_1.VOB", "VTS_01_2.VOB", "..."],
  
  "transcript_timestamped": [
    {"start": 0, "end": 5, "text": "Previously on Hunting Hitler...", "language": "en"}
  ],
  
  "meta_description": "DVD: Hunting Hitler Season 2, Disc 2. Dokumentation über die Suche nach Hitler-Fluchtrouten. 44 Minuten, Englisch mit deutschen Untertiteln. 6 Kapitel."
}
```

---

## 4. CAD-Formate

### DWG (AutoCAD)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | ODA File Converter (Open Design Alliance), LibreDWG |
| **Extrahiert** | Layer-Namen, Block-Namen, Textelemente, Bemaßungen |
| **Vorschau** | Konvertierung zu PNG/PDF möglich |

```json
{
  "content_type": "application/acad",
  "dwg_version": "AutoCAD 2024",
  "layers": ["0", "Walls", "Doors", "Electrical", "Furniture"],
  "blocks": ["Door_90cm", "Window_120cm", "Outlet_Schuko"],
  "text_elements": [
    "Grundriss EG",
    "Maßstab 1:100",
    "Wohnfläche: 85m²"
  ],
  "dimensions": ["3.50m", "4.20m", "2.80m"],
  "bounding_box": {"width": 12.5, "height": 8.3, "unit": "m"},
  
  "meta_description": "AutoCAD-Zeichnung: Grundriss Erdgeschoss. Enthält Layer für Wände, Türen, Elektro. Wohnfläche 85m², Maßstab 1:100."
}
```

### SHAPR (Shapr3D)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | Begrenzt! Shapr3D ist proprietär |
| **Strategie** | Export-Formate indexieren (wenn vorhanden) |
| **Fallback** | Nur Dateiname + Größe + Datum |

```json
{
  "content_type": "application/x-shapr3d",
  "is_proprietary": true,
  "fallback_mode": true,
  
  "file_size_bytes": 15728640,
  "original_filename": "Möbeldesign_Regal.shapr",
  "file_created_at": "2024-03-15T14:30:00",
  
  "associated_exports": [
    {"format": "STEP", "path": "Möbeldesign_Regal.step", "indexed": true},
    {"format": "STL", "path": "Möbeldesign_Regal.stl", "indexed": true}
  ],
  
  "meta_description": "Shapr3D-Datei: Möbeldesign Regal. Erstellt am 15.03.2024. Zugehörige Exporte: STEP, STL vorhanden."
}
```

**Workaround für Shapr3D:**
1. Suche nach Export-Dateien im selben Ordner (.step, .stl, .obj)
2. Indexiere diese stattdessen
3. Verlinke die .shapr als "Quelldatei"

---

## 5. Legacy/Container-Formate

### ISO (Disk Image)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | Python `pycdlib`, 7-Zip |
| **Strategie** | Inhaltsliste indexieren, NICHT extrahieren |

```json
{
  "content_type": "application/x-iso9660-image",
  "iso_label": "UBUNTU_22_04_LTS",
  "total_size_bytes": 3758096384,
  "file_count": 1247,
  "folder_count": 89,
  
  "contents_sample": [
    "/boot/grub/grub.cfg",
    "/casper/vmlinuz",
    "/casper/initrd",
    "/.disk/info"
  ],
  
  "meta_description": "ISO-Image: Ubuntu 22.04 LTS. Größe: 3.5 GB, enthält 1247 Dateien. Linux Installations-Medium."
}
```

### DMG (macOS Disk Image)

| Attribut | Wert |
| :--- | :--- |
| **Tool** | `dmg2img`, 7-Zip |
| **Extrahiert** | Volume-Name, Inhaltsliste |

---

## 6. Entscheidungsmatrix: Was wird wie verarbeitet?

| Format | Volltext | Transkript | Metadaten | Vorschau | Hinweis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WAV** | ❌ | ✅ | ✅ | ❌ | Audio → Whisper |
| **WMA** | ❌ | ✅ | ✅ | ❌ | Konvertierung nötig |
| **MOV** | ❌ | ✅ | ✅ | ✅ | Thumbnail |
| **VIDEO_TS** | ❌ | ✅ | ✅ | ✅ | Als Einheit behandeln |
| **VOB** | ⚠️ | ✅ | ✅ | ⚠️ | Teil von DVD, nicht einzeln |
| **DWG** | ✅ | ❌ | ✅ | ✅ | Textelemente extrahieren |
| **SHAPR** | ❌ | ❌ | ⚠️ | ❌ | Proprietär, Fallback-Modus |
| **ISO** | ⚠️ | ❌ | ✅ | ❌ | Inhaltsliste, nicht entpacken |

---

## 7. Spezieller Workflow: DVD-Sammlung

Für deine "Hunting Hitler" DVDs:

```python
def process_dvd_folder(path: str) -> dict:
    """
    Verarbeitet einen VIDEO_TS Ordner als DVD-Einheit.
    """
    # 1. Erkenne DVD-Struktur
    video_ts_path = find_video_ts(path)
    if not video_ts_path:
        return None
    
    # 2. Lese DVD-Metadaten aus IFO
    ifo_path = os.path.join(video_ts_path, "VIDEO_TS.IFO")
    dvd_info = parse_ifo(ifo_path)  # Kapitel, Sprachen, Dauer
    
    # 3. Finde Haupttitel (längster Titel = Film)
    main_title = max(dvd_info["titles"], key=lambda t: t["duration"])
    
    # 4. Extrahiere Audio für Transkription
    audio_track = extract_audio_from_vobs(
        video_ts_path, 
        main_title["vob_files"],
        language="de"  # Bevorzugt Deutsch
    )
    
    # 5. Transkribiere mit Whisper
    transcript = whisper.transcribe(audio_track, timestamps=True)
    
    # 6. Erstelle Meta-Beschreibung
    meta = generate_meta_description(
        source="DVD",
        title=extract_title_from_path(path),  # "Hunting Hitler Season 2"
        duration=main_title["duration"],
        languages=main_title["audio_tracks"],
        chapters=main_title["chapters"]
    )
    
    # 7. Indexiere als EINE Einheit
    return {
        "id": hash_path(video_ts_path),
        "type": "dvd",
        "path": path,
        "meta_description": meta,
        "transcript_timestamped": transcript,
        "dvd_info": dvd_info
    }
```

**Ergebnis für deine DVD:**

```json
{
  "type": "dvd",
  "path": "F:/Datenpool Gesellschaftsaechitektur/Hunting Hitler/Hunting Hitler Season 2/Disc 2",
  
  "meta_description": "DVD: Hunting Hitler Season 2, Disc 2. History-Channel-Dokumentation über die Suche nach möglichen Hitler-Fluchtrouten nach Südamerika. Laufzeit: 44 Minuten. Sprachen: Englisch, Deutsch. 6 Kapitel.",
  
  "series_info": {
    "series": "Hunting Hitler",
    "season": 2,
    "disc": 2
  },
  
  "searchable_content": "Previously on Hunting Hitler... Bob Baer und sein Team untersuchen Berichte über ein U-Boot... Die Suche führt nach Argentinien..."
}
```

---

## 8. Zusammenfassung

| Format-Kategorie | Strategie | Suchbar über |
| :--- | :--- | :--- |
| **Standard-Audio** (WAV, WMA) | Transkription | Gesprochener Text |
| **Standard-Video** (MOV, AVI) | Transkription + Frames | Text + Bildbeschreibung |
| **DVD** (VIDEO_TS) | Als Einheit, Transkription | Gesamter Inhalt |
| **CAD** (DWG) | Textelemente extrahieren | Layer, Blöcke, Bemaßungen |
| **Proprietär** (SHAPR) | Fallback auf Exports | Verknüpfte STEP/STL |
| **Container** (ISO) | Inhaltsliste | Dateinamen im Image |

---

*Alle Formate werden indexiert – die Tiefe der Analyse hängt vom Formattyp ab.*
