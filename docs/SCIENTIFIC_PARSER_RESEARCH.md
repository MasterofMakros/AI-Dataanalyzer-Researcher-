# Scientific Parser Research

## Ziel
Vergleich der Top-Parser für wissenschaftliche Inhalte mit Fokus auf Tabular- und Text-Extraction. Ergebnisse dienen als Grundlage für Routing-Entscheidungen und Benchmark-Planung.

## Kandidaten (Python)
| Library | Stärken | Schwächen | Typischer Einsatz |
| --- | --- | --- | --- |
| **pandas** | CSV/TSV/Excel schnell & robust, DataFrame-Export | Kein PDF-Parsing | Tabellen aus CSV/TSV/XLSX |
| **camelot** | PDF-Tabellen (lattice/stream) | Abhängig von Ghostscript | Tabellen aus PDF |
| **tabula-py** | PDF-Tabellen, stabil | Java-Dependency | Tabellen aus PDF |
| **pdfplumber** | Text + einfache Tabellen | Langsam bei großen PDFs | Text/Tabellen aus PDF |
| **PyMuPDF (fitz)** | Sehr schnell, gute Layout-Infos | Tabellen erfordern eigene Logik | Text/Koordinaten aus PDF |
| **unstructured** | Multi-Format, Layout-Parsing | Heavy, viele Abhängigkeiten | Dokument-Pipelines |
| **scienceparse** | Paper-spezifisch (Metadaten) | Training/Model nötig | wissenschaftliche Paper |
| **GROBID (Python bindings)** | Strukturierte Metadaten | Java-Service nötig | Bibliographische Extraktion |

## Kandidaten (Rust/C++)
| Library | Sprache | Stärken | Schwächen | Typischer Einsatz |
| --- | --- | --- | --- | --- |
| **pdfium** | C++ | Sehr schnell, Rendering + Text | API-Komplexität | Text/Rendering aus PDF |
| **poppler** | C++ | Solide Text-Extraktion | Tabellen-Logik extern | Text aus PDF |
| **tabula-java** | Java (C++ via JNI möglich) | Gute Tabellen-Extraction | Java-Stack | Tabellen aus PDF |
| **lopdf + pdf-extract** | Rust | Leichtgewichtig | Layout-Infos limitiert | Text aus PDF |
| **polars** | Rust | Sehr schnelle Tabellen | Kein PDF | Tabellen aus CSV/Parquet |

## Benchmarks (Dokumentation)
| Bereich | Quelle | Metrik | Relevanz |
| --- | --- | --- | --- |
| PDF-Tabellen | Docling Benchmarks (intern, 97.9% table accuracy) | Accuracy/Precision/Recall | Starker Kandidat für Tabellen |
| PDF-Parsing | Unstructured Benchmarks (blog) | Throughput, Accuracy | Vergleich Multi-Parser |
| PDF-Extraction | Procycons PDF Benchmark 2025 | Quality Scores | Vergleich Parser-Qualität |
| DataFrame | Polars/Pandas Microbenchmarks | Rows/s, Memory | Tabular Performance |

## Empfehlung (Kurz)
1. **Tabular**: pandas + (optional) camelot/tabula-py für PDF-Tabellen.
2. **Text**: PyMuPDF für Speed, pdfplumber für Qualität.
3. **Rust/C++**: pdfium/poppler als Performance-Backends, polars für große Tabellen.

## Nächste Schritte
- PDF-Tabellen-Benchmark mit 10–20 Papers (Gold-CSV) aufsetzen.
- JSON/CSV/TSV-Export messen (Row/Column Accuracy).
- Entscheidungsmatrix für Routing (Genauigkeit vs. Speed vs. Dependency).
