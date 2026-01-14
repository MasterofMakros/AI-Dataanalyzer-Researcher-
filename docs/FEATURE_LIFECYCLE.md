# Feature Lifecycle Management
## Differenzierung zwischen alten und neuen Implementierungen

> **Kernproblem:** Ohne klare Lifecycle-Regeln entstehen Konflikte zwischen
> alter und neuer Implementierung. Beide laufen parallel, liefern unterschiedliche
> Ergebnisse, und niemand weiß welche "richtig" ist.

---

## Feature-Status-Modell

Jede Funktion/Komponente hat einen von 5 Status:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │PROPOSED  │───▶│EXPERIMENT│───▶│ ACTIVE   │───▶│DEPRECATED│      │
│  │          │    │   AL     │    │          │    │          │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│       │               │               │               │             │
│       │               │               │               ▼             │
│       │               │               │         ┌──────────┐        │
│       │               ▼               │         │ REMOVED  │        │
│       │         ┌──────────┐          │         └──────────┘        │
│       └────────▶│ REJECTED │◀─────────┘                             │
│                 └──────────┘                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Status-Definitionen

| Status | Beschreibung | Code-Konvention | Nutzung erlaubt |
|--------|--------------|-----------------|-----------------|
| **PROPOSED** | Idee dokumentiert, nicht implementiert | Kein Code | Nein |
| **EXPERIMENTAL** | Implementiert, in A/B-Test | `_experimental/` Ordner | Nur in Tests |
| **ACTIVE** | Produktiv, empfohlen | Hauptordner | Ja |
| **DEPRECATED** | Wird abgeschaltet, Alternative existiert | `@deprecated` Decorator | Mit Warnung |
| **REMOVED** | Code gelöscht | - | Nein |
| **REJECTED** | Getestet, als "Roter Knopf" markiert | Kein Code, nur ADR | Nein |

---

## Code-Konventionen für Differenzierung

### 1. Ordnerstruktur

```
scripts/
├── active/                    # Produktiver Code
│   ├── smart_ingest.py       # ACTIVE
│   └── quality_gates.py      # ACTIVE
│
├── experimental/              # In A/B-Test
│   ├── smart_ingest_v2.py    # EXPERIMENTAL (mit GLiNER)
│   └── entity_resolver.py    # EXPERIMENTAL
│
├── deprecated/                # Wird abgeschaltet
│   ├── old_classifier.py     # DEPRECATED
│   └── README.md             # Migrationsanleitung
│
└── legacy/                    # Nur für Kompatibilität
    └── batch_processor_v1.py # Für alte Workflows
```

### 2. Code-Markierungen

```python
# In jeder Datei: Status-Header
"""
Feature: Smart Ingest Pipeline
Status: EXPERIMENTAL
Version: 2.0.0
Supersedes: smart_ingest.py (v1.x)
ADR: ADR-010-classification-method.md
A/B-Test: ABT-R02
"""

import warnings
from functools import wraps

# Decorator für deprecated Funktionen
def deprecated(reason: str, alternative: str, removal_version: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is DEPRECATED: {reason}. "
                f"Use {alternative} instead. "
                f"Will be removed in v{removal_version}.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Verwendung
@deprecated(
    reason="LLM-Klassifikation zu langsam",
    alternative="neural_worker.classify()",
    removal_version="3.0.0"
)
def classify_with_ollama(text: str) -> str:
    """ALT: Klassifikation via Ollama."""
    pass
```

### 3. Feature Flags

```python
# config/feature_flags.py

FEATURE_FLAGS = {
    # Format: "feature_name": (enabled, status, description)

    # Klassifikation
    "USE_GLINER_CLASSIFICATION": (False, "EXPERIMENTAL", "GLiNER statt Ollama"),
    "USE_OLLAMA_CLASSIFICATION": (True, "DEPRECATED", "Wird in v3.0 entfernt"),

    # Suche
    "ENABLE_RERANKING": (False, "EXPERIMENTAL", "Cross-Encoder Reranking"),
    "USE_HYBRID_SEARCH": (True, "ACTIVE", "BM25 + Vektor"),

    # Vector DB
    "USE_LANCEDB_ARCHIVE": (False, "EXPERIMENTAL", "LanceDB für Archiv"),
    "USE_QDRANT_ONLY": (True, "DEPRECATED", "Wird auf Hybrid umgestellt"),
}

def is_enabled(feature: str) -> bool:
    """Prüft ob Feature aktiviert ist."""
    return FEATURE_FLAGS.get(feature, (False,))[0]

def get_status(feature: str) -> str:
    """Gibt Status des Features zurück."""
    return FEATURE_FLAGS.get(feature, (None, "UNKNOWN"))[1]
```

### 4. Laufzeit-Routing

```python
# services/classifier.py

from config.feature_flags import is_enabled

class ClassificationRouter:
    """Routet zu aktiver oder experimenteller Implementierung."""

    def __init__(self):
        if is_enabled("USE_GLINER_CLASSIFICATION"):
            from experimental.gliner_classifier import GLiNERClassifier
            self._impl = GLiNERClassifier()
            self._version = "v2-experimental"
        else:
            from deprecated.ollama_classifier import OllamaClassifier
            self._impl = OllamaClassifier()
            self._version = "v1-deprecated"

    def classify(self, text: str) -> dict:
        result = self._impl.classify(text)
        result["_classifier_version"] = self._version
        return result
```

---

## Migrations-Workflow

### Schritt 1: Neue Implementierung als EXPERIMENTAL

```yaml
# ADR-010 Status-Übergang
status_history:
  - date: 2025-12-28
    status: PROPOSED
    reason: "KI-Analyse identifiziert Performance-Problem"

  - date: 2025-12-29  # Nach Implementierung
    status: EXPERIMENTAL
    reason: "GLiNER-Klassifikation implementiert, A/B-Test gestartet"
```

### Schritt 2: A/B-Test durchführen

```bash
# Feature Flag temporär aktivieren
export FEATURE_USE_GLINER_CLASSIFICATION=true

# Test laufen lassen
python -m pytest tests/ab_test_classification.py -v

# Metriken sammeln
python scripts/compare_ab.py --test ABT-R02
```

### Schritt 3: Entscheidung dokumentieren

```yaml
# In ADR-010
entscheidung:
  status: BLUE  # Kandidat gewinnt
  datum: 2025-01-05
  begruendung: "GLiNER 20x schneller bei 5% weniger Genauigkeit"
  migration_deadline: 2025-02-01
```

### Schritt 4: Status-Übergang

```python
# Alte Implementierung markieren
FEATURE_FLAGS["USE_OLLAMA_CLASSIFICATION"] = (False, "DEPRECATED", "...")
FEATURE_FLAGS["USE_GLINER_CLASSIFICATION"] = (True, "ACTIVE", "...")
```

### Schritt 5: Cleanup nach Deadline

```bash
# Nach Migration-Deadline
rm -rf scripts/deprecated/ollama_classifier.py
# ADR-010 Status auf "Superseded by ADR-XXX" setzen
```

---

## Konfliktvermeidung

### Regel 1: Nie zwei ACTIVE für dieselbe Funktion

```
❌ FALSCH:
   scripts/smart_ingest.py     (ACTIVE, Ollama)
   scripts/smart_ingest_v2.py  (ACTIVE, GLiNER)

✅ RICHTIG:
   scripts/smart_ingest.py     (DEPRECATED, Ollama)
   scripts/smart_ingest_v2.py  (ACTIVE, GLiNER)
```

### Regel 2: Feature Flag als Single Source of Truth

```python
# IMMER über Feature Flag entscheiden, nie direkt importieren
from services.classifier import ClassificationRouter  # ✅
from scripts.smart_ingest import classify             # ❌
```

### Regel 3: Ergebnis-Tagging für Nachvollziehbarkeit

```python
# Jedes Ergebnis muss die Version dokumentieren
result = {
    "category": "Finanzen",
    "confidence": 0.85,
    "_processed_by": "gliner_classifier_v2",  # Welche Impl?
    "_feature_flags": {"USE_GLINER": True},   # Welche Flags?
    "_timestamp": "2025-12-28T14:30:00Z"
}
```

---

## Verknüpfte Dokumente

- ADR-Template: [TEMPLATE-ADR.md](TEMPLATES/TEMPLATE-ADR.md) (mit Status-Feldern)
- Komponenten-Status: [COMPONENT_STATUS.md](COMPONENT_STATUS.md)
- Changelog: [CHANGELOG.md](../CHANGELOG.md)

---

*Erstellt: 2025-12-28*
*Basierend auf: Erfolgsalgorithmus (Rote/Blaue Knöpfe), Semantic Versioning, Feature Flag Patterns*
