# Vision: Neural Vault

> **Die unveränderliche "Verfassung" dieses Projekts.**

## 🎯 Das Eine Ziel

**Ein lokales, privates "Internes Google" für 10TB+ Lebensdaten.**

Das bedeutet:
1.  **Suche:** Jedes Dokument, Foto, Video, jede E-Mail ist in <3 Sekunden auffindbar.
2.  **Organisation:** Dateien klassifizieren sich selbst und landen im richtigen Ordner.
3.  **Privatsphäre:** Keine Cloud. Alle KI läuft lokal auf eigener Hardware.

---

## ✅ Kernprinzipien (Die "Gesetze")

1.  **Privacy First:** Kein Byte verlässt das lokale Netzwerk. Niemals.
2.  **Copy First, Delete Never:** Wir löschen keine Originale (außer exakte SHA-256 Duplikate).
3.  **Git is the Audit Trail:** Jede Konfigurationsänderung ist versioniert und nachvollziehbar.
4.  **AI Context is Mandatory:** Jeder Ordner bekommt eine `_context.md` Datei.

---

## 🚫 Non-Goals (Was wir NICHT machen)

Diese Liste ist genauso wichtig wie die Ziele. Sie schützt vor "Feature Creep".

| Non-Goal | Begründung |
| :--- | :--- |
| **Kein "Daily Briefing" in Phase 1** | Fokus auf *Retrieval* (Suche), nicht auf *Generierung* (TTS, Zusammenfassungen). Das ist Phase 2+. |
| **Keine Echtzeit-Suche (<100ms)** | Unser SLA ist "<3 Sekunden". Sub-100ms erfordert In-Memory-Indizes und mehr RAM. |
| **Keine Multi-User-Kollaboration** | Wir optimieren für *einen* Power-User. Familie bekommt Read-Only Zugang via Immich/Nextcloud. |
| **Kein Video-Transkodieren** | Wir *deduplizieren* Videos, aber wandeln sie nicht für Streaming um. Abspielen erfolgt extern (VLC, Plex). |
| **Kein automatisches Löschen von visuellen Duplikaten** | Visuelle Duplikate werden nur *getaggt*, nicht automatisch gelöscht. Menschliche Review erforderlich. |
| **Keine Cloud-Anbindung** | Kein Google Drive Sync, kein Dropbox, kein OneDrive. Lokal only. |

---

## 📏 Erfolgsmetriken (Wie wissen wir, dass es funktioniert?)

| Metrik | Zielwert | Test-Methode |
| :--- | :--- | :--- |
| **Suchzeit für Rechnungen/Belege** | < 60 Sekunden | Automatisierte `pytest` Szenarien (siehe `tests/`). |
| **Indexierungs-Geschwindigkeit** | 1M Files in < 2 Minuten | Benchmark mit `scandir_rs`. |
| **Deduplizierungs-Rate (Exakt)** | 100% erkannt | SHA-256 Hash-Match gegen Testdaten. |

---

## 🗓️ Phasen-Fokus

| Phase | Fokus | Status |
| :--- | :--- | :--- |
| **Phase 1** | **Suche & Indexierung.** Legacy-Daten (F:) durchsuchbar machen. | 🟡 In Planung |
| **Phase 2** | **Smart Ingestion.** Neue Dateien klassifizieren sich automatisch. | ⚪ Nicht begonnen |
| **Phase 3** | **Generative Features.** Daily Briefings, Chat-Interface. | ⚪ Nicht begonnen |

---

*Dieses Dokument wird nur geändert, wenn sich die fundamentale Richtung des Projekts ändert.*
*Letzte Änderung: 2025-12-26*
