# ADR-018: PDF Parsing - Apache Tika vs. Docling

**Status**
Accepted (Hybrid PDF Parsing)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "MinerU, PDF-Extract-Kit, Docling - State of the Art 2025"
- **Gemini 3 Pro:** "Docling ist leistungsfähiger für Tabellen, ersetzt Surya effektiv"

---

## Kontext und Problemstellung

Aktuelle Implementierung:
- Apache Tika (docker: apache/tika) für Basis-Parsing
- Docling im neural-worker für "Deep Ingest"
- Zwei parallele Systeme für ähnliche Aufgabe

**Problem:**
- Doppelte Verarbeitung = doppelte Ressourcen
- Inkonsistente Ergebnisse zwischen Tika und Docling
- Tika verliert Tabellenstruktur

**Kritikalität:** BLUE BUTTON - Kernfeature konsolidieren und verbessern

---

## Entscheidungstreiber (Decision Drivers)

* **Tabellenerhalt:** Finanzberichte, Rechnungen haben Tabellen
* **Layoutverständnis:** Spalten, Header müssen erkannt werden
* **Performance:** Parsing darf nicht zu lange dauern

---

## Betrachtete Optionen

1. **Option A (Baseline):** Apache Tika (Universal)
2. **Option B (Kandidat):** Docling (KI-gestützt)
3. **Option C:** MinerU (Neuester State of Art)
4. **Option D:** Hybrid nach Dateityp

---

## Tool-Vergleich (2025)

| Feature | Tika | Docling | MinerU |
|---------|------|---------|--------|
| Tabellenextraktion | Schwach | Gut | Sehr gut |
| Layout-Analyse | Keine | Gut | Sehr gut |
| Geschwindigkeit | Schnell | Mittel | Langsam |
| RAM-Bedarf | 1GB | 2-4GB | 4-8GB |
| Sprachen | Alle | Alle | Alle |
| Maintenance | Apache | IBM | MinerU Team |

---

## A/B-Test Spezifikation

### Test-ID: ABT-B04

```yaml
hypothese:
  these: "Docling extrahiert Tabellen 50% besser als Tika"
  null_hypothese: "Tika ist für Textextraktion ausreichend"

baseline:
  implementierung: "Apache Tika via Docker (Port 9998)"
  metriken:
    - name: "table_extraction_accuracy"
      beschreibung: "Korrekt extrahierte Tabellenzellen"
      messmethode: "Ground Truth mit 50 Rechnungs-PDFs"
      aktueller_wert: "~40% (Tabellen werden zu Fließtext)"
    - name: "layout_preservation"
      beschreibung: "Struktur (Header, Absätze) erhalten"
      aktueller_wert: "Schwach"
    - name: "parsing_time"
      beschreibung: "Zeit pro Dokument"
      aktueller_wert: "~500ms"

kandidat:
  implementierung: "Docling via neural-worker (Port 8005)"
  erwartete_verbesserung:
    - "table_extraction_accuracy: >= 80%"
    - "layout_preservation: Markdown mit korrekten Headern"
    - "parsing_time: < 2000ms (akzeptabel)"

testbedingungen:
  daten:
    - "50 Rechnungen/Kontoauszüge (Tabellen kritisch)"
    - "50 Verträge (Layout kritisch)"
    - "50 Briefe (Einfacher Text)"
  ground_truth: "Manuell annotierte Tabellenstruktur"

erfolgskriterien:
  primaer: "table_extraction_accuracy Docling >= Tika + 30%"
  sekundaer: "layout_preservation subjektiv 'besser'"
  tertiaer: "parsing_time < 3x Tika"

testscript: |
  # tests/ab_test_pdf_parsing.py

  import requests
  import json
  from pathlib import Path

  def parse_with_tika(pdf_path: str) -> dict:
      with open(pdf_path, "rb") as f:
          response = requests.put(
              "http://localhost:9998/tika",
              data=f,
              headers={"Accept": "text/plain"}
          )
      return {"text": response.text, "tables": []}  # Tika liefert keine Tabellen

  def parse_with_docling(pdf_path: str) -> dict:
      response = requests.post(
          "http://localhost:8005/parse",
          json={"file_path": pdf_path, "format": "markdown"}
      )
      result = response.json()
      return {
          "text": result.get("markdown", ""),
          "tables": result.get("tables", [])
      }

  def evaluate_table_extraction(parsed: dict, ground_truth: dict) -> float:
      """Vergleicht extrahierte Tabellen mit Ground Truth."""
      if not ground_truth.get("tables"):
          return 1.0  # Kein Tabellen-Test nötig

      correct_cells = 0
      total_cells = 0

      for gt_table in ground_truth["tables"]:
          for row in gt_table["rows"]:
              for cell in row:
                  total_cells += 1
                  if cell in parsed["text"]:
                      correct_cells += 1

      return correct_cells / total_cells if total_cells > 0 else 0.0
```

---

## Empfohlene Architektur (Hybrid)

```python
def parse_document(file_path: str, doc_type: str) -> dict:
    """Wählt Parser basierend auf Dokumenttyp."""

    # Für Tabellen-lastige Dokumente: Docling
    if doc_type in ["invoice", "bank_statement", "spreadsheet"]:
        return parse_with_docling(file_path)

    # Für einfache Texte: Tika (schneller)
    if doc_type in ["letter", "contract_simple"]:
        return parse_with_tika(file_path)

    # Default: Docling (besser als fallback)
    return parse_with_docling(file_path)
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option D (Hybrid)** mit Docling als Default

### Begründung (vorläufig)
- Gemini: "Docling ersetzt Surya effektiv für Tabellen"
- Claude: "Docling + MinerU sind State of Art 2025"
- Tika für Legacy-Kompatibilität behalten, Docling für Qualität

---

## Konsequenzen

### Wenn Option B/D gewinnt (Docling)
**Positiv:**
- Deutlich bessere Tabellenextraktion
- Markdown-Output für LLM-Kontext ideal
- Layout-Verständnis für komplexe Dokumente

**Negativ:**
- Langsamere Verarbeitung
- Höherer RAM-Bedarf
- Zusätzliche Abhängigkeit

### Wenn Option A bleibt (Nur Tika)
**Positiv:**
- Schnell und einfach
- Breite Formatunterstützung

**Negativ:**
- Tabellen gehen verloren
- Suboptimal für Finanz-Dokumente

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - "Rechnungen in < 1 Min finden" |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Parser-Auswahl dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Neural Worker: `docker/neural-worker/`
- Document ETL: [ADR-004-document-etl.md](./ADR-004-document-etl.md)
