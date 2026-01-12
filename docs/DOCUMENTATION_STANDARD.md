# Documentation Standard: Neural Vault

> **Die verbindlichen Regeln für alle Projektdokumentation.**
> *Erstellt basierend auf MADR 4.0, Google SRE Runbook Best Practices, Diátaxis Framework (2025).*

---

## 📋 Die "Definition of Done" für Aufgaben

### ❌ Eine Aufgabe ist NICHT abgeschlossen, wenn:
- Nur der Code committed wurde.
- "Es funktioniert auf meinem Rechner."

### ✅ Eine Aufgabe ist ABGESCHLOSSEN, wenn alle Kriterien erfüllt sind:

| Kriterium | Beschreibung | Prüfung |
| :--- | :--- | :--- |
| **Code Committed** | Code ist in `main`/`develop` Branch gemerged. | Git Log prüfen |
| **ADR geschrieben** | Falls eine neue Technologie eingeführt wurde: ADR in `docs/ADR/` vorhanden. | Datei existiert |
| **Runbook aktualisiert** | Falls operationale Änderungen: Runbook in `docs/runbooks/` aktualisiert. | Changelog prüfen |
| **Tests vorhanden** | Automatisierte Tests für neue Funktionen. | `pytest` grün |
| **README aktuell** | Bei strukturellen Änderungen: README.md aktualisiert. | Manuelle Prüfung |

**Signatur des Product Owners:**
> *"Nur wenn Code committed UND relevante ADRs geschrieben UND Runbooks aktualisiert sind, gilt eine Aufgabe als abgeschlossen. Keine Ausnahmen."*

---

## 📁 Dokumentations-Struktur (Diátaxis-inspiriert)

```
docs/
├── ADR/                    # Architecture Decision Records (Warum?)
│   └── ADR-XXX-titel.md
├── runbooks/               # Operational Guides (Wie?)
│   └── RUNBOOK-XXX-titel.md
├── tutorials/              # Learning-Oriented (Einführungen)
│   └── getting-started.md
├── reference/              # Information-Oriented (Nachschlagen)
│   └── api-spec.md
├── data-assets/            # Data Asset Registrierung
│   └── ASSET-XXX-titel.md
├── GLOSSARY.md             # Begriffserklärungen
└── TEMPLATES/              # <- Die Templates (dieses Dokument)
    ├── TEMPLATE-ADR.md
    ├── TEMPLATE-RUNBOOK.md
    └── TEMPLATE-DATA-ASSET.md
```

---

## 🔗 Quellen

- **MADR 4.0.0:** [github.com/adr/madr](https://github.com/adr/madr)
- **Google SRE Runbooks:** [sre.google](https://sre.google)
- **Diátaxis Framework:** [diataxis.fr](https://diataxis.fr)
- **Arc42:** [arc42.org](https://arc42.org)

---

*Letzte Aktualisierung: 2025-12-26*
