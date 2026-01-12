# A/B Test Framework: Neural Vault
## Basierend auf Alex Fischers Erfolgsalgorithmus

> **Kernprinzip:** "Erfolg ist das Weglassen von Misserfolg"
>
> *Jede Architekturentscheidung wird durch systematisches Testen validiert.*
> *Rote Knöpfe (Misserfolge) werden markiert und nie wieder berührt.*
> *Blaue Knöpfe (Erfolge) werden verstärkt und ausgebaut.*

---

## Quellenangabe

Dieses Framework basiert auf zwei unabhängigen KI-Analysen des Conductor-Projekts:

| Quelle | Modell | Datum | Fokus |
|--------|--------|-------|-------|
| **Analyse A** | Claude Opus 4.5 | 2025-12-28 | Architektur, 2025-Tools, Format-Handling |
| **Analyse B** | Gemini 3 Pro | 2025-12-28 | Entity Resolution, Circuit Breaker, Kritik |

Die Konsolidierung beider Analysen ermöglicht eine objektivere Bewertung.

---

## Der Erfolgsalgorithmus in Software

### Die 1000-Knöpfe-Metapher (übersetzt)

```
ARCHITEKTUR-ENTSCHEIDUNGEN = 1000 Knöpfe

┌─────────────────────────────────────────────────────────────┐
│  995 ROTE KNÖPFE (Misserfolg)     │  5 BLAUE KNÖPFE (Erfolg) │
│  - Werfen dich 1 Meter zurück     │  - Katapultieren 10m vor │
│  - MÜSSEN identifiziert werden    │  - MÜSSEN verstärkt werden│
└─────────────────────────────────────────────────────────────┘

STRATEGIE:
1. Nicht "All-in" gehen (kein Monolith)
2. Einzelne Knöpfe vorsichtig antippen (PoC/Pilot)
3. Rote Knöpfe sofort markieren (ADR mit Status "Deprecated")
4. Von anderen lernen (Gemini + Claude Analysen)
5. Blaue Bereiche identifizieren (Was funktioniert?)
```

### Hegels Dialektik als Feedback-Loop

```
IST-STAND → THESE → TEST → OUTCOME → NEUER IST-STAND
     ↑                                        ↓
     ←────────── AUTOMATISIERTER LOOP ←───────
```

**Anwendung auf A/B-Tests:**
1. IST-STAND: Aktuelle Implementierung messen (Baseline)
2. THESE: "Feature X ist besser als Feature Y"
3. TEST: Beide parallel mit identischen Daten testen
4. OUTCOME: Metriken vergleichen
5. NEUER IST-STAND: Gewinner wird Standard

---

## A/B-Test Struktur (MADR-kompatibel)

Jeder Test folgt diesem Schema:

```yaml
test_id: "ABT-XXX"
titel: "Feature A vs Feature B"
kategorie: "RED|BLUE|NEW"

hypothese:
  these: "Feature A ist besser weil..."
  null_hypothese: "Kein signifikanter Unterschied"

baseline:
  implementierung: "Aktuelle Version"
  metriken:
    - name: "Latenz"
      wert: "X ms"
    - name: "Genauigkeit"
      wert: "X %"

kandidat:
  implementierung: "Neue Version"
  erwartete_verbesserung: "X %"

testbedingungen:
  daten: "N Dateien aus F:/"
  dauer: "X Stunden/Tage"
  hardware: "Ryzen 5700X, 32GB RAM, RTX 3060"

erfolgskriterien:
  primaer: "Metrik X > Baseline um Y%"
  sekundaer: "Keine Regression in Metrik Z"

entscheidung:
  status: "PENDING|BLUE|RED"
  datum: "YYYY-MM-DD"
  begruendung: "..."
```

---

## Übersicht aller A/B-Tests

### RED Button Tests (Eliminieren/Ersetzen)

| ID | Test | Baseline (A) | Kandidat (B) | Status | ADR |
|----|------|--------------|--------------|--------|-----|
| ABT-R01 | Shadow Ledger Tracking | Event-basiert | Periodischer Scan | PENDING | [ADR-009](ADR/ADR-009-shadow-ledger-tracking.md) |
| ABT-R02 | Klassifikation | Ollama LLM | GLiNER NER | ACCEPTED | [ADR-010](ADR/ADR-010-classification-method.md) |
| ABT-R03 | Dateinamen | Auto-Rename | Metadata-Layer | PENDING | [ADR-011](ADR/ADR-011-filename-strategy.md) |
| ABT-R04 | Quarantäne-Rate | 50% Threshold | 10% Threshold | PENDING | [ADR-012](ADR/ADR-012-quarantine-threshold.md) |
| ABT-R05 | Knowledge Graph | Visualisierung | Related Docs | PENDING | [ADR-013](ADR/ADR-013-knowledge-graph-usage.md) |
| ABT-R06 | Docker Stack | 17 Container | 8 Core Container | PENDING | [ADR-014](ADR/ADR-014-docker-stack-size.md) |

### BLUE Button Tests (Verstärken)

| ID | Test | Baseline (A) | Kandidat (B) | Status | ADR |
|----|------|--------------|--------------|--------|-----|
| ABT-B01 | Search Ranking | BM25 only | BM25 + Reranker | REJECTED | [ADR-015](ADR/ADR-015-search-reranking.md) |
| ABT-B02 | Inbox Processing | Sync | Async + Circuit Breaker | PENDING | [ADR-016](ADR/ADR-016-inbox-processing.md) |
| ABT-B03 | LLM Backend | Cloud API | Local Ollama | ACCEPTED | [ADR-017](ADR/ADR-017-llm-backend.md) |
| ABT-B04 | Deep Structure | Tika | Docling | ACCEPTED | [ADR-018](ADR/ADR-018-pdf-parsing.md) |
| ABT-B05 | Vector DB Scale | Qdrant | LanceDB | PENDING | [ADR-019](ADR/ADR-019-vector-database.md) |
| ABT-B06 | Error Handling | Log only | Circuit Breaker | PENDING | [ADR-016](ADR/ADR-016-inbox-processing.md) |

### NEW Feature Tests (Evaluieren)

| ID | Test | Baseline (A) | Kandidat (B) | Status | ADR |
|----|------|--------------|--------------|--------|-----|
| ABT-N01 | Entity Matching | Exact Match | Fuzzy Resolution | PENDING | [ADR-020](ADR/ADR-020-entity-resolution.md) |
| ABT-N02 | Tabellen-Suche | Raw Text | Data Narrator | ACCEPTED | [ADR-021](ADR/ADR-021-data-narrator.md) |
| ABT-N03 | Search UI | Liste | Evidence Board | PENDING | [ADR-022](ADR/ADR-022-evidence-board-ui.md) |
| ABT-N04 | Security | Standard | PII Masking (Zero-Trust) | ACCEPTED | [ADR-023](ADR/ADR-023-canary-tokens.md) |

---

## Metriken-Katalog

### Performance-Metriken

| Metrik | Beschreibung | Messmethode | Zielwert |
|--------|--------------|-------------|----------|
| `latency_p50` | Median-Antwortzeit | Timer in Code | < 500ms |
| `latency_p99` | 99. Perzentil | Timer in Code | < 2000ms |
| `throughput` | Dateien/Minute | Counter | > 10/min |
| `memory_peak` | Max RAM-Nutzung | Docker stats | < 8GB |

### Qualitäts-Metriken

| Metrik | Beschreibung | Messmethode | Zielwert |
|--------|--------------|-------------|----------|
| `precision` | Relevante Treffer / Alle Treffer | Manuelles Review | > 80% |
| `recall` | Gefundene Relevante / Alle Relevante | Ground Truth Set | > 70% |
| `f1_score` | Harmonisches Mittel | Berechnet | > 0.75 |
| `confidence_avg` | Durchschnittliche KI-Konfidenz | Aus Logs | > 0.7 |

### Robustheit-Metriken

| Metrik | Beschreibung | Messmethode | Zielwert |
|--------|--------------|-------------|----------|
| `error_rate` | Fehler / Gesamt | Exception Counter | < 1% |
| `recovery_time` | Zeit bis Wiederherstellung | Timer | < 30s |
| `quarantine_rate` | Quarantäne / Gesamt | Counter | < 10% |

---

## Test-Durchführung

### Voraussetzungen

```bash
# Test-Datenset vorbereiten
python scripts/prepare_test_data.py --size 1000 --source F:/_TestPool

# Baseline messen
python scripts/benchmark.py --mode baseline --output data/baseline_metrics.json

# Kandidat messen
python scripts/benchmark.py --mode candidate --output data/candidate_metrics.json

# Vergleich
python scripts/compare_ab.py --a data/baseline_metrics.json --b data/candidate_metrics.json
```

### Entscheidungsregeln

```python
def entscheide(baseline: Metrics, kandidat: Metrics) -> str:
    """
    Erfolgsalgorithmus: Systematische Entscheidung
    """
    # Primäres Kriterium
    if kandidat.primaer_metrik > baseline.primaer_metrik * 1.1:  # 10% besser
        # Sekundäres Kriterium (keine Regression)
        if kandidat.sekundaer_metrik >= baseline.sekundaer_metrik * 0.95:
            return "BLUE"  # Kandidat gewinnt

    if kandidat.primaer_metrik < baseline.primaer_metrik * 0.9:  # 10% schlechter
        return "RED"  # Kandidat ist roter Knopf

    return "INCONCLUSIVE"  # Mehr Daten nötig
```

---

## Verknüpfte Dokumente

- ADRs: `docs/ADR/ADR-009-*.md` bis `ADR-024-*.md`
- Erfolgsalgorithmus: `docs/ARCHITECTURE_EVOLUTION.md`
- Dokumentationsstandard: `docs/DOCUMENTATION_STANDARD.md`

---

*Erstellt: 2025-12-28*
*Quellen: Claude Opus 4.5 Analyse, Gemini 3 Pro Analyse, Alex Fischer Erfolgsalgorithmus*
