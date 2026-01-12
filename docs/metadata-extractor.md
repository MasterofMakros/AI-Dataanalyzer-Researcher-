# Metadata Extractor – Tool-Auswahl & Benchmarks

## Tool-Auswahl (Research Summary)

**Empfehlung:** ExifTool (Phil Harvey) als primärer Metadata-Extractor.

**Warum ExifTool?**
- Sehr breite Formatabdeckung (RAW, PSD, XCF, ICO, AI, EXE, u. v. m.).
- Stabile CLI, gut skriptbar und in Containern nutzbar.
- Liefert strukturierte JSON-Ausgabe (`-json`) für API-Integration.

**Verglichene Optionen (Kurzüberblick)**
| Tool | Stärken | Einschränkungen | Fazit |
| --- | --- | --- | --- |
| **ExifTool (CLI)** | Maximale Formatabdeckung, stabile Ausgabe | Perl-basiert (größerer Footprint) | **Best Fit** |
| ExifRead (Python) | Leichtgewichtig, gut für EXIF | Primär Foto-EXIF | Zu eng |
| ffprobe | Stark für Audio/Video | Kein RAW/PSD/XCF/EXE | Teilbereich |
| libmagic | Schnell für Typ-Detektion | Keine Metadaten | Nicht ausreichend |

## Benchmarks (Harness + Beispielstruktur)

Benchmarking läuft über die API (`/metadata`) und misst Latenz pro Datei.

**Script:** `tests/scripts/benchmark_metadata_extractor.py`

**Beispiel-Output (JSON)**
```json
{
  "run_id": "2024-06-01T12:00:00Z",
  "endpoint": "http://localhost:8015/metadata",
  "samples": [
    {
      "file": "tests/fixtures/metadata_samples/sample.raw",
      "duration_ms": 120.5,
      "file_type": "RAW"
    },
    {
      "file": "tests/fixtures/metadata_samples/sample.psd",
      "duration_ms": 98.2,
      "file_type": "PSD"
    },
    {
      "file": "tests/fixtures/metadata_samples/sample.exe",
      "duration_ms": 85.1,
      "file_type": "EXE"
    }
  ]
}
```

**Hinweis:** Ergebnisse hängen von Hardware/IO ab. Die Benchmark-Struktur ist so gewählt, dass sie reproduzierbar in CI/Local ausgeführt werden kann.
