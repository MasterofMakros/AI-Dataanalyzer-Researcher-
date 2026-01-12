# Implementierungs-Prompt für Gemini 3 Pro Coder
## Neural Vault / Conductor - A/B-Test Implementation

> **Zweck:** Dieser Prompt gibt Gemini alle Informationen, um die geplanten
> Architektur-Verbesserungen zu implementieren und zu testen.

---

## 🎯 HAUPT-PROMPT (Kopiere dies zu Gemini)

```
# Kontext

Du arbeitest am Projekt "Neural Vault" (auch "Conductor" genannt) - ein Privacy-First,
lokales AI-Dokumentenmanagement-System für 10TB+ persönliche Daten.

Das Projekt hat eine umfassende Analyse durchlaufen (Claude Opus 4.5 + Gemini 3 Pro),
und es wurden 15 A/B-Tests definiert, um die Architektur systematisch zu verbessern.

Deine Aufgabe ist es, diese Tests zu implementieren und durchzuführen.

# Pflichtlektüre (in dieser Reihenfolge)

Lies diese Dateien ZUERST, bevor du Code schreibst:

1. `F:/conductor/docs/AB_TEST_FRAMEWORK.md`
   → Überblick aller 15 Tests, Metriken, Entscheidungsregeln

2. `F:/conductor/docs/COMPONENT_STATUS.md`
   → Aktueller Status aller Komponenten (was ist ALT vs NEU)

3. `F:/conductor/docs/FEATURE_LIFECYCLE.md`
   → Wie Features von EXPERIMENTAL → ACTIVE migrieren

4. `F:/conductor/docs/ARCHITECTURE_EVOLUTION.md`
   → RED/BLUE/NEW Button Klassifikation

# Aufgabe

Implementiere und teste die A/B-Tests in dieser Prioritätsreihenfolge:

## Phase 1: RED Buttons (Probleme eliminieren)

### ABT-R02: Klassifikation (Höchste Priorität)
- Lies: `F:/conductor/docs/ADR/ADR-010-classification-method.md`
- Aktueller Code: `F:/conductor/scripts/smart_ingest.py`
- Neuer Code: `F:/conductor/docker/neural-worker/`
- Aufgabe:
  1. Implementiere Feature Flag `USE_GLINER_CLASSIFICATION`
  2. Erstelle Router der zwischen Ollama und GLiNER wählt
  3. Schreibe Benchmark-Script: `tests/ab_test_classification.py`
  4. Erstelle Ground Truth Datenset (100 manuell kategorisierte Dateien)
  5. Führe Test durch, dokumentiere Ergebnisse

### ABT-R01: Shadow Ledger
- Lies: `F:/conductor/docs/ADR/ADR-009-shadow-ledger-tracking.md`
- Aktueller Code: `F:/conductor/scripts/shadow_ledger.py` (falls vorhanden)
- Aufgabe:
  1. Implementiere periodischen Filesystem-Scan als Alternative
  2. Vergleiche sync_accuracy zwischen Event-basiert und Scan
  3. Dokumentiere Ergebnisse

## Phase 2: BLUE Buttons (Stärken ausbauen)

### ABT-B01: Search Reranking
- Lies: `F:/conductor/docs/ADR/ADR-015-search-reranking.md`
- Aktueller Code: `F:/conductor/scripts/search_ui.py`, `vector_service.py`
- Aufgabe:
  1. Integriere Cross-Encoder (jina-reranker-v2-base-multilingual)
  2. Implementiere Two-Stage Search (Retrieve → Rerank)
  3. Benchmark Precision@10 mit/ohne Reranking

### ABT-B04: PDF Parsing
- Lies: `F:/conductor/docs/ADR/ADR-018-pdf-parsing.md`
- Aufgabe:
  1. Vergleiche Tika vs Docling Tabellenextraktion
  2. Erstelle Ground Truth mit 50 Rechnungs-PDFs

## Phase 3: NEW Features (Evaluieren)

### ABT-N01: Entity Resolution
- Lies: `F:/conductor/docs/ADR/ADR-020-entity-resolution.md`
- Aufgabe:
  1. Implementiere Fuzzy Matching mit rapidfuzz
  2. Integriere in `graph_builder.py`

### ABT-N02: Data Narrator
- Lies: `F:/conductor/docs/ADR/ADR-021-data-narrator.md`
- Aufgabe:
  1. Implementiere Tabellen-Zusammenfassung für CSV/Excel
  2. Integriere in Ingest-Pipeline

# Code-Konventionen

1. Neue Features in `scripts/experimental/` erstellen
2. Feature Flags in `config/feature_flags.py` definieren
3. Jede Funktion mit Status-Docstring versehen:
   ```python
   """
   Feature: Entity Resolution
   Status: EXPERIMENTAL
   ADR: ADR-020
   A/B-Test: ABT-N01
   """
   ```

4. Ergebnisse taggen:
   ```python
   result["_processed_by"] = "gliner_v2"
   result["_feature_flags"] = get_active_flags()
   ```

# Erfolgskriterien

Für jeden Test:
1. Baseline-Metriken dokumentieren (IST-Zustand)
2. Kandidat-Metriken dokumentieren (SOLL-Zustand)
3. Entscheidung treffen: BLUE (Kandidat gewinnt) oder RED (Kandidat verworfen)
4. ADR-Status aktualisieren
5. COMPONENT_STATUS.md aktualisieren

# Output-Format

Nach jedem Test, erstelle einen Report:

```markdown
## A/B-Test Report: ABT-XXX

### Baseline (A)
- Metrik 1: X
- Metrik 2: Y

### Kandidat (B)
- Metrik 1: X'
- Metrik 2: Y'

### Entscheidung
**[BLUE/RED]**: Begründung...

### Nächste Schritte
- [ ] Feature Flag aktivieren
- [ ] Alten Code nach deprecated/ verschieben
- [ ] ADR-Status auf "Accepted" setzen
```

# Fragen?

Falls dir Informationen fehlen:
1. Lies die verknüpften ADRs
2. Prüfe den aktuellen Code in den genannten Pfaden
3. Frage den User nach Ground Truth Daten falls nicht vorhanden
```

---

## 📁 Dokumente die Gemini braucht

### Pflichtlektüre (vor Implementierung)

| Priorität | Datei | Inhalt |
|-----------|-------|--------|
| 1 | `docs/AB_TEST_FRAMEWORK.md` | Alle 15 Tests, Metriken, Regeln |
| 2 | `docs/COMPONENT_STATUS.md` | Was ist ALT vs NEU |
| 3 | `docs/FEATURE_LIFECYCLE.md` | Wie Features migrieren |
| 4 | `docs/ARCHITECTURE_EVOLUTION.md` | RED/BLUE/NEW Klassifikation |

### Pro Test (spezifisch)

| Test | ADR | Aktueller Code | Neuer Code |
|------|-----|----------------|------------|
| ABT-R02 | `ADR-010-classification-method.md` | `scripts/smart_ingest.py` | `docker/neural-worker/` |
| ABT-R01 | `ADR-009-shadow-ledger-tracking.md` | `data/shadow_ledger.db` | Neu zu erstellen |
| ABT-B01 | `ADR-015-search-reranking.md` | `scripts/search_ui.py` | Neu zu erstellen |
| ABT-B04 | `ADR-018-pdf-parsing.md` | Tika Container | Docling im neural-worker |
| ABT-N01 | `ADR-020-entity-resolution.md` | `scripts/graph_builder.py` | Zu erweitern |
| ABT-N02 | `ADR-021-data-narrator.md` | Nicht vorhanden | Neu zu erstellen |

### Zusätzliche Referenzen

| Datei | Wann benötigt |
|-------|---------------|
| `docker-compose.yml` | Bei Docker-Änderungen |
| `scripts/quality_gates.py` | Bei ABT-R04 (Quarantäne) |
| `VISION.md` | Für Kontext und Non-Goals |

---

## 🚀 Empfohlener Workflow für Gemini

### Schritt 1: Kontext aufbauen

```
Lies zuerst diese Dateien und fasse zusammen, was du verstanden hast:
- F:/conductor/docs/AB_TEST_FRAMEWORK.md
- F:/conductor/docs/COMPONENT_STATUS.md

Bestätige, dass du die 15 A/B-Tests und ihre Prioritäten verstanden hast.
```

### Schritt 2: Ersten Test starten

```
Beginne mit ABT-R02 (Klassifikation - Ollama vs GLiNER).

1. Lies F:/conductor/docs/ADR/ADR-010-classification-method.md
2. Lies den aktuellen Code: F:/conductor/scripts/smart_ingest.py
3. Erkläre deinen Implementierungsplan bevor du Code schreibst
```

### Schritt 3: Implementierung

```
Implementiere jetzt:
1. Feature Flag USE_GLINER_CLASSIFICATION in config/feature_flags.py
2. ClassificationRouter in services/classifier.py
3. Benchmark-Script in tests/ab_test_classification.py

Zeige mir den Code und erkläre jeden Teil.
```

### Schritt 4: Test durchführen

```
Führe den A/B-Test durch:
1. Baseline messen (Ollama)
2. Kandidat messen (GLiNER)
3. Erstelle den Test-Report im definierten Format
```

### Schritt 5: Dokumentation aktualisieren

```
Aktualisiere basierend auf den Ergebnissen:
1. ADR-010 Status (BLUE oder RED)
2. COMPONENT_STATUS.md
3. AB_TEST_FRAMEWORK.md (Status-Spalte)
```

---

## ⚠️ Wichtige Hinweise für Gemini

### DO:
- ✅ Immer zuerst die ADR lesen bevor du implementierst
- ✅ Feature Flags für alle neuen Features nutzen
- ✅ Ergebnisse mit Version-Tag versehen
- ✅ Tests in `experimental/` Ordner erstellen
- ✅ Metriken vor UND nach der Änderung messen

### DON'T:
- ❌ Alten Code direkt überschreiben (erst DEPRECATED markieren)
- ❌ Features ohne A/B-Test aktivieren
- ❌ Zwei ACTIVE Implementierungen für dieselbe Funktion
- ❌ ADR-Status ändern ohne Test-Ergebnisse

---

## 📊 Erwartete Outputs

Nach Abschluss sollte Gemini folgendes geliefert haben:

### Code-Artefakte
```
scripts/
├── experimental/
│   ├── gliner_classifier.py      # ABT-R02
│   ├── filesystem_scanner.py     # ABT-R01
│   ├── search_reranker.py        # ABT-B01
│   ├── entity_resolver.py        # ABT-N01
│   └── data_narrator.py          # ABT-N02
│
├── config/
│   └── feature_flags.py          # Alle Feature Flags
│
└── services/
    └── classifier.py             # Router für Klassifikation

tests/
├── ab_test_classification.py
├── ab_test_shadow_ledger.py
├── ab_test_reranking.py
└── ground_truth/
    └── classification_gt.json    # Manuell annotierte Testdaten
```

### Dokumentations-Updates
```
docs/
├── ADR/
│   └── (Status-Updates in allen getesteten ADRs)
├── COMPONENT_STATUS.md (aktualisiert)
├── AB_TEST_FRAMEWORK.md (Status-Spalten aktualisiert)
└── test_reports/
    ├── ABT-R02-report.md
    ├── ABT-R01-report.md
    └── ...
```

---

*Erstellt: 2025-12-28*
*Für: Google Gemini 3 Pro Coder*
