# ADR-012: Quarantäne-Schwellenwert - 50% vs. 10% Rate

## Status
**Proposed** - A/B-Test erforderlich (ABT-R04)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Bessere Schwellenwerte definieren"
- **Gemini 3 Pro:** "Wenn 50% in Quarantäne landen, hast du die Arbeit nur verschoben"

---

## Kontext und Problemstellung

Aktuelle Implementierung in `quality_gates.py`:
```python
CONFIDENCE_THRESHOLD = 0.7
LOW_CONFIDENCE_THRESHOLD = 0.5
```

- Confidence < 0.5 → Quarantäne (Hard Fail)
- Confidence 0.5-0.7 → Warnung, aber durchgelassen

**Problem:** Bei realen Daten mit OCR-Fehlern, ungewöhnlichen Formaten etc. können 30-50% der Dateien in Quarantäne landen.

**Kritikalität:** RED BUTTON - Arbeit wird verschoben, nicht gelöst

---

## Entscheidungstreiber (Decision Drivers)

* **Durchsatz:** System soll Dateien verarbeiten, nicht blockieren
* **Qualität:** Fehlerhafte Zuordnungen minimieren
* **Benutzerfreundlichkeit:** Quarantäne-Review muss handhabbar sein

---

## Betrachtete Optionen

1. **Option A (Baseline):** Aktuelle Schwellenwerte (0.5/0.7)
2. **Option B (Kandidat):** Niedrigere Schwellenwerte + Tags
3. **Option C:** Adaptive Schwellenwerte basierend auf Dateityp

---

## A/B-Test Spezifikation

### Test-ID: ABT-R04

```yaml
hypothese:
  these: "Niedrigere Quarantäne-Rate mit Tags ist besser als hohe mit Review"
  null_hypothese: "Strenge Quarantäne verhindert Fehler"

baseline:
  implementierung: "quality_gates.py mit CONFIDENCE_THRESHOLD=0.7"
  metriken:
    - name: "quarantine_rate"
      beschreibung: "Anteil Dateien in Quarantäne"
      aktueller_wert: "UNBEKANNT - zu messen auf realem Datenset"
    - name: "false_positive_rate"
      beschreibung: "Korrekt klassifiziert aber in Quarantäne"
      messmethode: "Manuelles Review von 100 Quarantäne-Dateien"
    - name: "user_review_time"
      beschreibung: "Zeit für manuelles Quarantäne-Review"
      aktueller_wert: "UNBEKANNT"

kandidat:
  implementierung: |
    CONFIDENCE_THRESHOLD = 0.5  # Gesenkt
    LOW_CONFIDENCE_THRESHOLD = 0.3  # Gesenkt

    # Neue Logik:
    # < 0.3: Quarantäne
    # 0.3-0.5: Sortieren + Tag "_review"
    # 0.5-0.7: Sortieren + Tag "_autosorted"
    # > 0.7: Sortieren ohne Tag
  erwartete_verbesserung:
    - "quarantine_rate: < 10%"
    - "Manuelle Review-Last um 80% reduziert"

testbedingungen:
  daten: "1000 Dateien aus F:/_Inbox (reale Daten)"
  messung:
    - "Quarantäne-Rate pro Schwellenwert"
    - "Manuelles Review: Wie viele waren 'false positive'?"
    - "Zeit für Tag-basiertes Review vs. Quarantäne-Review"

erfolgskriterien:
  primaer: "quarantine_rate < 15%"
  sekundaer: "false_positive_rate in Quarantäne < 20%"
  tertiaer: "Kein Anstieg von Fehlzuordnungen bei sortierten Dateien"

testscript: |
  # tests/ab_test_quarantine.py

  from quality_gates import run_quality_gates
  from collections import Counter

  def test_threshold_impact(files: list, thresholds: dict) -> dict:
      """Testet Auswirkung verschiedener Schwellenwerte."""
      results = Counter()

      for file_data in files:
          result = run_quality_gates(file_data)

          if not result.passed:
              results["quarantine"] += 1
          elif any(g.severity == "warning" for g in result.gates):
              results["tagged"] += 1
          else:
              results["clean"] += 1

      total = len(files)
      return {
          "quarantine_rate": results["quarantine"] / total,
          "tagged_rate": results["tagged"] / total,
          "clean_rate": results["clean"] / total
      }
```

---

## Tag-Strategie (Option B Detail)

```python
# Vorgeschlagene Tag-Hierarchie
TAGS = {
    "confidence < 0.3": "_quarantine",       # Manuelles Review erforderlich
    "confidence 0.3-0.5": "_review",          # Bei Gelegenheit prüfen
    "confidence 0.5-0.7": "_autosorted",      # Automatisch, aber markiert
    "confidence > 0.7": None                   # Keine Markierung
}

# Vorteile:
# - Dateien bleiben zugänglich
# - Lazy Review möglich
# - Kein Quarantäne-Stau
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option B (Tags statt Quarantäne)**

### Begründung (vorläufig)
- "Mutig sortieren" ist besser als "vorsichtig blockieren"
- Tags ermöglichen nachträgliche Korrektur ohne Blockade
- Benutzer sieht Fortschritt statt wachsende Quarantäne

---

## Konsequenzen

### Wenn Option B gewinnt (Tags)
**Positiv:**
- Höherer Durchsatz
- Weniger manuelle Arbeit
- Psychologisch: "System arbeitet"

**Negativ:**
- Mehr Fehlzuordnungen im Archiv (aber markiert)
- Tag-Cleanup erforderlich

### Wenn Option A bleibt (Strenge Quarantäne)
**Positiv:**
- Keine Fehlzuordnungen im Archiv
- Klare Trennung

**Negativ:**
- Quarantäne wächst schneller als Review
- Frustrierend für Benutzer

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - Automatisierung ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Tag-Cleanup Prozess dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Quality Gates: `scripts/quality_gates.py`
- Erfolgsalgorithmus: "Rote Knöpfe = 50% Quarantäne ist ein Problem"
