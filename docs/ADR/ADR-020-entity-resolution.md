# ADR-020: Entity Resolution - Exact Match vs. Fuzzy Resolution

## Status
**Proposed** - A/B-Test erforderlich (ABT-N01)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Fuzzy Matching mit rapidfuzz einbauen"
- **Gemini 3 Pro:** "Entity Resolution - 'Dr. Müller' = 'Stefan M.' erkennen"

---

## Kontext und Problemstellung

Aktueller Zustand:
- `graph_builder.py` extrahiert Entities (Personen, Organisationen)
- Entities werden als separate Knoten gespeichert
- **Problem:** "Dr. Müller", "Stefan Müller", "S. Müller" sind 3 verschiedene Knoten

**Auswirkung:**
- Knowledge Graph fragmentiert
- "Related Documents" funktioniert nicht richtig
- Suche nach Person findet nicht alle Dokumente

**Kritikalität:** NEW FEATURE - Fundamental für Graph-Nutzbarkeit

---

## Entscheidungstreiber (Decision Drivers)

* **Genauigkeit:** Gleiche Person muss als gleiche Person erkannt werden
* **False Positives:** Verschiedene Personen dürfen nicht zusammengeführt werden
* **Performance:** Resolution muss bei jedem Ingest schnell sein

---

## Betrachtete Optionen

1. **Option A (Baseline):** Exact Match (aktuell)
2. **Option B (Kandidat):** Fuzzy Matching mit Schwellenwert
3. **Option C:** ML-basierte Entity Linking

---

## A/B-Test Spezifikation

### Test-ID: ABT-N01

```yaml
hypothese:
  these: "Fuzzy Resolution erhöht Entity-Verknüpfungen um 50% ohne signifikante False Positives"
  null_hypothese: "Exact Match ist ausreichend"

baseline:
  implementierung: "graph_builder.py mit exact match"
  metriken:
    - name: "unique_entities"
      beschreibung: "Anzahl einzigartiger Personen-Entities"
      aktueller_wert: "UNBEKANNT - zu messen"
    - name: "cross_doc_connections"
      beschreibung: "Dokument-Verbindungen über Entities"
      aktueller_wert: "UNBEKANNT"
    - name: "false_positive_rate"
      beschreibung: "Fälschlich zusammengeführte Entities"
      aktueller_wert: "0% (kein Merging)"

kandidat:
  implementierung: |
    from rapidfuzz import fuzz, process

    class EntityResolver:
        def __init__(self, threshold: float = 0.85):
            self.threshold = threshold
            self.entities = {}  # name -> canonical_id

        def resolve(self, name: str, context: dict = None) -> str:
            """
            Findet oder erstellt Entity für gegebenen Namen.

            Args:
                name: Extrahierter Name ("Dr. Müller")
                context: Zusätzliche Infos (Dokument, Datum, etc.)

            Returns:
                canonical_id: ID der Entity
            """
            # Normalisierung
            normalized = self._normalize(name)

            # Fuzzy Match gegen bekannte Entities
            matches = process.extract(
                normalized,
                self.entities.keys(),
                scorer=fuzz.token_sort_ratio,
                limit=3
            )

            for match_name, score, _ in matches:
                if score >= self.threshold * 100:
                    # Zusätzliche Validierung mit Kontext
                    if self._validate_merge(name, match_name, context):
                        return self.entities[match_name]

            # Neue Entity erstellen
            entity_id = self._create_entity(name)
            self.entities[normalized] = entity_id
            return entity_id

        def _normalize(self, name: str) -> str:
            """Normalisiert Namen für Vergleich."""
            import re
            # Titel entfernen
            name = re.sub(r'^(Dr\.|Prof\.|Herr|Frau)\s*', '', name)
            # Lowercase, Whitespace normalisieren
            return ' '.join(name.lower().split())

        def _validate_merge(self, name1: str, name2: str, context: dict) -> bool:
            """Zusätzliche Validierung vor Merge."""
            # Beispiel: Gleiches Dokument = wahrscheinlich gleiche Person
            # Verschiedene Firmen = wahrscheinlich verschiedene Personen
            return True  # Simplified
  erwartete_verbesserung:
    - "unique_entities: -30% (Duplikate zusammengeführt)"
    - "cross_doc_connections: +50%"
    - "false_positive_rate: < 5%"

testbedingungen:
  daten:
    - "100 Dokumente mit manuell annotierten Personen"
    - "Ground Truth: Welche Namen sind dieselbe Person?"
  metriken:
    - "Precision: Korrekte Merges / Alle Merges"
    - "Recall: Gefundene Merges / Alle korrekten Merges"

erfolgskriterien:
  primaer: "cross_doc_connections Kandidat > Baseline + 30%"
  sekundaer: "false_positive_rate < 10%"
  tertiaer: "Resolution-Zeit < 50ms pro Entity"

testscript: |
  # tests/ab_test_entity_resolution.py

  def evaluate_entity_resolution(
      resolver,
      test_names: list,
      ground_truth: dict  # name -> canonical_id
  ) -> dict:
      """Evaluiert Entity Resolution Qualität."""

      results = {
          "true_positives": 0,
          "false_positives": 0,
          "false_negatives": 0
      }

      resolved = {}
      for name in test_names:
          resolved_id = resolver.resolve(name)
          resolved[name] = resolved_id

      # Vergleich mit Ground Truth
      for name1 in test_names:
          for name2 in test_names:
              if name1 >= name2:
                  continue

              same_in_gt = ground_truth[name1] == ground_truth[name2]
              same_in_resolved = resolved[name1] == resolved[name2]

              if same_in_gt and same_in_resolved:
                  results["true_positives"] += 1
              elif not same_in_gt and same_in_resolved:
                  results["false_positives"] += 1
              elif same_in_gt and not same_in_resolved:
                  results["false_negatives"] += 1

      precision = results["true_positives"] / (results["true_positives"] + results["false_positives"])
      recall = results["true_positives"] / (results["true_positives"] + results["false_negatives"])

      return {
          "precision": precision,
          "recall": recall,
          "f1": 2 * precision * recall / (precision + recall)
      }
```

---

## Ground Truth Beispiele

```yaml
# Gleiche Person, verschiedene Schreibweisen
- names: ["Dr. Stefan Müller", "Stefan Müller", "S. Müller", "Herr Müller"]
  canonical_id: "person_001"
  validation: "Alle in Dokumenten der gleichen Firma"

# Verschiedene Personen, ähnliche Namen
- names: ["Peter Schmidt (Firma A)", "Peter Schmidt (Firma B)"]
  canonical_id: ["person_002", "person_003"]
  validation: "Verschiedene Firmen, verschiedene Personen"

# Organisationen
- names: ["Bauhaus GmbH", "Bauhaus", "Bauhaus Baumarkt"]
  canonical_id: "org_001"
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option B (Fuzzy Resolution)**

### Begründung (vorläufig)
- Gemini: "Entity Resolution ist das Herzstück für Geheimdienst-Architektur"
- Claude: "Macht den Knowledge Graph 10x wertvoller"
- Ohne Resolution: Graph ist fragmentiert und nutzlos

---

## Konsequenzen

### Wenn Option B gewinnt (Fuzzy Resolution)
**Positiv:**
- Mehr verknüpfte Dokumente
- "Related Documents" funktioniert besser
- Suche nach Person findet alles

**Negativ:**
- False Positives möglich
- Komplexerer Code
- Validierung erforderlich

### Wenn Option A bleibt (Exact Match)
**Positiv:**
- Keine False Positives
- Einfacher Code

**Negativ:**
- Graph bleibt fragmentiert
- "Related Documents" fast nutzlos

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - Intelligente Verknüpfung ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Resolution-Threshold dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Graph Builder: `scripts/graph_builder.py`
- Knowledge Graph Usage: [ADR-013-knowledge-graph-usage.md](./ADR-013-knowledge-graph-usage.md)
