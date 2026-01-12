# ADR-004: Dokument-ETL-Pipeline

## Status
**Akzeptiert** (2025-12-26, Rev. 2)

## Kontext
Wir müssen diverse Dokumentenformate (PDF, DOCX, EML, HTML, etc.) parsen, Text extrahieren und für die semantische Suche vorbereiten. Die Pipeline muss lokal laufen und mit 10TB+ skalieren. Besondere Herausforderung: Komplexe Tabellen und mathematische Formeln.

## Entscheidung
Wir nutzen eine **mehrstufige Pipeline**:

| Tier | Tool | Funktion |
| :--- | :--- | :--- |
| **Tier 1 (Triage)** | Apache Tika | Dateityp-Erkennung, Quick-Text-Extraction (1400+ Formate) |
| **Tier 2 (Deep Parse)** | **IBM Docling** | Tabellen, Formeln, Layout-Erhaltung, Office-Dateien |
| **Tier 3 (OCR)** | Surya / TrOCR | Siehe ADR-005 |
| **Indexierung** | LlamaIndex | Embedding + Chunking -> Qdrant |

## Begründung

### Warum IBM Docling statt Unstructured.io?

| Kriterium | **IBM Docling** | Unstructured.io |
| :--- | :--- | :--- |
| **Table Accuracy** | **97.9%** (Nested Tables) | 75% (Complex), 100% (Simple) |
| **Office-Parsing** | Native (DOCX, PPTX, XLSX) | Erfordert LibreOffice |
| **Formeln (LaTeX)** | ✅ Via Granite VLM | ⚠️ Begrenzt |
| **License** | Apache 2.0 (Open Source) | Open Core + Commercial |
| **VLM Integration** | Granite Docling (258M Params) | Optional |

### Quellen (Stand Dez 2025)
*   [procycons.com](https://procycons.com): Docling vs. Unstructured Benchmark (97.9% vs. 75% Table Accuracy)
*   [ibm.com](https://ibm.com): Granite Docling VLM Release Notes (Sept 2025)
*   [geeksforgeeks.org](https://geeksforgeeks.org): Docling Overview

### Granite Docling VLM (Neu Sept 2025)
Ein kompaktes Vision-Language-Model (258M Parameter), das:
*   OCR, Tabellen, Formeln, Code und Charts in einem Modell verarbeitet.
*   Regionengesteuerte Inferenz bietet (nur relevante Teile analysieren).
*   Apache 2.0 lizenziert ist.

## Konsequenzen
*   **Positiv:** Höchste Accuracy für Tabellen. Keine LibreOffice-Abhängigkeit. Vollständig lokal.
*   **Negativ:** Docling ist neuer (weniger Community-Erfahrung als Unstructured). Granite VLM benötigt GPU.

## Alternativen (abgelehnt)
| Alternative | Grund für Ablehnung |
| :--- | :--- |
| **Nur Apache Tika** | Kann keine komplexen Tabellen/Layouts erkennen. |
| **Unstructured.io** | Schlechtere Table Accuracy (75% vs. 97.9%). Erfordert LibreOffice für Office-Dateien. |
| **LangChain** | Höherer Overhead als LlamaIndex für reines ETL. Besser für Agenten. |

## Der Datenfluss
```
[Datei] --> [Tika: Typ + Quick-Text]
              |
              +--> Text OK? --> [LlamaIndex: Chunk + Embed] --> Qdrant
              |
              +--> Komplex (Tables/Formeln)? --> [Docling] --> LlamaIndex --> Qdrant
              |
              +--> Scan/Handschrift? --> [Surya/TrOCR] --> LlamaIndex --> Qdrant
              |
              +--> Office-Datei? --> [Docling (Native)] --> LlamaIndex --> Qdrant
```

## Installation (Docling)
```bash
pip install docling
# Optional: Granite VLM für erweiterte Features
pip install docling[vlm]
```
