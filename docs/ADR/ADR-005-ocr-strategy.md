# ADR-005: OCR-Strategie (Multi-Tier)

## Status
**Akzeptiert** (2025-12-26)

## Kontext
Wir haben ~35.000 PDFs auf Laufwerk F:, davon viele gescannte Dokumente (Rechnungen, Belege, Kontoauszüge). Zusätzlich existieren handschriftliche Notizen (iPad, Whiteboard-Fotos). Die OCR-Genauigkeit ist kritisch für die Suchfunktion.

## Entscheidung
Wir nutzen eine **3-stufige OCR-Strategie**:

| Tier | Tool | Anwendungsfall |
| :--- | :--- | :--- |
| **Tier 1 (Fast)** | Tesseract | PDFs mit erkennbarem Text-Layer (digital erstellt) |
| **Tier 2 (Accurate)** | **Surya OCR** | Gescannte Dokumente (Rechnungen, Belege, Formulare) |
| **Tier 3 (Handwriting)** | **TrOCR** | Handschriftliche Notizen (iPad, Whiteboards) |

## Begründung

### Warum Surya OCR für Scans?
*   **Accuracy:** 97.7% auf Invoice-Benchmark (vs. 87.7% Tesseract).
*   **Speed:** 2.4 Sekunden pro Bild auf GPU (A10). CPU ist langsamer (~157s), daher GPU-Pflicht.
*   **Layout-Erkennung:** Erkennt Tabellen, Header, Fußzeilen automatisch.
*   **Lokal:** Vollständig Open Source, kein Cloud-API nötig.

### Warum TrOCR für Handschrift?
*   **Accuracy:** 96% auf SROIE Dataset (Receipts), bis 99.7% auf strukturiertem Text.
*   **Transformer-basiert:** Versteht Kontext, nicht nur Pixel.
*   **Hugging Face Integration:** Einfaches Deployment via `transformers` Library.

### Quellen (Stand Dez 2025)
*   [researchify.io](https://researchify.io): Surya OCR Benchmark (97.7% Accuracy)
*   [nhsjs.com](https://nhsjs.com): TrOCR Evaluation (96% Word Accuracy)
*   [github.com/VikParuchuri/surya](https://github.com/VikParuchuri/surya): Surya Repository

## Konsequenzen
*   **Positiv:** Höchste Accuracy für Dokument-Suche. Handschrift wird erstmals durchsuchbar.
*   **Negativ:** Surya und TrOCR benötigen **GPU-Unterstützung**.
    *   Ryzen 890M iGPU: Experimentell via ROCm (Stand Dez 2025).
    *   Fallback: CPU-Mode (langsamer, aber funktional).

## Alternativen (abgelehnt)
| Alternative | Grund für Ablehnung |
| :--- | :--- |
| **Nur Tesseract** | Zu ungenau für Scans (87.7%). Handschrift nicht unterstützt. |
| **Google Cloud Vision** | Widerspricht "Privacy First". Kosten pro Dokument. |
| **PaddleOCR** | Gut, aber Surya ist schneller und genauer auf Invoices. |

## Pipeline-Integration
```
[PDF/Scan] --> [Tika: Hat Text-Layer?]
                 |
                 +--> Ja --> [Tier 1: Tesseract] --> Qdrant
                 |
                 +--> Nein --> [Surya: Layout + OCR] --> Qdrant
                 |
                 +--> Handschrift? --> [TrOCR] --> Qdrant
```
