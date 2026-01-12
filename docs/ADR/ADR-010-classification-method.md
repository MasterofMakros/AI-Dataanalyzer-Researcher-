# ADR-010: Klassifikation - Ollama LLM vs. GLiNER NER

## Status
**Proposed** - A/B-Test erforderlich (ABT-R02)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "NER (GLiNER) + Regelwerk statt LLM - 2-5 Sek/Datei ist zu langsam"
- **Gemini 3 Pro:** "Docling + GLiNER im neural-worker bereits vorhanden"

---

## Kontext und Problemstellung

Aktuelle Implementierung in `smart_ingest.py`:
- Ollama (qwen3:8b) für Kategorie-Klassifikation
- **Problem:** 2-5 Sekunden pro Datei
- Bei 100.000 Dateien = 50-139 Stunden Verarbeitungszeit

**Kritikalität:** RED BUTTON - Performance-Blocker für Mass-Ingest

---

## Entscheidungstreiber (Decision Drivers)

* **Performance:** < 100ms pro Datei für Skalierbarkeit
* **Genauigkeit:** Mindestens 80% korrekte Kategorisierung
* **Ressourcen:** GPU-RAM begrenzt auf 12GB (RTX 3060)

---

## Betrachtete Optionen

1. **Option A (Baseline):** Ollama LLM (qwen3:8b)
2. **Option B (Kandidat):** GLiNER NER + Regelwerk
3. **Option C:** Hybrid (GLiNER für Mass-Ingest, LLM für Quarantäne-Review)

---

## A/B-Test Spezifikation

### Test-ID: ABT-R02

```yaml
hypothese:
  these: "GLiNER + Regeln ist schneller UND ausreichend genau"
  null_hypothese: "LLM ist für Genauigkeit notwendig"

baseline:
  implementierung: "smart_ingest.py mit Ollama qwen3:8b"
  metriken:
    - name: "latency_per_file"
      beschreibung: "Zeit pro Datei für Klassifikation"
      aktueller_wert: "2000-5000ms"
    - name: "classification_accuracy"
      beschreibung: "Korrekte Kategorie-Zuordnung"
      aktueller_wert: "~85% (geschätzt)"
    - name: "gpu_memory"
      beschreibung: "VRAM-Nutzung"
      aktueller_wert: "~6GB"

kandidat:
  implementierung: "neural-worker GLiNER (urchade/gliner_medium-v2.1)"
  erwartete_verbesserung:
    - "latency_per_file: < 100ms (20-50x schneller)"
    - "classification_accuracy: >= 80%"
    - "gpu_memory: < 2GB"

testbedingungen:
  daten: "500 manuell kategorisierte Dateien (Ground Truth)"
  kategorien:
    - "Finanzen: 100 Dateien (Rechnungen, Kontoauszüge)"
    - "Arbeit: 100 Dateien (Verträge, Präsentationen)"
    - "Privat: 100 Dateien (Fotos, Briefe)"
    - "Medien: 100 Dateien (Videos, Audio)"
    - "Sonstiges: 100 Dateien (Gemischt)"
  hardware: "RTX 3060 12GB, Ryzen 5700X"

erfolgskriterien:
  primaer: "latency_per_file < 200ms"
  sekundaer: "classification_accuracy >= 75%"
  tertiaer: "gpu_memory < 4GB"

testscript: |
  # tests/ab_test_classification.py

  import time
  from typing import List, Tuple

  def test_classifier(classifier, files: List[str], ground_truth: dict) -> dict:
      """Testet Klassifikator gegen Ground Truth."""
      results = {
          "latencies": [],
          "correct": 0,
          "total": len(files)
      }

      for file_path in files:
          start = time.perf_counter()
          predicted = classifier.classify(file_path)
          elapsed = (time.perf_counter() - start) * 1000  # ms

          results["latencies"].append(elapsed)
          if predicted == ground_truth.get(file_path):
              results["correct"] += 1

      results["avg_latency_ms"] = sum(results["latencies"]) / len(results["latencies"])
      results["accuracy"] = results["correct"] / results["total"]

      return results
```

---

## Ground Truth Erstellung

Für validen A/B-Test muss Ground Truth erstellt werden:

```python
# scripts/create_ground_truth.py

GROUND_TRUTH_SCHEMA = {
    "file_path": "F:/path/to/file.pdf",
    "category": "Finanzen",  # Manuelle Zuordnung
    "subcategory": "Rechnung",  # Optional
    "entities": ["Bauhaus", "127.50 EUR"],  # Erwartete Entities
    "labeler": "human",
    "date": "2025-12-28"
}
```

**Frage an User:** Existiert bereits ein Ground Truth Datenset für Klassifikation?

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf beiden KI-Analysen: **Option C (Hybrid)** als Kompromiss:
- GLiNER für schnellen Mass-Ingest (95% der Dateien)
- LLM nur für unsichere Fälle (5% → Quarantäne)

---

## Konsequenzen

### Wenn Option B/C gewinnt (GLiNER)
**Positiv:**
- 20-50x schneller
- Geringerer GPU-RAM
- Parallelisierbar

**Negativ:**
- Weniger "Verständnis" für komplexe Dokumente
- Regelwerk muss gepflegt werden

### Wenn Option A bleibt (LLM)
**Positiv:**
- Besseres semantisches Verständnis
- Flexibler bei neuen Kategorien

**Negativ:**
- Performance-Blocker für > 10k Dateien
- Hoher GPU-Bedarf

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - Skalierbarkeit ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - GLiNER-Konfiguration dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Neural Worker: `docker/neural-worker/`
- GLiNER Modell: `urchade/gliner_medium-v2.1`
