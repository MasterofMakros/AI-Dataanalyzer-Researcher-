# ADR-009: Shadow Ledger Event-Tracking vs. Periodischer Scan

## Status
**Proposed** - A/B-Test erforderlich (ABT-R01)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Content-addressed storage statt Path-Tracking"
- **Gemini 3 Pro:** "Wartungs-Hölle - wenn du manuell verschiebst, ist die DB out of sync"

---

## Kontext und Problemstellung

Das Shadow Ledger (`data/shadow_ledger.db`) trackt aktuell jeden Datei-Move als Event:
- `original_path` → `current_path`
- Jede Verschiebung wird protokolliert

**Problem:** Wenn Dateien außerhalb des Systems verschoben werden (Windows Explorer, anderes Tool), ist die Datenbank "out of sync".

**Kritikalität:** RED BUTTON - Potenzielle Dateninkonsistenz

---

## Entscheidungstreiber (Decision Drivers)

* **Robustheit:** System muss mit manuellen Dateioperationen umgehen können
* **Performance:** Scan darf nicht zu lange dauern
* **Genauigkeit:** SHA-256 als primärer Identifier ist zuverlässiger als Pfad

---

## Betrachtete Optionen

1. **Option A (Baseline):** Event-basiertes Tracking (aktuell)
2. **Option B (Kandidat):** Periodischer Filesystem-Scan
3. **Option C:** Hybrid (Events + periodische Verifizierung)

---

## A/B-Test Spezifikation

### Test-ID: ABT-R01

```yaml
hypothese:
  these: "Periodischer Scan ist robuster als Event-Tracking"
  null_hypothese: "Event-Tracking ist ausreichend zuverlässig"

baseline:
  implementierung: "shadow_ledger.py mit Event-Tracking"
  metriken:
    - name: "sync_accuracy"
      beschreibung: "Übereinstimmung DB vs. Filesystem"
      messmethode: "Vergleich current_path mit tatsächlichem Pfad"
      aktueller_wert: "UNBEKANNT - zu messen"
    - name: "update_latency"
      beschreibung: "Zeit bis Änderung in DB"
      aktueller_wert: "< 100ms (Event-basiert)"

kandidat:
  implementierung: "Periodischer Scan alle 15 Minuten"
  erwartete_verbesserung:
    - "sync_accuracy: 100% (da aktueller Stand gescannt)"
    - "Toleranz für manuelle Operationen"

testbedingungen:
  szenario_1: "1000 Dateien normal über smart_ingest.py verarbeiten"
  szenario_2: "100 Dateien manuell im Explorer verschieben"
  szenario_3: "50 Dateien extern umbenennen"
  dauer: "24 Stunden"
  messung_nach: "Jede Stunde sync_accuracy prüfen"

erfolgskriterien:
  primaer: "sync_accuracy Kandidat > 95% nach manuellen Operationen"
  sekundaer: "Scan-Dauer < 5 Minuten für 100k Dateien"

testscript: |
  # tests/ab_test_shadow_ledger.py

  import sqlite3
  from pathlib import Path

  def measure_sync_accuracy(db_path: str, root_path: str) -> float:
      """Misst Übereinstimmung zwischen DB und Filesystem."""
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      cursor.execute("SELECT sha256, current_path FROM files")

      total = 0
      synced = 0

      for sha256, db_path in cursor.fetchall():
          total += 1
          if Path(db_path).exists():
              synced += 1

      conn.close()
      return synced / total if total > 0 else 0.0
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf beiden KI-Analysen: **Option B (Periodischer Scan)** ist wahrscheinlich robuster.

### Begründung (vorläufig)
- Gemini identifiziert Event-Tracking als "Wartungs-Hölle"
- Claude empfiehlt Content-addressed storage (SHA-256 als Key)
- Periodischer Scan garantiert Konsistenz mit Filesystem

---

## Konsequenzen

### Wenn Option B gewinnt (Periodischer Scan)
**Positiv:**
- 100% Sync-Garantie nach jedem Scan
- Toleranz für externe Dateioperationen
- Einfacherer Code (kein Event-Handling)

**Negativ:**
- Höhere CPU-Last während Scan
- Verzögerung bis Änderung erkannt (max 15 Min)

### Wenn Option A gewinnt (Event-Tracking)
**Positiv:**
- Sofortige Updates
- Geringere CPU-Last

**Negativ:**
- Manuelle Operationen verursachen Inkonsistenz
- Komplexere Fehlerbehandlung nötig

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision ([product/vision.md](../product/vision.md))? | [x] Ja - Robustheit ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Scan-Intervall dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Aktueller Code: `scripts/shadow_ledger.py`
- Erfolgsalgorithmus: [ARCHITECTURE_EVOLUTION.md](../ARCHITECTURE_EVOLUTION.md)
