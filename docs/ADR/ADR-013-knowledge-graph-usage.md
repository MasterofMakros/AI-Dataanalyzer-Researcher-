# ADR-013: Knowledge Graph - Visualisierung vs. Related Documents

## Status
**Proposed** - A/B-Test erforderlich (ABT-R05)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Graph für Entity Resolution nutzen, nicht visualisieren"
- **Gemini 3 Pro:** "Durch 3D-Graphen fliegen ist oft unübersichtlich - eher Spielerei"

---

## Kontext und Problemstellung

Aktuelle Implementierung:
- `scripts/graph_builder.py` erstellt Knowledge Graph mit rustworkx
- `scripts/search_ui.py` (Gradio) zeigt Graph-Visualisierung

**Problem:**
- Graph-Visualisierung sieht in Demos gut aus
- Im Alltag: "Wann nutzt man das wirklich?"
- CPU/RAM-Overhead für Rendering

**Kritikalität:** RED BUTTON - Feature ohne klaren Nutzen

---

## Entscheidungstreiber (Decision Drivers)

* **Nutzwert:** Feature muss im Alltag helfen
* **Performance:** Kein Overhead für ungenutztes Feature
* **Fokus:** Entwicklungszeit für wertvolle Features nutzen

---

## Betrachtete Optionen

1. **Option A (Baseline):** Graph-Visualisierung als UI-Feature
2. **Option B (Kandidat):** Graph nur für "Related Documents"
3. **Option C:** Graph entfernen, nur Entity-Datenbank

---

## A/B-Test Spezifikation

### Test-ID: ABT-R05

```yaml
hypothese:
  these: "'Related Documents' Feature hat höheren Nutzwert als Graph-Visualisierung"
  null_hypothese: "Graph-Visualisierung wird aktiv genutzt"

baseline:
  implementierung: "search_ui.py mit Graph-Visualisierung"
  metriken:
    - name: "graph_usage_rate"
      beschreibung: "Wie oft wird Graph-Tab geöffnet?"
      messmethode: "UI Event Tracking"
      aktueller_wert: "UNBEKANNT"
    - name: "graph_interaction_time"
      beschreibung: "Zeit in Graph-Ansicht"
      aktueller_wert: "UNBEKANNT"
    - name: "task_completion_with_graph"
      beschreibung: "Wurde Dokument über Graph gefunden?"
      aktueller_wert: "UNBEKANNT"

kandidat:
  implementierung: |
    # Statt Graph-Visualisierung:
    # "Related Documents" Panel bei jedem Dokument

    def get_related_documents(doc_id: str, top_k: int = 5) -> list:
        """Findet verwandte Dokumente über Graph-Verbindungen."""
        neighbors = graph.neighbors(doc_id)
        # Sortiert nach Verbindungsstärke
        return sorted(neighbors, key=lambda x: x.weight, reverse=True)[:top_k]
  erwartete_verbesserung:
    - "Höhere Feature-Nutzung (automatisch sichtbar)"
    - "Schnellere Dokumenten-Entdeckung"
    - "Weniger UI-Komplexität"

testbedingungen:
  methodik: "User Study mit 5 Testpersonen"
  aufgaben:
    - "Finde alle Dokumente die mit 'Bauhaus' zusammenhängen"
    - "Finde den Vertrag zu dieser Rechnung"
    - "Welche Personen tauchen in meinen Finanzdokumenten auf?"
  messung:
    - "Zeit bis Aufgabe gelöst"
    - "Anzahl Klicks"
    - "Subjektive Zufriedenheit (1-5)"

erfolgskriterien:
  primaer: "task_completion_time Kandidat < Baseline"
  sekundaer: "Subjektive Zufriedenheit >= 4/5"
  tertiaer: "graph_usage_rate > 20% (wenn beibehalten)"

testscript: |
  # tests/ab_test_graph_usage.py

  # Dieser Test erfordert echte Benutzer-Interaktion
  # Vorschlag: Gradio mit Event-Logging

  import gradio as gr
  from datetime import datetime

  usage_log = []

  def log_event(event_type: str, details: dict):
      usage_log.append({
          "timestamp": datetime.now().isoformat(),
          "event": event_type,
          **details
      })

  # In UI einbauen:
  # log_event("graph_opened", {"user": "test1"})
  # log_event("related_docs_clicked", {"doc_id": "abc123"})
```

---

## Alternative: Entity Resolution statt Visualisierung

Beide KI-Analysen schlagen vor, den Graph für **Entity Resolution** zu nutzen:

```python
# Statt: Schöne Visualisierung
# Besser: Intelligente Verknüpfung

def resolve_entity(name: str) -> Entity:
    """
    Findet ob 'Dr. Müller' und 'Stefan M.' dieselbe Person sind.
    Nutzt Graph-Struktur für Kontext.
    """
    # Fuzzy Match auf bestehende Entities
    candidates = find_similar_names(name, threshold=0.85)

    if not candidates:
        return create_new_entity(name)

    # Graph-Kontext nutzen
    for candidate in candidates:
        shared_docs = get_shared_documents(name, candidate)
        if len(shared_docs) > 2:  # Tauchen gemeinsam auf
            return merge_entities(name, candidate)

    return create_new_entity(name)
```

---

## Entscheidung

**PENDING** - User Study erforderlich

### Vorläufige Empfehlung
Basierend auf beiden KI-Analysen: **Option B (Related Documents)**

### Begründung (vorläufig)
- Gemini: "Spielerei, außer für forensische Audits"
- Claude: "Entity Resolution ist der wahre Wert"
- "Related Documents" bietet Nutzen ohne Komplexität

---

## Konsequenzen

### Wenn Option B gewinnt (Related Documents)
**Positiv:**
- Einfachere UI
- Automatische Dokumenten-Entdeckung
- Graph-Logik bleibt, nur Präsentation ändert sich

**Negativ:**
- "Cool Factor" der Visualisierung entfällt
- Weniger Differenzierung zu anderen Tools

### Wenn Option A bleibt (Visualisierung)
**Positiv:**
- Beeindruckend für Demos
- Manche Nutzer mögen es

**Negativ:**
- Entwicklungsaufwand für wenig genutztes Feature
- Performance-Overhead

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - Fokus auf Kernnutzen |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [ ] Nein |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Graph Builder: `scripts/graph_builder.py`
- Search UI: `scripts/search_ui.py`
