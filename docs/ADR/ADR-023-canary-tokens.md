# ADR-023: Security - Standard vs. Canary Tokens (Honeypots)

## Status
**Proposed** - A/B-Test erforderlich (ABT-N04)

## Datum
2025-12-28

## Entscheider
- Product Owner (basierend auf KI-Analyse)

## Quellen
- **Claude Opus 4.5:** "Security-Feature wenn System geteilt wird"
- **Gemini 3 Pro:** "Deception - Geheimdienste gehen davon aus, dass der Feind schon drin ist"

---

## Kontext und Problemstellung

Aktueller Zustand:
- Keine Intrusion Detection
- Keine "Honeypots" für unbefugten Zugriff
- System geht von "sicherem Perimeter" aus

**Gemini-Insight (Geheimdienst-Architektur):**
> "Zwischen deinen echten Dateien liegen falsche Dokumente (Honeypots).
> Sobald jemand 'passwords.xlsx' öffnet, wird ein stiller Alarm ausgelöst."

**Kritikalität:** NEW FEATURE - Sicherheit für geteiltes System

---

## Entscheidungstreiber (Decision Drivers)

* **Früherkennung:** Unbefugter Zugriff soll erkannt werden
* **Deception:** Angreifer soll getäuscht werden
* **Minimal Overhead:** Kein Performance-Impact auf normale Nutzung

---

## Betrachtete Optionen

1. **Option A (Baseline):** Keine Honeypots
2. **Option B (Kandidat):** Canary Tokens (Dateien + URLs)
3. **Option C:** Full Deception Network (komplex)

---

## Was sind Canary Tokens?

```
NORMALE DATEI                    CANARY TOKEN
┌─────────────┐                  ┌─────────────┐
│ Rechnung.pdf│                  │passwords.xlsx│
│             │                  │ (fake)       │
│ Echte Daten │                  │ Fake Daten   │
│             │                  │ + Trigger    │
└─────────────┘                  └──────┬──────┘
                                        │
                                        ▼ Bei Zugriff
                                 ┌─────────────┐
                                 │   ALARM!    │
                                 │ - E-Mail    │
                                 │ - Log       │
                                 │ - IP-Track  │
                                 └─────────────┘
```

---

## A/B-Test Spezifikation

### Test-ID: ABT-N04

```yaml
hypothese:
  these: "Canary Tokens erkennen unbefugte Zugriffe ohne Performance-Overhead"
  null_hypothese: "Kein Sicherheitsgewinn durch Honeypots"

baseline:
  implementierung: "Keine Honeypots"
  metriken:
    - name: "detection_rate"
      beschreibung: "Erkannte unbefugte Zugriffe"
      aktueller_wert: "0% (keine Detection)"
    - name: "false_positive_rate"
      beschreibung: "Fehlalarme"
      aktueller_wert: "N/A"
    - name: "performance_overhead"
      beschreibung: "Zusätzliche Latenz"
      aktueller_wert: "0ms"

kandidat:
  implementierung: |
    import os
    import hashlib
    import smtplib
    from datetime import datetime
    from pathlib import Path
    import sqlite3

    class CanarySystem:
        """Canary Token System für Neural Vault."""

        def __init__(self, db_path: str = "F:/conductor/data/canary.db"):
            self.db_path = db_path
            self._init_db()
            self.canaries = self._load_canaries()

        def _init_db(self):
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS canaries (
                    id TEXT PRIMARY KEY,
                    file_path TEXT,
                    file_hash TEXT,
                    created_at TEXT,
                    triggered_at TEXT,
                    trigger_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canary_id TEXT,
                    triggered_at TEXT,
                    source_ip TEXT,
                    user_agent TEXT,
                    details TEXT
                )
            """)
            conn.commit()
            conn.close()

        def create_canary(self, file_path: str, content: bytes) -> str:
            """Erstellt eine Canary-Datei."""
            canary_id = hashlib.sha256(file_path.encode()).hexdigest()[:16]

            # Datei erstellen
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)

            # In DB registrieren
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO canaries VALUES (?, ?, ?, ?, NULL, 0)",
                (canary_id, file_path, hashlib.sha256(content).hexdigest(),
                 datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

            return canary_id

        def check_and_trigger(self, file_path: str, context: dict = None) -> bool:
            """Prüft ob Datei ein Canary ist und triggert Alarm."""
            for canary_id, canary_path in self.canaries.items():
                if file_path == canary_path:
                    self._trigger_alert(canary_id, context)
                    return True
            return False

        def _trigger_alert(self, canary_id: str, context: dict):
            """Löst Alarm aus."""
            # 1. In DB loggen
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO triggers (canary_id, triggered_at, source_ip, details) VALUES (?, ?, ?, ?)",
                (canary_id, datetime.now().isoformat(),
                 context.get("ip", "unknown"),
                 str(context))
            )
            conn.execute(
                "UPDATE canaries SET triggered_at = ?, trigger_count = trigger_count + 1 WHERE id = ?",
                (datetime.now().isoformat(), canary_id)
            )
            conn.commit()
            conn.close()

            # 2. Alert senden (optional)
            self._send_alert(canary_id, context)

        def _send_alert(self, canary_id: str, context: dict):
            """Sendet Alert (E-Mail, Telegram, etc.)."""
            print(f"🚨 CANARY TRIGGERED: {canary_id}")
            print(f"   Context: {context}")
            # TODO: E-Mail, Telegram, etc.
  erwartete_verbesserung:
    - "detection_rate: 100% bei Canary-Zugriff"
    - "false_positive_rate: 0% (nur bei echtem Zugriff)"
    - "performance_overhead: < 1ms (Hash-Lookup)"

testbedingungen:
  setup:
    - "5 Canary-Dateien in verschiedenen Ordnern platzieren"
    - "Namen: passwords.xlsx, geheim.docx, backup_keys.txt, etc."
  test_szenarien:
    - "Normaler User greift auf echte Dateien zu → Kein Alarm"
    - "Simulierter Angreifer öffnet Canary → Alarm"
    - "Backup-Tool liest Canary → Alarm (True Positive, aber erwartbar)"

erfolgskriterien:
  primaer: "Alle Canary-Zugriffe werden erkannt"
  sekundaer: "Keine False Positives bei normaler Nutzung"
  tertiaer: "Latenz < 5ms für Canary-Check"
```

---

## Empfohlene Canary-Dateien

| Dateiname | Ordner | Beschreibung |
|-----------|--------|--------------|
| `passwords.xlsx` | `_Archiv/` | Fake Passwort-Liste |
| `Kontoauszug_GEHEIM.pdf` | `Finanzen/` | Fake Bankauszug |
| `backup_keys.txt` | `Technologie/` | Fake Backup-Keys |
| `Vertrag_ENTWURF.docx` | `Arbeit/` | Fake Vertrag |
| `.ssh_backup/` | `_System/` | Fake SSH-Keys Ordner |

---

## Entscheidung

**PENDING** - Test muss durchgeführt werden

### Vorläufige Empfehlung
Basierend auf Gemini-Analyse: **Option B (Canary Tokens)**

### Begründung (vorläufig)
- Gemini: "Geheimdienste gehen davon aus, dass der Feind schon drin ist"
- Minimaler Overhead bei maximaler Detection
- Sinnvoll wenn System später geteilt wird

---

## Konsequenzen

### Wenn Option B gewinnt (Canary Tokens)
**Positiv:**
- Früherkennung von Eindringlingen
- Psychologische Abschreckung
- Audit-Trail für unbefugte Zugriffe

**Negativ:**
- Zusätzliche Wartung (Canaries aktuell halten)
- Potenzielle False Positives bei Backup-Tools
- Komplexität im System

### Wenn Option A bleibt (Keine Honeypots)
**Positiv:**
- Einfacher
- Keine False Positives

**Negativ:**
- Keine Intrusion Detection
- Keine Früherkennung

---

## Priorität

**NIEDRIG** - Erst relevant wenn:
- System über Netzwerk erreichbar ist
- Mehrere Benutzer Zugriff haben
- Remote-Zugriff (Nextcloud, VPN) aktiviert ist

Für reines Homelab-System ohne externe Zugriffe: Nicht notwendig.

---

## Compliance-Check (PO-Absegnung)

| Frage | Antwort |
| :--- | :--- |
| Passt zur Vision (VISION.md)? | [x] Ja - "Privacy-First" impliziert Sicherheit |
| Verstößt gegen Non-Goals? | [ ] Nein |
| Erfordert Runbook-Update? | [x] Ja - Canary-Wartung dokumentieren |

**PO-Signatur:** _________________ Datum: _________

---

## Verknüpfte Dokumente

- A/B Framework: [AB_TEST_FRAMEWORK.md](../AB_TEST_FRAMEWORK.md)
- Erfolgsalgorithmus: [ARCHITECTURE_EVOLUTION.md](../ARCHITECTURE_EVOLUTION.md)
- Geheimdienst-Architektur: Gemini 3 Pro Analyse
