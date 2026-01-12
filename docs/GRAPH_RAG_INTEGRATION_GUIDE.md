# GraphRAG Integration Guide (Perplexica UI)

## Ziel
Diese Richtlinie stellt sicher, dass Graph-Funktionen konsistent, fehlerarm und **nahtlos** in die Perplexica-UI integriert werden. Der Fokus liegt auf **automatischer Entscheidungslogik** (LLM-gesteuert) für:
- **Graph-UI** (explizite Visualisierung)
- **Related Documents** (stille, kontextuelle Verknüpfung)

## Leitplanken (Fehlervermeidung)
1. **Keine UI ohne Nutzen**: Graph-UI nur, wenn ein klarer Informationsgewinn vorliegt (z. B. Netzwerkanalyse, Entitätenbeziehungen).  
2. **Default = Related Documents**: Standardmäßig verwandte Dokumente bereitstellen, ohne visuelle Overhead-Ansicht.  
3. **LLM entscheidet, nicht UI**: Die UI zeigt nur, was der Antwort-Controller explizit anfordert.  
4. **Fail-Safe**: Wenn Graph-Daten unvollständig oder unsicher sind → Related Docs (oder nichts) statt Graph-UI.  
5. **Single Source of Truth**: Alle Entscheidungen laufen über eine zentrale „Answer Orchestrator“ Logik (keine UI-Side-Logik).

---

## Entscheidungs-Matrix (Wann Graph-UI vs. Related Documents)

| Anfrage-Typ | Signal | Empfehlung | Begründung |
| --- | --- | --- | --- |
| **Entitäten-Netzwerk** | „Wer hängt mit wem zusammen?“, „Verbindungen zwischen…“ | **Graph-UI** | Visualisierung erklärt Beziehungen besser |
| **Dokument-Nachbarschaft** | „Ähnliche Dokumente“, „hängende Belege“ | **Related Documents** | Schnell, direkt, wenig UI-Overhead |
| **Entity Resolution** | Namensvarianten, Aliasfragen | **Related Documents** + Entitätenliste | Graph-Daten nützlich, UI oft unnötig |
| **Explorative Recherche** | „Zeig mir Cluster“, „Themen-Netzwerk“ | **Graph-UI** (optional) | Entdeckungsmodus sinnvoll |
| **Standard QA** | Fakten, Zusammenfassungen | **Kein Graph** | Graph bringt keinen Mehrwert |

**Default-Policy:** Wenn kein starkes Signal → **Related Documents** (falls verfügbar), sonst nichts.

---

## LLM-Entscheidungslogik (Routing)

### Entscheidungs-Ausgabeformat (Beispiel)
```json
{
  "include_graph_ui": false,
  "include_related_docs": true,
  "related_docs_reason": "User asked for similar invoices",
  "graph_ui_reason": null
}
```

### Regeln für das LLM
1. **Graph-UI nur mit Begründung** (textlich im JSON), sonst `false`.
2. **Related Docs mit niedriger Schwelle** aktivieren, wenn: 
   - Anfrage nach „ähnlich“, „verwandt“, „zugehörig“ oder
   - Entitäten/Organisationen mehrfach vorkommen.
3. **Konfidenzbedingung**: Wenn Graph-Datenqualität < Schwelle → Graph-UI deaktivieren.
4. **User Override**: Wenn der User explizit „Graph anzeigen“ sagt → Graph-UI aktivieren (falls Daten vorhanden).

---

## Perplexica UI Integration (einheitlich & fließend)

### UI-Komponenten
- **Answer Panel** (Primary): Antwort + Quellen (standardmäßig)
- **Related Documents Panel** (Secondary): nur wenn `include_related_docs=true`
- **Graph Panel** (Secondary/Tertiary): nur wenn `include_graph_ui=true`

### UI-Regeln
- **Keine konkurrierenden Panels**: Graph-UI soll nicht gleichzeitig mit zu vielen anderen Sektionen laden.
- **Staging**: Related Docs zuerst laden, Graph-UI nur nachgelagert (falls aktiv), um UI-Blockaden zu vermeiden.
- **Visuelle Konsistenz**: Graph-Panel dieselben Card-/Panel-Styles wie Related Docs.

---

## Datenquellen & Fallbacks

1. **Graph-Daten vorhanden** → optional Graph-UI oder Related Docs.
2. **Graph-Daten teilweise** → Related Docs, keine Graph-UI.
3. **Keine Graph-Daten** → Standardantwort ohne Graph.

**Fehlerfälle:**
- Graph Query Error → UI zeigt keinen Fehler, sondern **stille Degradierung** (kein Graph-Panel).

---

## Vorschlag für Evaluation (Bug-Reduktion)

- A/B-Test gemäß ADR-013: Graph-UI vs. Related Docs Usage.
- Metriken: `graph_usage_rate`, `related_docs_click_rate`, `task_completion_time`.
- Ziel: **Graph-UI nur beibehalten, wenn klare Nutzungssteigerung**.

---

## Abgleich mit externer Referenz (z. B. Cole Medin)

Diese Richtlinie setzt **keine** externen Tutorials voraus. Wenn eine externe Referenz (z. B. ein Video) als Maßstab dienen soll, nutze folgende **Abgleich-Checkliste**, damit die Umsetzung konsistent bleibt und keine UI-Inkonsistenzen entstehen:

1. **Routing-Quelle:** Externe Anleitung verwendet eine zentrale Orchestrierung? → Muss hier dem Abschnitt „LLM-Entscheidungslogik“ entsprechen.
2. **UI-Defaults:** Externe Anleitung nutzt Graph-UI als Default? → **Hier nicht erlaubt**, Default bleibt „Related Documents“.
3. **Fallbacks:** Externe Anleitung zeigt Graph trotz Datenlücken? → **Hier nicht erlaubt**, es gilt stille Degradierung.
4. **Entity-Fokus:** Externe Anleitung priorisiert Entity Resolution? → **Konform** mit dieser Richtlinie.

Wenn eine externe Quelle eine abweichende Priorisierung verlangt, dokumentiere die Abweichung ausdrücklich in der Projekt-Dokumentation und verweise auf ADR-013/ADR-020.

---

## Kurzfazit
- **Graph-UI ist ein Spezialwerkzeug**, nicht Standard.
- **Related Documents ist der Default**, weil es ruhig und nutzerzentriert ist.
- **LLM entscheidet** anhand klarer Regeln + Datenqualität.
