# Architecture Evolution Plan
## Synthese aus Claude Opus 4.5 + Gemini 3 Pro Analyse

*Basierend auf Alex Fischer's Erfolgsalgorithmus: "Erfolg ist das Weglassen von Misserfolg"*

---

## RED Buttons (Systematisch eliminieren)

### RED-001: Shadow Ledger Event-Tracking
**Problem:** Jede Datei-Bewegung in SQLite tracken ist fragil.
**Gemini:** "Wartungs-Hölle - wenn du manuell verschiebst, ist die DB out of sync"
**Claude:** "Content-addressed storage statt Path-Tracking"
**Entscheidung:**
- [ ] Shadow Ledger auf periodischen Scan umstellen (nicht Event-basiert)
- [ ] SHA-256 als primärer Identifier, nicht Pfad

### RED-002: Ollama für Klassifikation
**Problem:** 2-5 Sekunden pro Datei = 50+ Stunden für 100k Dateien
**Claude:** "NER (GLiNER) + Regelwerk statt LLM"
**Gemini:** "Docling + GLiNER im neural-worker bereits vorhanden"
**Entscheidung:**
- [ ] LLM-Klassifikation nur für Quarantäne-Review
- [ ] GLiNER + Regex-Patterns für Mass-Ingest

### RED-003: Auto-Rename ohne Rollback
**Problem:** "2024-12-26_Finanzen_Bauhaus.pdf" - Original verloren
**Claude:** "Umbenennung ist destruktiv"
**Entscheidung:**
- [ ] Keine automatische Umbenennung
- [ ] Metadata-Layer für "virtuellen" Namen

### RED-004: Quality Gates mit 50% Quarantäne
**Problem:** Arbeit nur verschoben, nicht gelöst
**Gemini:** "Mutig sortieren mit Tag '_Autosorted'"
**Entscheidung:**
- [ ] Confidence < 0.5 → Quarantäne (nur ~10%)
- [ ] Confidence 0.5-0.7 → Sortieren + Tag `_review`
- [ ] Confidence > 0.7 → Sortieren ohne Tag

### RED-005: Knowledge Graph als Selbstzweck
**Problem:** "Durch 3D-Graphen fliegen ist oft unübersichtlich"
**Gemini:** "Eher Spielerei, außer für forensische Audits"
**Claude:** "Graph für Entity Resolution nutzen, nicht visualisieren"
**Entscheidung:**
- [ ] Graph-Visualisierung niedrige Priorität
- [ ] Graph für "Related Documents" Feature nutzen

### RED-006: 17 Docker Container für Homelab
**Problem:** Ressourcen-Overhead, Komplexität
**Claude:** "Nextcloud, Immich sind optional"
**Entscheidung:**
- [ ] Core Stack: 8 Container max
- [ ] Optional: Nextcloud, Immich als separate Compose

---

## BLUE Buttons (Verstärken und ausbauen)

### BLUE-001: Hybrid Search (Semantic + Keyword)
**Beide Analysen:** "Das Herzstück. Mach das so gut wie möglich."
**Status:** Funktioniert via Qdrant + Meilisearch
**Nächster Schritt:**
- [ ] Cross-encoder Reranking (zerank-1) hinzufügen
- [ ] Query Expansion mit Synonymen

### BLUE-002: Inbox-Automatisierung
**Gemini:** "Spart täglich 15 Min Arbeit"
**Status:** smart_ingest.py funktioniert
**Nächster Schritt:**
- [ ] Circuit Breaker für fehlerhafte Dateien
- [ ] Retry-Queue statt sofortiger Quarantäne

### BLUE-003: Privacy-First (Local LLM)
**Beide:** "Strategisch notwendig"
**Status:** Ollama läuft
**Nächster Schritt:**
- [ ] Qwen3:8b als Default (Geminis Empfehlung)
- [ ] A/B-Test Framework automatisieren

### BLUE-004: Docling für Deep Ingest
**Gemini:** "Perfekt für Tabellen, ersetzt Surya effektiv"
**Status:** Im neural-worker integriert
**Nächster Schritt:**
- [ ] Docling für alle PDFs aktivieren
- [ ] Markdown-Output in LanceDB speichern

### BLUE-005: LanceDB als "Neural Spine"
**Gemini:** "Qdrant bei >100k Docs zu viel RAM"
**Status:** Bereits konfiguriert
**Nächster Schritt:**
- [ ] Migration von Qdrant zu LanceDB für Archiv
- [ ] Qdrant nur für Hot-Data (letzte 30 Tage)

### BLUE-006: Circuit Breaker Pattern
**Gemini (Erfolgsalgorithmus):** "Fehler abfangen, nicht nur loggen"
**Status:** Teilweise in quality_gates.py
**Nächster Schritt:**
- [ ] Alle API-Calls mit Timeout + Retry
- [ ] Quarantäne-Ordner als "Error Sink"

---

## NEUE Features (Aus Synthese)

### NEW-001: Entity Resolution
**Quelle:** Gemini (Geheimdienst-Architektur)
**Konzept:** "Dr. Müller" = "Stefan M." erkennen
**Implementation:**
```python
# In graph_builder.py
def resolve_entity(name: str, existing_entities: List[Entity]) -> Entity:
    # Fuzzy matching mit rapidfuzz
    matches = process.extract(name, [e.name for e in existing_entities], limit=3)
    if matches[0][1] > 85:  # 85% Ähnlichkeit
        return merge_entities(name, matches[0][0])
    return create_new_entity(name)
```

### NEW-002: Data Narrator für Tabellen
**Quelle:** Gemini
**Konzept:** CSV/Excel → Zusammenfassung für KI
**Implementation:**
```python
def narrate_table(df: pd.DataFrame) -> str:
    return f"""
    Tabelle mit {len(df)} Zeilen.
    Spalten: {', '.join(df.columns)}
    Numerische Zusammenfassung:
    {df.describe().to_markdown()}
    Erste 10 Zeilen:
    {df.head(10).to_markdown()}
    """
```

### NEW-003: Evidence Board UI
**Quelle:** Gemini (Neural Deck)
**Konzept:** Split-Screen mit Quellen-Vorschau
- Links: Chat/Q&A Stream
- Rechts: PDF-Ausschnitte, Video-Timestamps, Bild-Crops

### NEW-004: Canary Tokens (Honeypots)
**Quelle:** Gemini (Geheimdienst)
**Konzept:** Fake-Dateien die Alarm auslösen
**Für später:** Security-Feature wenn System geteilt wird

---

## Die 4+1 Fragen (Risk Management)

Vor JEDER Architektur-Entscheidung durchgehen:

### 1. Gibt es Downsides?
- API öffnen → Read-Only Token für externe Tools
- Batch-Processing → Resource Limits in Docker

### 2. Wechselwirkungen?
- batch_processor + search_ui auf gleichem Host?
- → Docker CPU Limits setzen

### 3. Fehlende Daten?
- Wie viel RAM brauchen 500k Docs?
- → Pilot mit 5k Docs liefert Daten

### 4. Alle Blickwinkel?
- Adlersicht: Architektur-Diagramm
- Ameisensicht: Ein User sucht "Rechnung Dezember"

### 5. Test auf Schwachpunkt?
- Kritischster Pfad zuerst: Query → Embedding → Search → Rerank → Answer

---

## Erfolgskurve Prognose

```
Fortschritt
    │
    │                                    ╭──── Exponentielles Wachstum
    │                              ╭─────╯     (Meiste RED Buttons eliminiert)
    │                         ╭────╯
    │                    ╭────╯
    │               ╭────╯
    │          ╭────╯
    │     ╭────╯
    │ ────╯  ← Flache Phase (Viele RED Buttons finden)
    │
    └─────────────────────────────────────────── Zeit
         ^
         |
    Du bist hier (Pilot Phase)
```

---

## Nächste Schritte (Priorisiert)

1. **Heute:** RED-002 umsetzen (GLiNER statt Ollama für Klassifikation)
2. **Diese Woche:** BLUE-001 verbessern (Reranking hinzufügen)
3. **Nächste Woche:** NEW-001 (Entity Resolution in graph_builder.py)
4. **Phase 5:** NEW-003 (Evidence Board UI)

---

*Dokument generiert: 2025-12-28*
*Quellen: Claude Opus 4.5 Analyse + Gemini 3 Pro Analyse*
