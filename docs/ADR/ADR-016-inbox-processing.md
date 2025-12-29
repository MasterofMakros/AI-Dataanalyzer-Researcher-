# ADR-016: Inbox Processing - Synchron vs. Async mit Circuit Breaker

## Status
**Proposed** - A/B-Test erforderlich (ABT-B02)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Retry-Queue statt sofortiger Quarantäne"
- **Gemini 3 Pro:** "Circuit Breakers - Fehler abfangen, nicht nur loggen"

---

## Kontext und Problemstellung

Aktuelle Implementierung in `smart_ingest.py`:
- Synchrone Verarbeitung: Datei → Tika → LLM → Move
- Bei Fehler: Sofort in Quarantäne
- Kein Retry-Mechanismus

**Problem:**
- Eine defekte Datei blockiert die Queue nicht, aber...
- Transiente Fehler (Tika-Timeout, LLM-Überlast) führen zu unnötiger Quarantäne
- Kein "Self-Healing"

**Kritikalität:** BLUE BUTTON - Robustheit des Kernfeatures verbessern

---

## Entscheidungstreiber (Decision Drivers)

* **Robustheit:** System muss sich von transienten Fehlern erholen
* **Durchsatz:** Fehler dürfen nicht andere Dateien blockieren
* **Transparenz:** Fehler müssen sichtbar und nachvollziehbar sein

---

## Betrachtete Optionen

1. **Option A (Baseline):** Synchrone Verarbeitung, sofortige Quarantäne
2. **Option B (Kandidat):** Async mit Circuit Breaker + Retry Queue
3. **Option C:** Komplett async mit Message Queue (Redis/RabbitMQ)

---

## Circuit Breaker Pattern

```
                    ┌──────────────┐
                    │   CLOSED     │ ← Normal operation
                    │ (All passes) │
                    └──────┬───────┘
                           │ Failure threshold exceeded
                           ▼
                    ┌──────────────┐
                    │    OPEN      │ ← Fail fast, no calls
                    │ (All fails)  │
                    └──────┬───────┘
                           │ Timeout expires
                           ▼
                    ┌──────────────┐
                    │  HALF-OPEN   │ ← Test if service recovered
                    │ (Test call)  │
                    └──────────────┘
```

---

## A/B-Test Spezifikation

### Test-ID: ABT-B02

```yaml
hypothese:
  these: "Circuit Breaker + Retry reduziert unnötige Quarantäne um 50%"
  null_hypothese: "Sofortige Quarantäne ist ausreichend robust"

baseline:
  implementierung: "smart_ingest.py synchron"
  metriken:
    - name: "quarantine_rate_transient"
      beschreibung: "Quarantäne durch transiente Fehler"
      messmethode: "Fehlertyp-Analyse in Logs"
      aktueller_wert: "UNBEKANNT"
    - name: "recovery_rate"
      beschreibung: "Dateien die nach Retry erfolgreich sind"
      aktueller_wert: "0% (kein Retry)"
    - name: "throughput_under_load"
      beschreibung: "Dateien/Minute bei hoher Last"
      aktueller_wert: "UNBEKANNT"

kandidat:
  implementierung: |
    from circuitbreaker import circuit

    class IngestPipeline:
        def __init__(self):
            self.retry_queue = []
            self.max_retries = 3

        @circuit(failure_threshold=5, recovery_timeout=60)
        def call_tika(self, file_path: str) -> str:
            """Mit Circuit Breaker geschützt."""
            response = requests.post(
                "http://tika:9998/tika",
                data=open(file_path, "rb"),
                timeout=30
            )
            return response.text

        async def process_with_retry(self, file_path: str):
            for attempt in range(self.max_retries):
                try:
                    text = self.call_tika(file_path)
                    return await self.classify_and_move(file_path, text)
                except CircuitBreakerError:
                    # Tika ist überlastet, später versuchen
                    self.retry_queue.append((file_path, attempt + 1))
                    return "DEFERRED"
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        return await self.quarantine(file_path, str(e))
  erwartete_verbesserung:
    - "quarantine_rate_transient: -50%"
    - "recovery_rate: > 30% der Retry-Fälle"
    - "throughput_under_load: +20%"

testbedingungen:
  szenario_1: "Normal: 500 Dateien, alle Services healthy"
  szenario_2: "Tika-Stress: 500 Dateien, Tika mit 50% Timeout-Rate"
  szenario_3: "LLM-Überlast: 500 Dateien, Ollama mit 30% Timeout"
  szenario_4: "Gemischt: Reale Fehlermuster"

erfolgskriterien:
  primaer: "quarantine_rate unter Stress < Baseline - 30%"
  sekundaer: "Keine Datenverluste (alle Dateien verarbeitet oder in Retry/Quarantäne)"
  tertiaer: "throughput normal >= Baseline"

testscript: |
  # tests/ab_test_circuit_breaker.py

  import asyncio
  from unittest.mock import patch
  import random

  def simulate_flaky_tika(failure_rate: float = 0.3):
      """Simuliert instabilen Tika-Service."""
      if random.random() < failure_rate:
          raise TimeoutError("Tika timeout")
      return "Extracted text..."

  async def test_resilience(pipeline, files: list, failure_rate: float) -> dict:
      results = {"success": 0, "retry": 0, "quarantine": 0}

      with patch.object(pipeline, 'call_tika', side_effect=simulate_flaky_tika):
          for file_path in files:
              result = await pipeline.process_with_retry(file_path)
              results[result] += 1

      # Nach Wartezeit: Retry-Queue verarbeiten
      await asyncio.sleep(70)  # Circuit Breaker Recovery
      for file_path, attempt in pipeline.retry_queue:
          result = await pipeline.process_with_retry(file_path)
          if result == "success":
              results["retry_success"] = results.get("retry_success", 0) + 1

      return results
```

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option B (Circuit Breaker)**

### Begründung (vorläufig)
- Gemini explizit: "Circuit Breakers einbauen"
- Erfolgsalgorithmus: "Fehler in Wissen verwandeln, nicht nur loggen"
- Robustheit ist für Produktivbetrieb essentiell

---

## Konsequenzen

### Wenn Option B gewinnt (Circuit Breaker)
**Positiv:**
- Selbstheilung bei transienten Fehlern
- Schutz vor Überlastung der Downstream-Services
- Weniger manuelle Quarantäne-Reviews

**Negativ:**
- Komplexerer Code
- Verzögerte Verarbeitung bei Retry
- Zusätzliche Abhängigkeit (circuitbreaker library)

### Wenn Option A bleibt (Synchron)
**Positiv:**
- Einfacher Code
- Deterministisches Verhalten

**Negativ:**
- Unnötige Quarantäne bei transienten Fehlern
- Keine Self-Healing-Fähigkeit

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - Robustheit ist Kernziel |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Circuit Breaker States dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Smart Ingest: `scripts/smart_ingest.py`
- Erfolgsalgorithmus: [ARCHITECTURE_EVOLUTION.md](../ARCHITECTURE_EVOLUTION.md)
