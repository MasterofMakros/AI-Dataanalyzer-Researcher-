# Anti-Roadmap: Was Neural Vault NIEMALS tun wird

> **Zweck:** Explizite Definition von fundamentalen Constraints.
> Diese Liste dokumentiert Entscheidungen, die NIEMALS geändert werden dürfen.
> Inspiriert vom "Erfolgsalgorithmus" – Rote Knöpfe, die wir nie wieder anfassen.

*Stand: 2025-12-28*

---

## 🚫 Absolute Verbote (Zero Tolerance)

### 1. Datenverlust verursachen
```
❌ NIEMALS Originaldateien automatisch löschen
❌ NIEMALS Dateien ohne Backup überschreiben
❌ NIEMALS "Cleanup"-Skripte ohne Dry-Run ausführen
```

**Begründung:** Daten sind unwiederbringlich. Lieber 10 Duplikate als 1 verlorene Datei.

**Stattdessen:**
- Duplikate in `_Quarantine/_duplicates/` verschieben (nicht löschen)
- Immer `--dry-run` als Default für destruktive Operationen
- Shadow Ledger behält alle Metadaten (auch für gelöschte Dateien)

---

### 2. Cloud-APIs für Inhalte nutzen
```
❌ NIEMALS OpenAI/Anthropic/Google APIs für private Dokumente
❌ NIEMALS Dateien zu externen OCR-Diensten hochladen
❌ NIEMALS Vektoren in Cloud-Datenbanken speichern
```

**Begründung:** Privacy First ist das Kernversprechen. Einmal in der Cloud = für immer kompromittiert.

**Stattdessen:**
- Lokale LLMs (Ollama)
- Lokale OCR (Tesseract, Docling, Surya)
- Lokale Vector-DB (Qdrant, LanceDB)

---

### 3. Originale in der Passive Zone verändern
```
❌ NIEMALS Dateien in F:/* (außerhalb _Inbox) umbenennen
❌ NIEMALS Dateien in F:/* verschieben
❌ NIEMALS Metadaten in Originaldateien schreiben (EXIF, PDF-Tags)
```

**Begründung:** Bestehende Ordnerstrukturen sind gewachsen und haben Bedeutung.
Das System beobachtet nur, es greift nicht ein ("ReadOnly-Beobachter").

**Stattdessen:**
- Metadaten im Shadow Ledger speichern
- Virtuelle Ansichten über die Datenbank
- Nur `_Inbox` ist "Active Zone"

---

### 4. Vendor Lock-in akzeptieren
```
❌ NIEMALS proprietäre Formate für Metadaten (z.B. .mdb, .accdb)
❌ NIEMALS Abhängigkeit von einem einzigen Tool/Service
❌ NIEMALS Daten in nicht-exportierbaren Formaten speichern
```

**Begründung:** Das System muss in 10 Jahren noch funktionieren, auch wenn Qdrant nicht mehr existiert.

**Stattdessen:**
- SQLite für Shadow Ledger (universell lesbar)
- JSON für Export (menschenlesbar)
- Markdown für Dokumentation
- Standard-APIs (REST, nicht proprietär)

---

### 5. Stille Fehler akzeptieren
```
❌ NIEMALS Exceptions schlucken ohne Logging
❌ NIEMALS fehlgeschlagene Operationen als Erfolg melden
❌ NIEMALS "funktioniert bei mir" als Test akzeptieren
```

**Begründung:** Stille Fehler führen zu Datenverlust, der erst Monate später auffällt.

**Stattdessen:**
- Jeder Fehler wird geloggt (`logs/`)
- Quarantäne bei Unsicherheit
- Telegram-Benachrichtigung bei kritischen Fehlern

---

## ⚠️ Architektur-Constraints

### 6. Keine monolithischen Skripte
```
❌ NIEMALS >500 Zeilen in einer Datei ohne klare Trennung
❌ NIEMALS Geschäftslogik und I/O vermischen
❌ NIEMALS hartcodierte Pfade (immer config.paths)
```

**Begründung:** Monolithen sind nicht testbar und nicht wartbar.

---

### 7. Keine ungetesteten Produktiv-Deployments
```
❌ NIEMALS neue Features ohne Spike/PoC direkt in Produktion
❌ NIEMALS "funktioniert schon" als Argument
❌ NIEMALS 2 Wochen an etwas bauen ohne frühen Test
```

**Begründung:** Der Erfolgsalgorithmus sagt: Antippen, nicht Durchdrücken.

**Stattdessen:**
- Feature Flags für neue Features
- Max. 2 Tage für Spike
- ADR vor großen Änderungen

---

### 8. Keine Abhängigkeit von Internet-Verfügbarkeit
```
❌ NIEMALS Features, die ohne Internet nicht funktionieren
❌ NIEMALS externe APIs im kritischen Pfad
```

**Begründung:** Das System muss offline funktionieren (Stromausfall, Netzwerkprobleme).

**Stattdessen:**
- Alle KI-Modelle lokal
- Externe Dienste (Telegram) nur für Notifications, nicht für Kernfunktion

---

## 📋 Checkliste für neue Features

Vor jedem neuen Feature diese Fragen stellen:

| Frage | Erwartete Antwort |
|:---|:---|
| Kann es Daten löschen/beschädigen? | Nein |
| Sendet es Daten an externe Server? | Nein |
| Ändert es Dateien in der Passive Zone? | Nein |
| Funktioniert es offline? | Ja |
| Ist es ohne Vendor-Lock-in? | Ja |
| Wurde es mit Spike getestet? | Ja |
| Gibt es einen Rollback-Plan? | Ja |

**Wenn eine Antwort "Ja" bei den ersten 3 oder "Nein" bei den letzten 4 ist → STOPP!**

---

## 🔴 Bereits identifizierte "Rote Knöpfe" (aus ADRs)

Diese wurden getestet und verworfen – nie wieder anfassen:

| Feature | ADR | Grund für Ablehnung |
|:---|:---|:---|
| Cross-Encoder Reranking | ADR-015 | Zu langsam, kein Nutzen |
| Ollama für Klassifikation | ADR-010 | GLiNER ist schneller |
| Auto-Rename in Passive Zone | ADR-011 | User-Verwirrung |
| Event-basiertes Ledger | ADR-009 | Zu fragil |
| Knowledge Graph UI | ADR-013 | Zu komplex, niemand nutzt es |
| Separate Docker für ffmpeg | ADR-014 | Overhead |

---

## 📜 Änderungsprotokoll

| Datum | Änderung | Begründung |
|:---|:---|:---|
| 2025-12-28 | Dokument erstellt | Übernahme aus Gemini-Analyse |

---

*Dieses Dokument ist unveränderlich. Neue Einträge können hinzugefügt, aber bestehende NIEMALS entfernt werden.*

### ⚠️ Cross-Encoder Reranking (ADR-015) - AMENDED 2026-01-06
**Status:** Conditionally Allowed (<100ms)

- ✅ TinyBERT-L-6 (~50ms)
- ❌ bert-base (>500ms)
