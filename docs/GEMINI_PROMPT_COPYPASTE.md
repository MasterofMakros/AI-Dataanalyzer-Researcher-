# COPY-PASTE PROMPT FÜR GOOGLE GEMINI 3 PRO CODER

---

## PROMPT 1: Kontext & Verständnis (ZUERST SENDEN)

```
# Projekt: Neural Vault (Conductor)

Du arbeitest am Projekt "Neural Vault" - ein Privacy-First, lokales AI-Dokumentenmanagement-System für 10TB+ persönliche Daten. Das Projekt befindet sich in F:/conductor.

Das Projekt hat eine umfassende Architektur-Analyse durchlaufen. Es wurden 15 A/B-Tests definiert, basierend auf Alex Fischers "Erfolgsalgorithmus":
- 6 RED Buttons (Probleme eliminieren)
- 6 BLUE Buttons (Stärken ausbauen)
- 4 NEW Features (Evaluieren)

## Deine erste Aufgabe

Lies diese Dateien und bestätige dein Verständnis:

1. F:/conductor/docs/AB_TEST_FRAMEWORK.md
2. F:/conductor/docs/COMPONENT_STATUS.md
3. F:/conductor/docs/FEATURE_LIFECYCLE.md

Beantworte dann:
1. Wie viele A/B-Tests gibt es in jeder Kategorie (RED/BLUE/NEW)?
2. Was bedeuten die Status ACTIVE, EXPERIMENTAL, DEPRECATED?
3. Welcher Test hat die höchste Priorität und warum?
4. Was ist das Grundprinzip des Erfolgsalgorithmus?

Warte auf meine Bestätigung bevor du mit der Implementierung beginnst.
```

---

## PROMPT 2: Implementierung (NACH BESTÄTIGUNG SENDEN)

```
# Implementierungs-Auftrag: A/B-Tests für Neural Vault

## Projektstruktur

Das Projekt ist in F:/conductor mit folgender Struktur:

```
F:/conductor/
├── docs/
│   ├── ADR/                      # Architecture Decision Records
│   │   ├── ADR-009 bis ADR-023   # Die 15 A/B-Test ADRs
│   ├── AB_TEST_FRAMEWORK.md      # Übersicht aller Tests
│   ├── COMPONENT_STATUS.md       # Status aller Komponenten
│   ├── FEATURE_LIFECYCLE.md      # Wie Features migrieren
│   └── ARCHITECTURE_EVOLUTION.md # RED/BLUE/NEW Klassifikation
├── scripts/
│   ├── smart_ingest.py           # Aktuelle Klassifikation (Ollama)
│   ├── quality_gates.py          # Quarantäne-Logik
│   ├── graph_builder.py          # Knowledge Graph
│   ├── search_ui.py              # Gradio Search UI
│   └── vector_service.py         # Embedding Service
├── docker/
│   └── neural-worker/            # Neuer Worker mit GLiNER + Docling
├── docker-compose.yml            # Docker Stack Definition
└── tests/                        # Test-Verzeichnis
```

## Implementierungs-Reihenfolge (Priorität)

### Phase 1: ABT-R02 - Klassifikation (HÖCHSTE PRIORITÄT)

**Problem:** Ollama LLM braucht 2-5 Sekunden pro Datei = zu langsam
**Lösung:** GLiNER NER ist 20x schneller

**Lies zuerst:**
- F:/conductor/docs/ADR/ADR-010-classification-method.md
- F:/conductor/scripts/smart_ingest.py

**Implementiere:**

1. Feature Flag System:
```python
# Erstelle: F:/conductor/config/feature_flags.py

FEATURE_FLAGS = {
    "USE_GLINER_CLASSIFICATION": (False, "EXPERIMENTAL"),
    "USE_OLLAMA_CLASSIFICATION": (True, "DEPRECATED"),
}

def is_enabled(feature: str) -> bool:
    return FEATURE_FLAGS.get(feature, (False,))[0]
```

2. Classification Router:
```python
# Erstelle: F:/conductor/services/classifier.py

from config.feature_flags import is_enabled

class ClassificationRouter:
    def __init__(self):
        if is_enabled("USE_GLINER_CLASSIFICATION"):
            # Neuer Weg: GLiNER via neural-worker
            self._impl = GLiNERClassifier()
            self._version = "v2-gliner"
        else:
            # Alter Weg: Ollama
            self._impl = OllamaClassifier()
            self._version = "v1-ollama-deprecated"

    def classify(self, text: str) -> dict:
        result = self._impl.classify(text)
        result["_classifier_version"] = self._version
        return result
```

3. Benchmark Script:
```python
# Erstelle: F:/conductor/tests/ab_test_classification.py

# Teste beide Implementierungen mit 100 Dateien
# Miss: latency_per_file, accuracy, gpu_memory
# Vergleiche gegen Ground Truth
```

**Erfolgskriterien:**
- latency_per_file < 200ms (aktuell: 2000-5000ms)
- accuracy >= 75% (aktuell: ~85%)
- gpu_memory < 4GB (aktuell: 6GB)

### Phase 2: ABT-B01 - Search Reranking

**Lies:** F:/conductor/docs/ADR/ADR-015-search-reranking.md

**Implementiere:**
- Cross-Encoder Integration (jina-reranker-v2-base-multilingual)
- Two-Stage Search: Retrieve Top-50 → Rerank → Return Top-10

### Phase 3: ABT-N01 - Entity Resolution

**Lies:** F:/conductor/docs/ADR/ADR-020-entity-resolution.md

**Implementiere:**
- Fuzzy Matching mit rapidfuzz (threshold 0.85)
- Integration in graph_builder.py
- "Dr. Müller" = "Stefan Müller" = "S. Müller" erkennen

### Phase 4: ABT-N02 - Data Narrator

**Lies:** F:/conductor/docs/ADR/ADR-021-data-narrator.md

**Implementiere:**
- CSV/Excel → Markdown Zusammenfassung
- Statistiken, Top-Werte, Preview der ersten Zeilen

## Code-Konventionen (WICHTIG!)

1. **Neue Features** → `scripts/experimental/` Ordner
2. **Alte Features** → `scripts/deprecated/` verschieben (nicht löschen!)
3. **Feature Flags** → Für JEDES neue Feature
4. **Status-Docstring** in jeder Datei:
```python
"""
Feature: [Name]
Status: EXPERIMENTAL | ACTIVE | DEPRECATED
ADR: ADR-XXX
A/B-Test: ABT-XXX
"""
```

5. **Ergebnis-Tagging:**
```python
result = {
    "category": "Finanzen",
    "_processed_by": "gliner_v2",
    "_timestamp": "2025-12-28T14:30:00Z"
}
```

## Output nach jedem Test

Erstelle einen Report in diesem Format:

```markdown
## A/B-Test Report: ABT-XXX

### Test-Setup
- Daten: X Dateien aus F:/
- Hardware: [deine Hardware]
- Datum: YYYY-MM-DD

### Baseline (A) - [Name]
| Metrik | Wert |
|--------|------|
| latency_per_file | X ms |
| accuracy | X % |
| memory | X GB |

### Kandidat (B) - [Name]
| Metrik | Wert |
|--------|------|
| latency_per_file | X ms |
| accuracy | X % |
| memory | X GB |

### Entscheidung
**[BLUE/RED/INCONCLUSIVE]**

Begründung: ...

### Nächste Schritte
- [ ] Feature Flag aktivieren/deaktivieren
- [ ] Code verschieben (experimental → active ODER → deprecated)
- [ ] ADR-Status aktualisieren
- [ ] COMPONENT_STATUS.md aktualisieren
```

## Fragen vor dem Start

Bevor du beginnst:
1. Hast du Zugriff auf alle genannten Dateien?
2. Läuft der Docker Stack (docker-compose.yml)?
3. Gibt es bereits Test-Daten in F:/_Inbox oder F:/_TestPool?
4. Welche GPU/Hardware steht zur Verfügung?

Starte mit Phase 1 (ABT-R02) und zeige mir deinen Implementierungsplan BEVOR du Code schreibst.
```

---

## OPTIONAL: PROMPT 3 - Ground Truth erstellen

```
# Ground Truth Datenset für A/B-Tests

Ich brauche ein Ground Truth Datenset für die Klassifikations-Tests.

## Aufgabe

Erstelle ein Script das:
1. 100 Dateien aus F:/ auswählt (verschiedene Typen: PDF, DOCX, JPG, etc.)
2. Eine JSON-Datei erstellt wo ich manuell die korrekte Kategorie eintragen kann

## Kategorien (aus VALID_CATEGORIES in quality_gates.py)
- Finanzen
- Arbeit
- Privat
- Medien
- Dokumente
- Technologie
- Gesundheit
- Reisen
- Sonstiges

## Output Format

```json
{
  "ground_truth": [
    {
      "file_path": "F:/_Archiv/Finanzen/Rechnung.pdf",
      "expected_category": "Finanzen",
      "expected_entities": ["Bauhaus", "127.50 EUR"],
      "labeled_by": "human",
      "date": "2025-12-28"
    }
  ],
  "metadata": {
    "total_files": 100,
    "categories_distribution": {...}
  }
}
```

Erstelle: F:/conductor/tests/ground_truth/classification_gt.json
```

---

*Ende des Copy-Paste Prompts*
